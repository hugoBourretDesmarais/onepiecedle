#!/usr/bin/env python3
"""Write one dossier file per character: draft record + raw Char Box +
Haki/Abilities section excerpts, for the verification agents."""
import json
import re
from pathlib import Path

import fetch_wiki as fw

HERE = Path(__file__).parent
OUT = HERE / "out"
DOSS = OUT / "dossier"
DOSS.mkdir(exist_ok=True)


def section_excerpt(text, heading_re, limit=2500):
    m = re.search(r"^=+\s*(" + heading_re + r")\s*=+\s*$", text, re.M | re.I)
    if not m:
        return None
    start = m.end()
    nxt = re.search(r"^==[^=].*==\s*$", text[start:], re.M)
    end = start + (nxt.start() if nxt else len(text) - start)
    return text[start:end][:limit]


def main():
    roster = json.loads((HERE / "roster.json").read_text())
    names = roster["original"] + roster["additions"]
    recs = {r["requested"]: r for r in json.loads((OUT / "characters.draft.json").read_text())}

    content = fw.fetch_content(names)  # cached
    need_sub = [rt for (rt, txt) in content.values()
                if txt is not None and fw.extract_charbox(txt) is None]
    subs = fw.fetch_content([f"Template:{t} Tabs Top" for t in need_sub])
    sub_by_base = {req[len("Template:"):-len(" Tabs Top")]: txt
                   for req, (rt2, txt) in subs.items()}

    for i, name in enumerate(names):
        rt, txt = content[name]
        rec = recs[name]
        box_src = txt if (txt and "{{Char Box" in txt) else sub_by_base.get(rt, "")
        m = re.search(r"\{\{Char Box.*", box_src or "", re.S)
        raw_box = ""
        if m:
            depth = 0
            j = m.start()
            s = box_src
            while j < len(s):
                if s[j:j+2] == "{{":
                    depth += 1
                    j += 2
                elif s[j:j+2] == "}}":
                    depth -= 1
                    j += 2
                    if depth == 0:
                        break
                else:
                    j += 1
            raw_box = s[m.start():j]

        haki_x = section_excerpt(txt or "", r"Haki") if txt else None
        abil_x = section_excerpt(txt or "", r"Abilities and Powers|Abilities") if txt else None
        intro = (txt or "").strip()[:1200]

        slug = re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_")
        out = [
            f"# {name} (wiki page: {rt})",
            "\n## Parsed draft record\n",
            json.dumps(rec, indent=1, ensure_ascii=False),
            "\n## Raw Char Box wikitext\n",
            raw_box[:4000] or "(none)",
            "\n## Page intro (excerpt)\n",
            intro,
        ]
        if abil_x:
            out += ["\n## Abilities section (excerpt)\n", abil_x]
        if haki_x:
            out += ["\n## Haki section (excerpt)\n", haki_x]
        (DOSS / f"{i:03d}_{slug}.md").write_text("\n".join(out))
    print(f"wrote {len(names)} dossiers to {DOSS}")


if __name__ == "__main__":
    main()
