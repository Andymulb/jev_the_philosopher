#!/usr/bin/env python3
"""Ask Jev every question in questions.json N times and summarise the answers.

Usage: python3 run_tests.py [--runs 10] [--only QA.1,Q2.3]
Writes results/<timestamp>/raw.jsonl, summary.json and summary.md.
"""
import argparse
import json
import statistics
import time
import urllib.error
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent
RETRY_STATUSES = {429, 500, 502, 503, 524, 529}


def load_env(path):
    env = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip()
    return env


def resolve_state(state, shared):
    return {k: shared[v[1:]] if isinstance(v, str) and v.startswith("@") else v for k, v in state.items()}


def build_questions(item):
    if item.get("kind") != "selection":
        return item["questions"]
    return {
        c["name"]: {"type": "noul", "instructions": item["instructions_template"].format(**c)}
        for c in item["candidates"]
    }


def build_state(item, shared):
    state = resolve_state(item["state"], shared)
    if item.get("kind") == "selection":
        state["people"] = [f'{c["name"]}: {c["card"]}' for c in item["candidates"]]
    return state


def call_jev(env, body, attempts=5):
    request = urllib.request.Request(
        env["JEV_DECISIONS_URL"],
        data=json.dumps(body).encode(),
        headers={"Authorization": f'Bearer {env["OPENROUTER_API_KEY"]}', "Content-Type": "application/json"},
        method="POST",
    )
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code not in RETRY_STATUSES or attempt == attempts - 1:
                raise RuntimeError(f"HTTP {error.code}: {error.read().decode()[:300]}") from None
        except (urllib.error.URLError, TimeoutError):
            if attempt == attempts - 1:
                raise
        time.sleep(2 ** attempt)


def label(item):
    return item["id"] + (f' ({item["variant"]})' if item.get("variant") else "")


def summarise_question(answers):
    kind = answers[0]["type"]
    if kind == "noul":
        values = [a["noul"] for a in answers]
        return {"type": "noul", "mean": statistics.mean(values), "min": min(values), "max": max(values),
                "stdev": statistics.pstdev(values), "yes_runs": sum(v > 0.5 for v in values), "values": values}
    if kind == "choice":
        options = answers[0]["probabilities"].keys()
        return {"type": "choice", "counts": dict(Counter(a["choice"] for a in answers)),
                "mode": Counter(a["choice"] for a in answers).most_common(1)[0][0],
                "mean_probabilities": {o: statistics.mean(a["probabilities"][o] for a in answers) for o in options},
                "mean_confidence": statistics.mean(a["confidence"] for a in answers)}
    levels = answers[0]["legend"]
    return {"type": "score", "mean": statistics.mean(a["score"] for a in answers),
            "stdev": statistics.pstdev([a["score"] for a in answers]), "legend": levels,
            "mean_probabilities": {k: statistics.mean(a["probabilities"][k] for a in answers) for k in levels},
            "mean_confidence": statistics.mean(a["confidence"] for a in answers)}


def film_agreement(item, questions):
    """Compare Jev's aggregate answers with what the film shows (or with a known reference)."""
    expected = item.get("film") or item.get("reference")
    if expected is None or item.get("kind") == "selection":
        return None
    result = {}
    for key, want in expected.items():
        q = questions[key]
        got = q["mean"] > 0.5 if q["type"] == "noul" else q["mode"]
        result[key] = {"film": want, "jev": got, "agrees": got == want}
    return result


def summarise_item(item, rows):
    runs = [r["response"] for r in rows]
    keys = runs[0]["answers"].keys()
    questions = {k: summarise_question([r["answers"][k] for r in runs]) for k in keys}
    summary = {"id": item["id"], "variant": item.get("variant"), "section": item["section"],
               "title": item["title"], "source": item.get("source", "film sources"),
               "state": item["state"], "runs": len(runs), "questions": questions,
               "film_note": item.get("film_note"), "reference": "reference" in item,
               "questions_per_request": len(keys),
               "latency_ms": timing_stats([r["latency_ms"] for r in rows if r.get("latency_ms") is not None]),
               "roundtrip_ms": timing_stats([r["roundtrip_ms"] for r in rows if r.get("roundtrip_ms") is not None])}
    if item.get("kind") == "selection":
        chosen_counts = Counter()
        for r in runs:
            ranked = sorted(r["answers"], key=lambda name: r["answers"][name]["noul"], reverse=True)
            chosen_counts.update(ranked[:10])
        by_mean = sorted(keys, key=lambda name: questions[name]["mean"], reverse=True)
        film = set(item["film"])
        summary["selection"] = {
            "ranking": [{"name": n, "mean": questions[n]["mean"], "top10_runs": chosen_counts[n],
                         "card": next(c["card"] for c in item["candidates"] if c["name"] == n),
                         "film_chose": n in film} for n in by_mean],
            "jev_top10": by_mean[:10], "film": item["film"],
            "overlap_with_film": len(film & set(by_mean[:10])),
        }
    else:
        summary["film"] = film_agreement(item, questions)
    return summary


def fmt_question(key, q):
    if q["type"] == "noul":
        spread = f' (range {q["min"]:.2f}–{q["max"]:.2f})' if q["max"] - q["min"] >= 0.01 else ""
        return f'`{key}` yes-probability **{q["mean"]:.2f}**{spread}, yes in {q["yes_runs"]}/{len(q["values"])} runs'
    if q["type"] == "choice":
        probs = ", ".join(f'{o} {p:.2f}' for o, p in sorted(q["mean_probabilities"].items(), key=lambda x: -x[1]))
        counts = ", ".join(f'{o} ×{n}' for o, n in q["counts"].items())
        return f'`{key}` chose **{q["mode"]}** ({counts}); mean probabilities {probs}; confidence {q["mean_confidence"]:.2f}'
    nearest = q["legend"][str(round(q["mean"]))]
    return f'`{key}` score **{q["mean"]:.2f}** ≈ "{nearest}"; confidence {q["mean_confidence"]:.2f}'


def write_markdown(path, summaries, meta):
    lines = [f'# Jev on The Philosophers: test run {meta["started"]}', "",
             f'Model `{meta["model"]}`, {meta["runs"]} runs per item, {meta["requests"]} requests, '
             f'{meta["input_tokens"]} input tokens, cost ${meta["cost"]:.5f}.', ""]
    if meta.get("latency_ms"):
        lat = meta["latency_ms"]
        lines += [f'Jev\'s answer time per request (measured by OpenRouter, excluding network): median **{lat["median"]} ms**, '
                  f'mean {lat["mean"]} ms, range {lat["min"]}–{lat["max"]} ms.', ""]
    agree = [v["agrees"] for s in summaries if s.get("film") for v in s["film"].values()]
    lines += [f'Agreement with the film / reference answers: **{sum(agree)}/{len(agree)}** questions.', ""]
    for s in summaries:
        name = s["id"] + (f' ({s["variant"]})' if s["variant"] else "")
        lines.append(f'## {name}: {s["title"]}')
        if s["source"] == "user recollection":
            lines.append("*(from user recollection)*")
        if s.get("latency_ms"):
            plural = "s" if s["questions_per_request"] > 1 else ""
            lines.append(f'*Jev\'s time: median {s["latency_ms"]["median"]} ms for {s["questions_per_request"]} question{plural} in one request*')
        if "selection" in s:
            sel = s["selection"]
            lines.append(f'Jev top 10: {", ".join(sel["jev_top10"])}')
            lines.append(f'Film: {", ".join(sel["film"])}')
            lines.append(f'Overlap: **{sel["overlap_with_film"]}/10**')
            lines += ["", "| # | Person | Card | Jev yes | In Jev top 10 (runs) | Film chose |", "|---|---|---|---|---|---|"]
            for i, r in enumerate(sel["ranking"], 1):
                lines.append(f'| {i} | {r["name"]} | {r["card"]} | {r["mean"]:.2f} | {r["top10_runs"]}/{s["runs"]} | {"✓" if r["film_chose"] else ""} |')
        else:
            for key, q in s["questions"].items():
                lines.append(f'- {fmt_question(key, q)}')
            for key, f in (s["film"] or {}).items():
                who = "Reference" if s["reference"] else "Film"
                lines.append(f'- {who} for `{key}`: {f["film"]} → Jev **{"agrees" if f["agrees"] else "disagrees"}**')
        if s["film_note"]:
            lines.append(f'- Note: {s["film_note"]}')
        lines.append("")
    path.write_text("\n".join(lines))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--only", help="comma-separated item ids")
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--add-timing", metavar="RESULTS_DIR",
                        help="add Jev's latency to an existing run (e.g. results/2026-09-19_08-49-45) instead of running")
    args = parser.parse_args()

    env = load_env(ROOT / ".env")
    data = json.loads((ROOT / "questions.json").read_text())
    items = data["items"]
    if args.only:
        wanted = set(args.only.split(","))
        items = [i for i in items if i["id"] in wanted]

    if args.add_timing:
        out_dir = ROOT / args.add_timing
        rows = [json.loads(line) for line in (out_dir / "raw.jsonl").read_text().splitlines()]
        present = {r["item"] for r in rows}
        finish(env, out_dir, [i for i in items if label(i) in present], rows)
        return

    started = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_dir = ROOT / "results" / started
    out_dir.mkdir(parents=True)

    jobs = [(item, run) for item in items for run in range(args.runs)]

    def execute(job):
        item, run = job
        body = {"model": env["JEV_MODEL"], "state": build_state(item, data["shared_states"]),
                "questions": build_questions(item)}
        start = time.perf_counter()
        response = call_jev(env, body)
        return {"item": label(item), "run": run, "request": body, "response": response,
                "roundtrip_ms": round((time.perf_counter() - start) * 1000)}

    print(f"{len(items)} items × {args.runs} runs = {len(jobs)} requests")
    rows = []
    with ThreadPoolExecutor(args.workers) as pool:
        for n, row in enumerate(pool.map(execute, jobs), 1):
            rows.append(row)
            if n % 25 == 0 or n == len(jobs):
                print(f"  {n}/{len(jobs)} done")
    finish(env, out_dir, items, rows)


def fetch_latency(env, generation_id, attempts=5):
    """Jev's own answer time in ms, as OpenRouter measured it (excludes our network)."""
    url = "https://openrouter.ai/api/v1/generation?id=" + generation_id
    request = urllib.request.Request(url, headers={"Authorization": f'Bearer {env["OPENROUTER_API_KEY"]}'})
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)["data"]["latency"]
        except (urllib.error.URLError, TimeoutError, KeyError):
            time.sleep(1 + attempt)  # stats can take a moment to appear after the request
    return None


def finish(env, out_dir, items, rows):
    """Add Jev's latency to every row, then write raw.jsonl, summary.json and summary.md."""
    missing = [r for r in rows if r.get("latency_ms") is None]
    print(f"Fetching Jev's latency for {len(missing)} requests from OpenRouter…")
    with ThreadPoolExecutor(4) as pool:
        for row, ms in zip(missing, pool.map(lambda r: fetch_latency(env, r["response"]["id"]), missing)):
            row["latency_ms"] = ms
    (out_dir / "raw.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))

    by_item = {}
    for row in sorted(rows, key=lambda r: r["run"]):
        by_item.setdefault(row["item"], []).append(row)
    responses = [r["response"] for r in rows]
    latencies = [r["latency_ms"] for r in rows if r.get("latency_ms") is not None]
    roundtrips = [r["roundtrip_ms"] for r in rows if r.get("roundtrip_ms") is not None]
    meta = {"started": out_dir.name, "model": responses[0]["model"], "runs": len(rows) // len(by_item),
            "requests": len(rows), "input_tokens": sum(r["usage"]["input_tokens"] for r in responses),
            "cost": sum(r["usage"].get("cost", 0) for r in responses),
            "latency_ms": timing_stats(latencies), "roundtrip_ms": timing_stats(roundtrips)}
    summaries = [summarise_item(i, by_item[label(i)]) for i in items]
    (out_dir / "summary.json").write_text(json.dumps({"meta": meta, "items": summaries}, indent=2, ensure_ascii=False))
    write_markdown(out_dir / "summary.md", summaries, meta)
    print(f"Wrote {out_dir.relative_to(ROOT)}/ (cost ${meta['cost']:.5f}, "
          f"Jev's median latency {meta['latency_ms']['median'] if latencies else '?'} ms)")


def timing_stats(values):
    if not values:
        return None
    return {"median": round(statistics.median(values)), "mean": round(statistics.mean(values)),
            "min": min(values), "max": max(values), "n": len(values)}


if __name__ == "__main__":
    main()
