#!/usr/bin/env python3
"""Shared scoring logic: turn a run's summary.json into per-question results.

Used by paper/make_data.py, which turns a run into the numbers, tables and plot data
the paper uses. Kept separate so that any other renderer reports the same numbers.
"""
import re

# A yes-probability inside this band counts as "undecided" rather than yes or no.
UNDECIDED = (0.45, 0.55)

# Human decision times, read off Fig. 3 of Greene et al. (2001), Science 293:2105, to about ±0.1 s.
# 9 participants in an fMRI scanner read each dilemma at their own pace (max 46 s) and pressed a button.
HUMAN_TIMES = {
    "source": "Greene et al. 2001, Science 293:2105, Fig. 3",
    "rows": [
        {"label": "switch the track: “appropriate”", "s": 4.6},
        {"label": "push the man: “inappropriate”", "s": 5.0},
        {"label": "a question with no moral side", "s": 5.5, "note": "5.5–6.0 s"},
        {"label": "push the man: “appropriate”, against the gut", "s": 6.8},
    ],
}


def scenario_text(state, shared):
    parts = []
    for key, value in state.items():
        if isinstance(value, str) and value.startswith("@"):
            continue  # the shared bunker rules are printed once per section
        parts.append(value)
    return " ".join(parts)


def verdict(q, film):
    """Compare Jev's aggregate answer with the film's (or a known reference answer)."""
    if q["type"] == "noul":
        if UNDECIDED[0] <= q["mean"] <= UNDECIDED[1]:
            return "undecided"
        return "agrees" if (q["mean"] > 0.5) == film else "disagrees"
    return "agrees" if q["mode"] == film else "disagrees"


def build_item(item, summary, shared):
    """One question group: its scenario, Jev's answers, the film's answer and the comparison."""
    out = {"id": item["id"], "variant": item.get("variant"), "section": item["section"],
           "title": item["title"], "fromUser": item.get("source") == "user recollection",
           "scenario": scenario_text(item["state"], shared), "note": item.get("film_note"),
           "runs": summary["runs"], "latency": (summary.get("latency_ms") or {}).get("median")}
    if item.get("kind") == "selection":
        sel = summary["selection"]
        out["kind"] = "selection"
        prompt = re.sub(r",? ?(the )?\(?\{card\}\)?,?", "", item["instructions_template"])
        out["prompt"] = prompt.replace("{name}", "each person")
        out["rows"] = [{"name": r["name"], "card": r["card"], "p": round(r["mean"], 3),
                        "top10": r["top10_runs"], "film": r["film_chose"],
                        "min": round(min(summary["questions"][r["name"]]["values"]), 3),
                        "max": round(max(summary["questions"][r["name"]]["values"]), 3)} for r in sel["ranking"]]
        out["overlap"] = sel["overlap_with_film"]
        return out
    expected = item.get("film") or item.get("reference") or {}
    out["kind"] = "questions"
    out["questions"] = []
    for key, spec in item["questions"].items():
        q = summary["questions"][key]
        entry = {"key": key, "type": spec["type"], "prompt": spec["instructions"]}
        if spec["type"] == "noul":
            entry.update(p=round(q["mean"], 3), min=round(q["min"], 3), max=round(q["max"], 3), yes=q["yes_runs"])
        elif spec["type"] == "choice":
            entry["options"] = [{"key": k, "label": label, "p": round(q["mean_probabilities"][k], 3),
                                 "picked": q["counts"].get(k, 0)} for k, label in spec["criteria"].items()]
            entry.update(mode=q["mode"], confidence=round(q["mean_confidence"], 2))
        else:
            entry.update(score=round(q["mean"], 2), levels=spec["criteria"], confidence=round(q["mean_confidence"], 2))
        if key in expected:
            entry["film"] = expected[key]
            entry["reference"] = "reference" in item
            entry["verdict"] = verdict(q, expected[key])
        out["questions"].append(entry)
    return out
