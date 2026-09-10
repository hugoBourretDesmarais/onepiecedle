#!/usr/bin/env python3
"""Consolidate the property timelines into one file for build_dataset.py.

Sources, in increasing order of authority:
  out/history.raw.json      - the scrape (heights, haki hints, fruit defaults)
  out/portraits_pre.json    - pre-timeskip art, where the wiki has any
  out/review/aff*.json      - researched affiliation timelines + fruit reveals
  out/review/haki*.json     - researched haki dates
  out/history_review.json   - hand overrides, last word

Output:
  out/history.json          - {character: {affiliation, haki, devilFruit, heightCm, portrait}}
  out/history_merge_report.txt
"""
import json
import re
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "out"
REVIEW = OUT / "review"
DATA = HERE.parent / "src" / "data"

TIMESKIP_CHAPTER = 598


def load(path, default=None):
    return json.loads(path.read_text()) if path.exists() else default


def newest_first(entries):
    return sorted(entries, key=lambda e: -e["chapter"])


def main():
    chars = json.loads((DATA / "characters.json").read_text())
    by_name = {c["name"]: c for c in chars}
    raw = load(OUT / "history.raw.json", {})
    pre_art = load(OUT / "portraits_pre.json", {})
    overrides = load(OUT / "history_review.json", {})

    aff_results, haki_results, vocab_problems = {}, {}, []
    for f in sorted(REVIEW.glob("aff*.json")):
        d = json.loads(f.read_text())
        for r in d.get("results", []):
            aff_results[r["character"]] = r
        vocab_problems += [f"{f.name}: {p}" for p in d.get("vocabularyProblems", [])]
    # The first pass ran against a vocabulary with no CP9, Buggy Pirates, Drake
    # Pirates and the like, so some characters got an anachronistic label —
    # Drake's debut read "Marines", giving away his cover. fix*.json redoes
    # those against the widened list and wins.
    for f in sorted(REVIEW.glob("fix*.json")):
        d = json.loads(f.read_text())
        for r in d.get("results", []):
            prev = aff_results.get(r["character"], {})
            aff_results[r["character"]] = {**prev, **r}
        vocab_problems += [f"{f.name}: {p}" for p in d.get("remainingGaps", [])]
    for f in sorted(REVIEW.glob("haki*.json")):
        for r in json.loads(f.read_text()).get("results", []):
            haki_results[r["character"]] = r

    notes, out = [], {}
    for c in chars:
        name, debut = c["name"], c["firstChapter"]
        r = raw.get(name, {})
        h = {}

        # --- affiliation -------------------------------------------------
        res = aff_results.get(name)
        timeline = (res or {}).get("affiliationTimeline") or []
        timeline = [e for e in timeline if e.get("value") and e.get("chapter") is not None]
        if not timeline:
            notes.append(f"{name}: no researched affiliation, using current at debut")
            timeline = [{"value": c["affiliation"], "chapter": debut}]
        timeline = newest_first(timeline)
        # There must always be something to show from the moment they appear.
        if timeline[-1]["chapter"] > debut:
            timeline[-1] = {**timeline[-1], "chapter": debut}
        h["affiliation"] = [{"value": e["value"], "chapter": e["chapter"]} for e in timeline]

        # --- haki --------------------------------------------------------
        if c["haki"]:
            res = haki_results.get(name)
            entries = []
            for e in (res or {}).get("haki", []):
                if e.get("chapter") is None or e.get("value") not in c["haki"]:
                    continue
                entries.append({"value": e["value"], "chapter": max(e["chapter"], debut)})
            got = {e["value"] for e in entries}
            for missing in c["haki"]:
                if missing not in got:
                    notes.append(f"{name}: {missing} haki undated — hidden under a limit")
            h["haki"] = sorted(entries, key=lambda e: e["chapter"])

        # --- devil fruit --------------------------------------------------
        if c["dfTypes"]:
            reveal = (aff_results.get(name) or {}).get("devilFruitRevealChapter")
            chapter = max(reveal, debut) if reveal else debut
            h["devilFruit"] = [{"chapter": chapter, "types": c["dfTypes"], "name": c["dfName"]}]

        # --- height --------------------------------------------------------
        heights = r.get("heightCm") or []
        if heights:
            h["heightCm"] = newest_first(
                [{"value": e["value"], "chapter": e["chapter"]} for e in heights])

        # --- portrait -------------------------------------------------------
        if name in pre_art:
            h["portrait"] = [
                {"value": c["portrait"], "chapter": TIMESKIP_CHAPTER},
                {"value": pre_art[name], "chapter": debut},
            ]

        # --- hand overrides -------------------------------------------------
        for field, value in (overrides.get(name) or {}).items():
            if field.startswith("_"):
                continue
            h[field] = value

        out[name] = h

    (OUT / "history.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))

    lines = [f"{len(out)} characters"]
    lines.append(f"affiliation timelines with a change: "
                 f"{sum(1 for v in out.values() if len(v['affiliation']) > 1)}")
    lines.append(f"haki dated: {sum(len(v.get('haki', [])) for v in out.values())} of "
                 f"{sum(len(c['haki']) for c in chars)}")
    lines.append(f"late fruit reveals: "
                 f"{sum(1 for n, v in out.items() if v.get('devilFruit') and v['devilFruit'][-1]['chapter'] > by_name[n]['firstChapter'])}")
    lines.append(f"height timelines: {sum(1 for v in out.values() if 'heightCm' in v)}")
    lines.append(f"pre-timeskip portraits: {sum(1 for v in out.values() if 'portrait' in v)}")
    lines.append("")
    lines.append(f"== affiliation vocabulary now in use ({len({e['value'] for v in out.values() for e in v['affiliation']})}) ==")
    for k, n in Counter(e["value"] for v in out.values() for e in v["affiliation"]).most_common():
        lines.append(f"  {n:3d}  {k}")
    lines.append("")
    lines.append("== vocabulary problems raised in review ==")
    lines += ["  " + p for p in vocab_problems]
    lines.append("")
    lines.append("== notes ==")
    lines += ["  " + n for n in notes]
    (OUT / "history_merge_report.txt").write_text("\n".join(lines))
    print("\n".join(lines[:8]))
    print(f"... report at {OUT / 'history_merge_report.txt'}")


if __name__ == "__main__":
    main()
