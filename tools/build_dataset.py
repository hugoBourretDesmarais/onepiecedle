#!/usr/bin/env python3
"""Merge draft records + verification corrections + arc table into the app dataset.

Inputs:
  out/characters.draft.json
  out/corrections.json   (from the verification workflow)
  out/arcs.json          (from the verification workflow)
  out/portraits.json
  out/bounties.json      (from fetch_bounties.py)
  out/bounty_dates.json  (reviewed dates for bounties the wiki doesn't date)
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
# Baroque Works agents are known to readers by their codename, not their real
# name — "Zala" or "Drophy" is unrecognizable on its own.
CODENAMES = {
    "Crocodile": "Mr. 0",
    "Nico Robin": "Miss All Sunday",
    "Daz Bonez": "Mr. 1",
    "Zala": "Miss Doublefinger",
    "Bentham": "Mr. 2 Bon Clay",
    "Galdino": "Mr. 3",
    "Drophy": "Miss Merry Christmas",
    "Gem": "Mr. 5",
    "Mikita": "Miss Valentine",
    "Nefertari Vivi": "Miss Wednesday",
    "Igaram": "Mr. 8",
}

# vocabulary unification (spelling/recognizability)
AFFILIATION_RENAMES = {
    "Kouzuki Family": "Kozuki Family",
    "Arabasta Kingdom": "Alabasta Kingdom",
    "Arabasta": "Alabasta Kingdom",
    "Spiders Cafe": "Baroque Works",
}

# Most bounties past the Straw Hats' were never printed in a chapter — they come
# from a databook, an exhibition, a film or a novel. Those still have a moment
# the reader could know them: publication. Each value below is the chapter being
# serialised then, so the spoiler limit hides the figure until the player has
# read that far. The Vivre Card boosters ran from 2018 into 2023, so its date is
# the first release and is clamped to the character's debut on use.
SOURCE_CHAPTER = {
    "data=vivre card": 918,          # Vivre Card Databook, from Sept 2018
    "special=marinebounties": 1133,  # Oda's Cross Guild Q&A, Volume 111
    "data=blue": 250,                # One Piece Blue, Aug 2002
    "data=red": 264,                 # One Piece Red, Dec 2002
    "data=yellow": 410,              # One Piece Yellow, Apr 2006
    "data=green": 605,               # One Piece Green, Nov 2010
    "data=blue deep": 688,           # One Piece Blue Deep, Nov 2012
    "magazine=3": 918,               # One Piece Magazine Vol.3, Sept 2018
    "novel=a2": 918,                 # Novel A vol.2, 2018
    "novel=kikoku": 880,             # Novel Law: The Hour of Kikoku, 2017
    "other=OP10": 660,               # the One Piece Exhibition, March 2012
    "movie=15": 1058,                # Film Red, Aug 2022
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
    bounties = json.loads((OUT / "bounties.json").read_text())
    bounty_dates = json.loads((OUT / "bounty_dates.json").read_text())
    history = json.loads((OUT / "history.json").read_text())

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

        # Newest first, as the wiki lists them. A missing chapter means we could
        # not work out when the reader learned the figure, so a spoiler-limited
        # board has to leave it out rather than risk showing it too early.
        bounty_history = []
        for e in bounties.get(req, []):
            ch = e["chapter"]
            if ch is None:
                ch = bounty_dates.get(f"{req}|{e['amount']}")
            if ch is None and e.get("source"):
                ch = SOURCE_CHAPTER.get(e["source"])
                # A databook can't have told you a bounty before you met them.
                if ch is not None and chapter is not None:
                    ch = max(ch, chapter)
            if ch is None:
                problems.append(
                    f"{req}: undated bounty ฿{e['amount']:,} ({e.get('source') or 'no source'})"
                    " — hidden under a spoiler limit")
            bounty_history.append({"amount": e["amount"], "chapter": ch})
        if bounty_history and bounty_history[0]["amount"] != bounty:
            problems.append(
                f"{req}: latest bounty {bounty} != history head {bounty_history[0]['amount']}")

        # Everything else that changes as the story goes: affiliation, haki,
        # devil fruit, height, portrait. merge_history.py assembles it.
        hist = history.get(req, {})
        if not hist.get("affiliation"):
            problems.append(f"{req}: no affiliation timeline — card cannot rewind")
        undated = len(pick("haki") or []) - len(hist.get("haki", []))
        if undated > 0:
            problems.append(f"{req}: {undated} haki type(s) undated — hidden under a limit")

        aliases = c.get("aliases", [])
        if d["name"] != req and d["name"] not in aliases:
            aliases = aliases + [d["name"]]
        aliases = [a for a in aliases if a.lower() != req.lower()]

        if c.get("notes"):
            problems.append(f"note {req}: {c['notes']}")

        codename = CODENAMES.get(req)
        if codename and codename not in aliases:
            aliases = aliases + [codename]

        final.append({
            "name": req,
            "codename": codename,
            "aliases": aliases,
            "gender": gender,
            "affiliation": affiliation,
            "dfTypes": dftypes,
            "dfName": pick("dfName"),
            "haki": haki,
            "bounty": bounty if bounty is None else int(bounty),
            "bounties": bounty_history,
            "history": hist,
            "heightCm": height,
            "origin": origin,
            "firstChapter": chapter,
            "firstEpisode": pick("firstEpisode"),
            "firstArc": arc,
            "portrait": portraits[req],
            "wikiPage": d["name"],
        })

    # Crews a character only ever belonged to earlier in the story, so they
    # never appear as anyone's current affiliation but are what a reader at that
    # point would name them by. Without these the timelines have to reach for
    # something anachronistic — X Drake's debut reading "Marines" gives away the
    # cover he keeps for another 300 chapters.
    historical_only = {
        "CP9", "CP5", "Buggy Pirates", "Alvida Pirates", "Drake Pirates",
        "Bellamy Pirates", "Rumbar Pirates", "Drum Kingdom", "Rebel Army",
        "Kyoshiro Family", "Hyogoro Family", "Mt. Atama Thieves", "Underworld",
        "Centaur Patrol Unit", "Twin Capes", "Kuja Tribe", "MADS",
        "Bliking Pirates", "Charlotte Family", "Four Emperors",
        "Vegapunk's Satellites",
    }
    vocabulary = {r["affiliation"] for r in final} | historical_only
    for r in final:
        for entry in r["history"].get("affiliation", []):
            if entry["value"] not in vocabulary:
                problems.append(f"{r['name']}: historical affiliation "
                                f"{entry['value']!r} is outside the vocabulary")

    final.sort(key=lambda r: r["name"])
    (DATA / "characters.json").write_text(json.dumps(final, indent=1, ensure_ascii=False))
    (DATA / "arcs.json").write_text(json.dumps(
        [{"name": a["name"], "endChapter": a["endChapter"]} for a in arcs],
        indent=1, ensure_ascii=False))

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
