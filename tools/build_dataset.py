#!/usr/bin/env python3
"""Merge draft records + verification corrections + arc table into the app dataset.

Inputs:
  out/characters.draft.json
  out/corrections.json   (from the verification workflow)
  out/arcs.json          (from the verification workflow)
  out/portraits.json
Outputs:
  ../src/data/characters.json
  ../src/data/arcs.json
  out/final_report.txt
"""
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "out"
DATA = HERE.parent / "src" / "data"
DATA.mkdir(parents=True, exist_ok=True)

# per-character fixes where verification agents picked odd/echoed values
AFFILIATION_FIXES = {
    "Page One": "Beasts Pirates",
    "Ulti": "Beasts Pirates",
    "Johnny": "Bounty Hunters",
    "Yosaku": "Bounty Hunters",
    "Pierre": "Skypiea",
    "Pappag": "Takoyaki 8",
    "Conis": "Skypiea",
    "Igaram": "Alabasta Kingdom",
    "Kurozumi Orochi": "Kurozumi Family",
    "Stussy": "CP0",
    "Hiriluk": "Sakura Kingdom",
}
# vocabulary unification (spelling/recognizability)
AFFILIATION_RENAMES = {
    "Kouzuki Family": "Kozuki Family",
    "Arabasta Kingdom": "Alabasta Kingdom",
    "Arabasta": "Alabasta Kingdom",
    "Spiders Cafe": "Baroque Works",
}

VALID_GENDER = {"Male", "Female", "Other", "Unknown"}
VALID_DF = {"Paramecia", "Special Paramecia", "Zoan", "Ancient Zoan", "Mythical Zoan",
            "Logia", "Unknown"}
VALID_HAKI = {"Armament", "Observation", "Conqueror", "Unknown"}
VALID_ORIGIN = {"East Blue", "North Blue", "South Blue", "West Blue", "Grand Line",
                "Calm Belt", "Red Line", "Sky Island", "Unknown"}


def main():
    drafts = {r["requested"]: r for r in json.loads((OUT / "characters.draft.json").read_text())}
    corrections = {c["requested"]: c for c in json.loads((OUT / "corrections.json").read_text())}
    arcs = json.loads((OUT / "arcs.json").read_text())
    portraits = json.loads((OUT / "portraits.json").read_text())

    arc_names = [a["name"] for a in arcs]

    def arc_for(ch):
        if ch is None:
            return None
        for a in arcs:
            if a["startChapter"] <= ch <= a["endChapter"]:
                return a["name"]
        return None

    problems = []
    final = []
    for req, d in drafts.items():
        c = corrections.get(req)
        if not c:
            problems.append(f"NO CORRECTION for {req} (using draft)")
            c = {}

        def pick(key, default=None):
            return c.get(key, d.get(key, default))

        gender = pick("gender") or "Unknown"
        if gender not in VALID_GENDER:
            problems.append(f"{req}: bad gender {gender!r}")
            gender = "Unknown"

        affiliation = (pick("affiliation") or "Unknown").replace("Elbaph", "Elbaf")
        affiliation = AFFILIATION_RENAMES.get(affiliation, affiliation)
        affiliation = AFFILIATION_FIXES.get(req, affiliation)

        dftypes = [t.replace(" (Artificial", "").strip() for t in (pick("dfTypes") or [])]
        bad = [t for t in dftypes if t not in VALID_DF]
        if bad:
            problems.append(f"{req}: bad dfTypes {bad}")
            dftypes = [t for t in dftypes if t in VALID_DF]

        haki = pick("haki") or []
        bad = [h for h in haki if h not in VALID_HAKI]
        if bad:
            problems.append(f"{req}: bad haki {bad}")
            haki = [h for h in haki if h in VALID_HAKI]

        origin = pick("origin") or "Unknown"
        if origin not in VALID_ORIGIN:
            problems.append(f"{req}: bad origin {origin!r} -> Unknown")
            origin = "Unknown"

        chapter = pick("firstChapter") or d.get("firstChapter")
        arc = arc_for(chapter)
        if arc is None:
            problems.append(f"{req}: no arc for chapter {chapter}")

        bounty = pick("bounty")
        height = pick("heightCm")

        aliases = c.get("aliases", [])
        if d["name"] != req and d["name"] not in aliases:
            aliases = aliases + [d["name"]]
        aliases = [a for a in aliases if a.lower() != req.lower()]

        if c.get("notes"):
            problems.append(f"note {req}: {c['notes']}")

        final.append({
            "name": req,
            "aliases": aliases,
            "gender": gender,
            "affiliation": affiliation,
            "dfTypes": dftypes,
            "dfName": pick("dfName"),
            "haki": haki,
            "bounty": bounty if bounty is None else int(bounty),
            "heightCm": height,
            "origin": origin,
            "firstChapter": chapter,
            "firstEpisode": pick("firstEpisode"),
            "firstArc": arc,
            "portrait": portraits[req],
            "wikiPage": d["name"],
        })

    final.sort(key=lambda r: r["name"])
    (DATA / "characters.json").write_text(json.dumps(final, indent=1, ensure_ascii=False))
    (DATA / "arcs.json").write_text(json.dumps(
        [{"name": a["name"]} for a in arcs], indent=1, ensure_ascii=False))

    lines = [f"{len(final)} characters, {len(arc_names)} arcs", ""]
    lines.append("== affiliation vocabulary ==")
    for k, n in Counter(r["affiliation"] for r in final).most_common():
        lines.append(f"  {n:3d}  {k}")
    lines.append("== origin ==")
    for k, n in Counter(r["origin"] for r in final).most_common():
        lines.append(f"  {n:3d}  {k}")
    lines.append("== arcs used ==")
    for k, n in Counter(r["firstArc"] for r in final).most_common():
        lines.append(f"  {n:3d}  {k}")
    lines.append("")
    lines.append("== problems / notes ==")
    lines += ["  " + p for p in problems]
    (OUT / "final_report.txt").write_text("\n".join(lines))
    print("\n".join(lines[:8]))
    print(f"... report at {OUT / 'final_report.txt'}")


if __name__ == "__main__":
    main()
