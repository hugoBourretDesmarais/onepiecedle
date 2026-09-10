#!/usr/bin/env python3
"""Scrape when the reader learned each of a character's properties.

Companion to fetch_bounties.py, which does the same job for bounties. Between
them they give the spoiler limit a date for every value on a character card.

How datable each field is varies a lot:
  height       - the Char Box tags its values "(debut)" / "(after timeskip)"
  haki         - the Abilities pages have per-type sections full of chapter refs
  devil fruit  - the Abilities pages have a Devil Fruit section, likewise
  affiliation  - not datable at all; the Char Box lists crews in no particular
                 order and mostly without refs, so this only collects candidates
                 for review and marks them needsResearch

Outputs:
  tools/out/history.raw.json     - per character, per field
  tools/out/history_report.json  - what could not be dated
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from fetch_bounties import (  # noqa: E402
    fetch_content, find_template, split_fields, iter_templates, qref_chapter,
)

HERE = Path(__file__).parent
OUT = HERE / "out"
DATA = HERE.parent / "src" / "data"

# Luffy's two-year training ends here; every "after timeskip" value dates to it.
TIMESKIP_CHAPTER = 598

HAKI_HEADINGS = {
    "armament": "Armament",
    "busoshoku": "Armament",
    "observation": "Observation",
    "kenbunshoku": "Observation",
    "supreme king": "Conqueror",
    "conqueror": "Conqueror",
    "haoshoku": "Conqueror",
}


def strip_markup(s):
    for _n, _p, block in list(iter_templates(s)):
        s = s.replace(block, " ")
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\[\[([^\]|]*\|)?([^\]]*)\]\]", r"\2", s)
    return re.sub(r"\s+", " ", s).strip()


def section_chapters(text, heading_re):
    """-> {heading: sorted chapters} for every heading matching heading_re."""
    out = {}
    if not text:
        return out
    for m in re.finditer(r"^=+\s*([^=\n]+?)\s*=+\s*$", text, re.M):
        title = m.group(1)
        if not heading_re.search(title):
            continue
        start = m.end()
        nxt = re.search(r"^=+[^=\n]+=+\s*$", text[start:], re.M)
        block = text[start:start + (nxt.start() if nxt else 4000)]
        chaps = sorted({c for n, p, _ in iter_templates(block)
                        if n.lower() in ("qref", "ref") and (c := qref_chapter(p))})
        out.setdefault(title, []).extend(chaps)
    return out


def parse_heights(raw, debut):
    """-> [{value, chapter, note}] newest first, or [] if there's no growth to track.

    The field tags its values: "(debut, child)", "(pre-timeskip)", "(after
    timeskip)". Only a genuine pre/post-timeskip pair is worth a timeline —
    "(age 13)" entries are trivia the card never showed.
    """
    if not raw:
        return []
    entries = []
    for seg in re.split(r"<br\s*/?>", raw):
        m = re.search(r"([\d,]+(?:\.\d+)?)\s*cm", seg)
        if not m:
            continue
        plain = strip_markup(seg).lower()
        if re.search(r"after timeskip|post.timeskip", plain):
            note, chapter = "after timeskip", TIMESKIP_CHAPTER
        elif re.search(r"child|flashback", plain):
            note, chapter = "child", debut
        elif re.search(r"debut|pre.timeskip", plain):
            note, chapter = "debut", debut
        else:
            note, chapter = strip_markup(seg)[:40], None
        entries.append({"value": float(m.group(1).replace(",", "")),
                        "chapter": chapter, "note": note})
    if not any(e["note"] == "after timeskip" for e in entries):
        return []
    # A childhood height only stands in when there is no adult one to show.
    if any(e["note"] == "debut" for e in entries):
        entries = [e for e in entries if e["note"] != "child"]
    entries = [e for e in entries if e["chapter"] is not None]
    entries.sort(key=lambda e: -e["chapter"])
    return entries if len(entries) > 1 else []


def main():
    chars = json.loads((DATA / "characters.json").read_text())
    pages = {c["name"]: c["wikiPage"] for c in chars}
    by_name = {c["name"]: c for c in chars}
    print(f"{len(chars)} characters")

    content = fetch_content(sorted(set(pages.values())))
    need_sub = [rt for (rt, txt) in content.values()
                if txt is not None and find_template(txt, "Char Box") is None]
    tabs = {}
    for req, (rt, txt) in fetch_content(
            [f"Template:{t} Tabs Top" for t in need_sub]).items():
        tabs[req[len("Template:"):-len(" Tabs Top")]] = txt

    # Abilities live on a subpage for the better-documented characters and
    # inline for everyone else.
    wants_abilities = sorted({pages[c["name"]] for c in chars
                              if c["haki"] or c["dfTypes"]})
    abilities = fetch_content([f"{t}/Abilities and Powers" for t in wants_abilities])
    print(f"{sum(1 for _rt, t in abilities.values() if t)} abilities subpages")

    haki_re = re.compile("|".join(HAKI_HEADINGS), re.I)
    fruit_re = re.compile(r"devil fruit", re.I)

    out, report = {}, {"undated_haki": [], "late_fruit_hint": [], "no_height_pair": 0}
    for name in sorted(pages):
        c = by_name[name]
        page = pages[name]
        rt, txt = content[page]
        debut = c["firstChapter"]
        box = find_template(txt, "Char Box") or find_template(tabs.get(rt), "Char Box")
        fields = split_fields(box) if box else {}

        _rt2, abil = abilities.get(f"{page}/Abilities and Powers", (None, None))
        ability_text = abil or txt

        rec = {"debutChapter": debut}

        heights = parse_heights(fields.get("height"), debut)
        if heights:
            rec["heightCm"] = heights
        elif c["heightCm"] is not None:
            report["no_height_pair"] += 1

        if c["haki"]:
            found = section_chapters(ability_text, haki_re)
            generic = min((min(v) for k, v in found.items()
                           if v and not any(w in k.lower() for w in HAKI_HEADINGS)),
                          default=None)
            entries = []
            for t in c["haki"]:
                chap, how = None, None
                for title, chaps in found.items():
                    low = title.lower()
                    if any(HAKI_HEADINGS[w] == t for w in HAKI_HEADINGS if w in low) and chaps:
                        chap = min(chaps) if chap is None else min(chap, min(chaps))
                        how = "section"
                if chap is None and generic is not None:
                    chap, how = generic, "generic Haki section"
                if chap is None:
                    report["undated_haki"].append(f"{name}: {t}")
                entries.append({"value": t, "chapter": chap, "source": how})
            entries.sort(key=lambda e: (e["chapter"] is None, e["chapter"] or 0))
            rec["haki"] = entries

        if c["dfTypes"]:
            # The earliest ref in the Devil Fruit section is not the reveal —
            # Robin's earliest is chapter 629, hundreds after readers saw her
            # power. Almost every fruit is shown when the character is, so debut
            # is the default and review only has to catch the late reveals.
            found = section_chapters(ability_text, fruit_re)
            hint = min((min(v) for v in found.values() if v), default=None)
            if hint is not None and hint > debut:
                report["late_fruit_hint"].append(f"{name}: debut {debut}, section {hint}")
            rec["devilFruit"] = {
                "chapter": debut,
                "source": "debut",
                "sectionHint": hint,
                "types": c["dfTypes"],
                "dfName": c["dfName"],
            }

        cands = []
        for seg in re.split(r"<br\s*/?>|;", fields.get("affiliation") or ""):
            if not seg.strip():
                continue
            chaps = [q for n, p, _ in iter_templates(seg)
                     if n.lower() == "qref" and (q := qref_chapter(p))]
            plain = strip_markup(seg)
            former = bool(re.search(r"former|disbanded|temporary", plain, re.I))
            label = re.sub(r"\(.*?\)", "", plain).strip().strip(",")
            if label:
                cands.append({"value": label, "chapter": min(chaps) if chaps else None,
                              "former": former})
        rec["affiliationCandidates"] = cands
        rec["currentAffiliation"] = c["affiliation"]
        rec["needsResearch"] = True
        out[name] = rec

    (OUT / "history.raw.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    (OUT / "history_report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False))
    print(f"height timelines: {sum(1 for r in out.values() if 'heightCm' in r)}")
    print(f"haki users: {sum(1 for r in out.values() if 'haki' in r)}, "
          f"undated types: {len(report['undated_haki'])}")
    print(f"fruit users: {sum(1 for r in out.values() if 'devilFruit' in r)}, "
          f"late-reveal hints: {len(report['late_fruit_hint'])}")


if __name__ == "__main__":
    main()
