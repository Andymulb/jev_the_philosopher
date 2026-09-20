#!/usr/bin/env python3
"""Generate the numbers, tables and plot data the paper uses, straight from the results.

Usage: python3 paper/make_data.py [results/<run>/summary.json]
Writes paper/generated/*.tex and *.dat; main.tex \\input s them, so no number is typed by hand.
"""
import json
import statistics
import sys
from pathlib import Path

PAPER = Path(__file__).parent
ROOT = PAPER.parent
sys.path.insert(0, str(ROOT))
from analysis import HUMAN_TIMES, UNDECIDED, build_item  # noqa: E402  (shared with the web page)

OUT = PAPER / "generated"


def tex(text):
    """Escape plain text for LaTeX."""
    repl = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
            "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}
    return "".join(repl.get(c, c) for c in text)


def macro(name, value):
    return f"\\newcommand{{\\{name}}}{{{value}}}\n"


def verdict_word(v):
    return {"agrees": "same", "disagrees": "different", "undecided": "undecided"}[v]


def jev_answer(q):
    if q["type"] == "noul":
        return f"yes-prob.\\ {q['p']:.2f}"
    if q["type"] == "choice":
        opt = next(o for o in q["options"] if o["key"] == q["mode"])
        return f"{tex(opt['label'].split(':')[0])} ({opt['p']:.2f})"
    return f"score {q['score']:.2f} of {len(q['levels']) - 1}"


def film_answer(q):
    if "film" not in q:
        return "--"
    if q["type"] == "noul":
        return "yes" if q["film"] else "no"
    return tex(next(o for o in q["options"] if o["key"] == q["film"])["label"].split(":")[0])


def main():
    summary_path = Path(sys.argv[1]) if len(sys.argv) > 1 else sorted(ROOT.glob("results/*/summary.json"))[-1]
    summary = json.loads(summary_path.read_text())
    questions = json.loads((ROOT / "questions.json").read_text())
    by_label = {(s["id"], s["variant"]): s for s in summary["items"]}
    pairs = [(i, by_label[(i["id"], i.get("variant"))]) for i in questions["items"]]
    items = [build_item(i, s, questions["shared_states"]) for i, s in pairs]
    meta = summary["meta"]
    OUT.mkdir(exist_ok=True)

    # ---- headline numbers -------------------------------------------------
    verdicts = [q["verdict"] for i in items if i["kind"] == "questions" for q in i["questions"] if "verdict" in q]
    nouls = [q for i in items if i["kind"] == "questions" for q in i["questions"] if q["type"] == "noul"]
    spreads = [q["max"] - q["min"] for q in nouls]
    for i in items:
        if i["kind"] == "selection":
            spreads += [r["max"] - r["min"] for r in i["rows"]]
    selections = {i["id"]: i for i in items if i["kind"] == "selection"}

    # uncertainty vs latency (per question, using its request's median latency)
    pts = []
    for (raw_item, s), item in zip(pairs, items):
        if item["kind"] != "questions":
            continue
        for key, q in s["questions"].items():
            u = 1 - 2 * abs(q["mean"] - 0.5) if q["type"] == "noul" else 1 - q["mean_confidence"]
            pts.append((u, s["latency_ms"]["median"]))
    xs, ys = zip(*pts)
    sure = [y for x, y in pts if x < 0.3]
    torn = [y for x, y in pts if x > 0.8]
    human_fastest = min(r["s"] for r in HUMAN_TIMES["rows"])
    human_slowest = max(r["s"] for r in HUMAN_TIMES["rows"])

    def agrees_at_half(q):
        if q["type"] == "noul":
            return (q["p"] > 0.5) == q["film"]
        return q["mode"] == q["film"]
    agree_half = sum(agrees_at_half(q) for i in items if i["kind"] == "questions" for q in i["questions"] if "verdict" in q)

    lat = meta["latency_ms"]
    n = [
        macro("NAgreeHalf", agree_half),
        macro("NRuns", meta["runs"]), macro("NRequests", meta["requests"]),
        macro("NItems", len(items)), macro("NQuestionIds", len({i["id"] for i in items})),
        macro("InputTokens", f"{meta['input_tokens']:,}".replace(",", "\\,")),
        macro("TotalCost", f"{meta['cost']:.4f}"),
        macro("RunDate", "19 September 2026"), macro("ModelVersion", tex(meta["model"])),
        macro("LatMedian", lat["median"]), macro("LatMean", lat["mean"]),
        macro("LatMin", lat["min"]), macro("LatMax", lat["max"]),
        macro("LatMedianSec", f"{lat['median'] / 1000:.2f}"),
        macro("NAgree", verdicts.count("agrees")), macro("NDisagree", verdicts.count("disagrees")),
        macro("NUndecided", verdicts.count("undecided")), macro("NFilmQuestions", len(verdicts)),
        macro("BandLo", f"{UNDECIDED[0]:.2f}"), macro("BandHi", f"{UNDECIDED[1]:.2f}"),
        macro("MaxSpread", f"{max(spreads):.2f}"),
        macro("MedianSpread", f"{statistics.median(spreads):.3f}"),
        macro("OverlapOne", selections["Q1.1"]["overlap"]), macro("OverlapTwo", selections["Q2.1"]["overlap"]),
        macro("OverlapThree", selections["Q3.2"]["overlap"]),
        macro("CorrUncertaintyLatency", f"{statistics.correlation(xs, ys):.2f}"),
        macro("NCorrPoints", len(pts)),
        macro("LatSure", round(statistics.median(sure))), macro("NSure", len(sure)),
        macro("LatTorn", round(statistics.median(torn))), macro("NTorn", len(torn)),
        macro("HumanFastest", f"{human_fastest:.1f}"), macro("HumanSlowest", f"{human_slowest:.1f}"),
        macro("SpeedupLow", round(human_fastest * 1000 / lat["median"])),
        macro("SpeedupHigh", round(human_slowest * 1000 / lat["median"])),
        macro("CostPerDecision", f'{meta["cost"] / meta["requests"]:.5f}'),
        macro("CostPerMillion", round(meta["cost"] / meta["requests"] * 1e6)),
        macro("DecisionsPerHumanOne", round(human_fastest * 1000 / lat["median"])),
    ]
    (OUT / "numbers.tex").write_text("% generated by make_data.py; do not edit\n" + "".join(n))

    # ---- summary table (Table I) -----------------------------------------
    sel_over = f'{selections["Q1.1"]["overlap"]}, {selections["Q2.1"]["overlap"]} and {selections["Q3.2"]["overlap"]} of 10'
    summary_rows = [
        ("Questions put to Jev", f'{len(items)} requests covering {len({i["id"] for i in items})} questions, '
                                 f'{meta["runs"]} runs each ({meta["requests"]} requests)', "sec:method"),
        ("Same answer as the film", f'{verdicts.count("agrees")} of {len(verdicts)} questions '
                                    f'({verdicts.count("disagrees")} different, {verdicts.count("undecided")} undecided)', "sec:agreement"),
        ("Shared picks in the three bunker rounds", sel_over, "sec:rounds"),
        ("Stability over the repeated runs", f'largest spread {max(spreads):.2f}, median {statistics.median(spreads):.3f}', "sec:stability"),
        ("Jev's time per decision", f'median {lat["median"]}\\,ms (range {lat["min"]}--{lat["max"]}\\,ms)', "sec:timing"),
        ("Human time per dilemma \\cite{greene2001}", f'{human_fastest:.1f}--{human_slowest:.1f}\\,s', "sec:timing"),
        ("Cost of the whole experiment", f'\\${meta["cost"]:.4f}', "sec:method"),
    ]
    body = "\n".join(f"{label} & {value} & \\S\\ref{{{ref}}} \\\\" for label, value, ref in summary_rows)
    (OUT / "summary_table.tex").write_text(
        "% generated by make_data.py; do not edit\n"
        "\\begin{table*}[t]\n\\centering\n"
        "\\caption{Summary of results. Details in the sections listed.}\n\\label{tab:summary}\n\\small\n"
        "\\begin{tabular}{@{}>{\\raggedright\\arraybackslash}p{5.4cm}"
        ">{\\raggedright\\arraybackslash}p{8.6cm}l@{}}\n\\toprule\n"
        "Measure & Result & Section \\\\\n\\midrule\n"
        f"{body}\n"
        "\\bottomrule\n\\end{tabular}\n\\end{table*}\n")

    # ---- full results table (appendix) -----------------------------------
    rows = []
    for item in items:
        name = item["id"] + (f" ({item['variant']})" if item["variant"] else "")
        mark = r"$^{\dagger}$" if item["fromUser"] else ""
        if item["kind"] == "selection":
            rows.append(f"{name}{mark} & {tex(item['prompt'])} & Jev's top~10 (see Fig.~\\ref{{fig:rounds}}) "
                        f"& the film's 10 & {item['overlap']}/10 shared \\\\")
            continue
        for q in item["questions"]:
            verdict = verdict_word(q["verdict"]) if "verdict" in q else "--"
            if q.get("reference"):
                verdict += " (maths)"
            rows.append(f"{name}{mark} & {tex(q['prompt'])} & {jev_answer(q)} & {film_answer(q)} & {verdict} \\\\")
            name, mark = "", ""
    (OUT / "results_table.tex").write_text("% generated by make_data.py; do not edit\n" + "\n".join(rows) + "\n")

    # ---- every single value, for \val{ID}{key} in the text ----------------
    vals = ["% generated by make_data.py; do not edit"]
    def put(name, value):
        vals.append(f"\\expandafter\\def\\csname v@{name}\\endcsname{{{value}}}")
    for item in items:
        if item["kind"] != "questions":
            continue
        ident = item["id"] + (f"-{item['variant'].split()[0]}" if item["variant"] else "")
        for q in item["questions"]:
            if q["type"] == "noul":
                put(f"{ident}@{q['key']}", f"{q['p']:.2f}")
            elif q["type"] == "choice":
                for o in q["options"]:
                    put(f"{ident}@{q['key']}@{o['key']}", f"{o['p']:.2f}")
            else:
                put(f"{ident}@{q['key']}", f"{q['score']:.2f}")
    (OUT / "values.tex").write_text("\n".join(vals) + "\n")

    # ---- yes/no dot plot data --------------------------------------------
    dots = []
    for item in items:
        if item["kind"] != "questions":
            continue
        n_noul = sum(q["type"] == "noul" for q in item["questions"])
        for q in item["questions"]:
            if q["type"] != "noul":
                continue
            label = item["title"] if n_noul == 1 else f"{item['title']} ({q['key'].replace('_', ' ')})"
            film = {"agrees": "same", "disagrees": "diff", "undecided": "undec"}.get(q.get("verdict"), "none")
            filmval = ("1" if q["film"] else "0") if "film" in q else "nan"
            dots.append((f"{item['id']} {label}", q["p"], q["min"], q["max"], film, filmval))
    lines = ["idx p lo hi film filmval label"]
    for k, (label, p, lo, hi, film, filmval) in enumerate(reversed(dots)):
        lines.append(f'{k} {p:.3f} {lo:.3f} {hi:.3f} {film} {filmval} {{{tex(label)}}}')
    (OUT / "nouls.dat").write_text("\n".join(lines) + "\n")
    (OUT / "nouls_count.tex").write_text(macro("NNouls", len(dots)))

    # ---- bunker rounds ----------------------------------------------------
    for key, round_id in (("one", "Q1.1"), ("two", "Q2.1"), ("three", "Q3.2")):
        sel = selections[round_id]
        lines = ["idx p film inside name"]
        for k, r in enumerate(reversed(sel["rows"])):
            rank = len(sel["rows"]) - k
            lines.append(f"{k} {r['p']:.3f} {int(r['film'])} {int(rank <= 10)} {{{tex(r['name'])}}}")
        (OUT / f"round_{key}.dat").write_text("\n".join(lines) + "\n")

    # ---- thinking time ----------------------------------------------------
    lines = ["idx s isjev txt label"]
    rows_t = [("Jev", "any question (median)", lat["median"] / 1000, f"{lat['median'] / 1000:.2f} s")] + \
             [("People", r["label"], r["s"], r"$\approx$" + r.get("note", f"{r['s']:.1f} s")) for r in HUMAN_TIMES["rows"]]
    for k, (who, label, s, txt) in enumerate(reversed(rows_t)):
        lines.append(f"{k} {s:.3f} {int(who == 'Jev')} {{{txt}}} {{{tex(who + ', ' + label)}}}")
    (OUT / "timing.dat").write_text("\n".join(lines) + "\n")

    print(f"paper/generated/ from {summary_path.relative_to(ROOT)}: {len(items)} items, {len(dots)} yes/no questions, "
          f"verdicts same {verdicts.count('agrees')} / different {verdicts.count('disagrees')} / undecided {verdicts.count('undecided')}")


if __name__ == "__main__":
    main()
