#!/usr/bin/env python3
"""Fetch character data from the One Piece wiki API and build a draft dataset.

Outputs:
  tools/out/characters.draft.json  - parsed per-character records
  tools/out/report.json            - missing/ambiguous fields needing review
  tools/out/images.json            - portrait URL per character
"""
import hashlib
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://onepiece.fandom.com/api.php"
UA = {"User-Agent": "OnePieceDleFanProject/1.0 (personal, low-volume data fetch)"}
HERE = Path(__file__).parent
CACHE = HERE / "cache"
OUT = HERE / "out"
CACHE.mkdir(exist_ok=True)
OUT.mkdir(exist_ok=True)


def api_get(params, cache_key):
    cache_file = CACHE / (cache_key + ".json")
    if cache_file.exists():
        return json.loads(cache_file.read_text())
    qs = urllib.parse.urlencode({**params, "format": "json"})
    req = urllib.request.Request(f"{API}?{qs}", headers=UA)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read().decode())
            cache_file.write_text(json.dumps(data))
            time.sleep(0.4)
            return data
        except Exception as e:
            print(f"  retry {attempt+1} for {cache_key}: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"failed: {cache_key}")


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def fetch_content(titles):
    """Return {requested_title: (resolved_title, wikitext)}"""
    result = {}
    for bi, batch in enumerate(chunks(titles, 20)):
        bh = hashlib.md5("|".join(batch).encode()).hexdigest()[:10]
        d = api_get({
            "action": "query", "titles": "|".join(batch),
            "prop": "revisions", "rvprop": "content", "rvslots": "main",
            "redirects": 1,
        }, f"content_{bh}")
        q = d["query"]
        redir = {}
        for r in q.get("normalized", []) + q.get("redirects", []):
            redir[r["from"]] = r["to"]
        resolved = {}
        for t in batch:
            r = t
            seen = set()
            while r in redir and r not in seen:
                seen.add(r)
                r = redir[r]
            resolved[t] = r
        by_title = {}
        for pid, p in q["pages"].items():
            if int(pid) < 0:
                by_title[p.get("title", "")] = None
                continue
            by_title[p["title"]] = p["revisions"][0]["slots"]["main"]["*"]
        for t in batch:
            rt = resolved[t]
            result[t] = (rt, by_title.get(rt))
    return result


def fetch_categories(titles):
    """Return {resolved_title: [category names]}"""
    result = {}
    for bi, batch in enumerate(chunks(titles, 20)):
        cont = {}
        while True:
            d = api_get({
                "action": "query", "titles": "|".join(batch),
                "prop": "categories", "cllimit": "max", "redirects": 1, **cont,
            }, f"cats_{bi:03d}_{cont.get('clcontinue','0').replace('|','_')[:40]}")
            for pid, p in d["query"]["pages"].items():
                cats = [c["title"].replace("Category:", "") for c in p.get("categories", [])]
                result.setdefault(p["title"], []).extend(cats)
            if "continue" in d:
                cont = {"clcontinue": d["continue"]["clcontinue"]}
            else:
                break
    return result


def fetch_images(titles):
    """Return {resolved_title: image_url}"""
    result = {}
    for bi, batch in enumerate(chunks(titles, 20)):
        d = api_get({
            "action": "query", "titles": "|".join(batch),
            "prop": "pageimages", "piprop": "original", "redirects": 1,
        }, f"img_{bi:03d}")
        for pid, p in d["query"]["pages"].items():
            orig = p.get("original", {}).get("source")
            if orig:
                result[p["title"]] = orig
    return result


def fetch_category_members(cat):
    members = []
    cont = {}
    i = 0
    while True:
        d = api_get({
            "action": "query", "list": "categorymembers",
            "cmtitle": f"Category:{cat}", "cmlimit": "max", **cont,
        }, f"catmem_{cat.replace(' ', '_')}_{i}")
        members += [m["title"] for m in d["query"]["categorymembers"]]
        if "continue" in d:
            cont = {"cmcontinue": d["continue"]["cmcontinue"]}
            i += 1
        else:
            break
    return members


# ---------- wikitext parsing ----------

def extract_charbox(text):
    if not text:
        return None
    m = re.search(r"\{\{Char Box", text)
    if not m:
        return None
    # balanced braces scan
    i = m.start()
    depth = 0
    j = i
    while j < len(text):
        if text[j:j+2] == "{{":
            depth += 1
            j += 2
        elif text[j:j+2] == "}}":
            depth -= 1
            j += 2
            if depth == 0:
                break
        else:
            j += 1
    box = text[i:j]
    # split top-level | fields
    fields = {}
    depth = 0
    cur = []
    parts = []
    k = 0
    while k < len(box):
        c2 = box[k:k+2]
        if c2 in ("{{", "[["):
            depth += 1
            cur.append(c2)
            k += 2
        elif c2 in ("}}", "]]"):
            depth -= 1
            cur.append(c2)
            k += 2
        elif box[k] == "|" and depth == 1:
            parts.append("".join(cur))
            cur = []
            k += 1
        else:
            cur.append(box[k])
            k += 1
    parts.append("".join(cur))
    for part in parts[1:]:
        if "=" in part:
            key, _, val = part.partition("=")
            val = val.strip()
            if val.endswith("}}") and val.count("}}") > val.count("{{"):
                val = val[:-2].strip()
            fields[key.strip().lower()] = val
    return fields


def strip_refs(s):
    if not s:
        return s
    # remove Qref/ref/Web ref templates (balanced)
    out = []
    k = 0
    while k < len(s):
        if s[k:k+2] == "{{":
            depth = 0
            j = k
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
            inner = s[k+2:j-2]
            name = inner.split("|")[0].strip().lower()
            if name in ("qref", "web ref", "ref", "vol ref", "sbs ref"):
                k = j
                continue
            if name == "nihongo":
                # {{Nihongo|English|kanji|romaji|extra}} -> English
                parts = inner.split("|")
                out.append(parts[1] if len(parts) > 1 else "")
                k = j
                continue
            if name == "b":
                out.append("฿")
                k = j
                continue
            if name == "ruby":
                parts = inner.split("|")
                out.append(parts[1] if len(parts) > 1 else "")
                k = j
                continue
            # keep other templates' text form
            out.append(s[k:j])
            k = j
        else:
            out.append(s[k])
            k += 1
    s = "".join(out)
    s = re.sub(r"<ref[^>]*/>", "", s)
    s = re.sub(r"<ref[^>]*>.*?</ref>", "", s, flags=re.S)
    s = re.sub(r"<!--.*?-->", "", s, flags=re.S)
    return s.strip()


def strip_links(s):
    if not s:
        return s
    s = re.sub(r"\[\[([^\]|]*)\|([^\]]*)\]\]", r"\2", s)
    s = re.sub(r"\[\[([^\]]*)\]\]", r"\1", s)
    s = s.replace("'''", "").replace("''", "")
    return s.strip()


def parse_first(raw):
    """-> (chapter, episode)"""
    if not raw:
        return None, None
    s = strip_refs(raw)
    chap = re.search(r"Chapter (\d+)", s)
    ep = re.search(r"Episode (\d+)", s)
    return (int(chap.group(1)) if chap else None,
            int(ep.group(1)) if ep else None)


def parse_bounty(raw):
    """-> int berries (latest = first listed) or None if field absent/unknown"""
    if raw is None:
        return None
    s = strip_links(strip_refs(raw))
    m = re.search(r"([\d,]{3,})", s)
    if not m:
        return None
    return int(m.group(1).replace(",", ""))


def parse_height(raw):
    """-> centimeters (latest listed) or None"""
    if not raw:
        return None
    s = strip_links(strip_refs(raw))
    vals = re.findall(r"([\d,]+(?:\.\d+)?)\s*cm", s)
    if not vals:
        return None
    return float(vals[-1].replace(",", ""))


def first_segment(raw):
    """First ;- or <br>-separated segment, links stripped."""
    if not raw:
        return None
    s = strip_refs(raw)
    s = re.split(r"<br\s*/?>|;", s)[0]
    s = strip_links(s)
    s = re.sub(r"\(.*?\)", "", s).strip().strip(",").strip()
    return s or None


def parse_origin(raw):
    if not raw:
        return None
    s = strip_refs(raw)
    s = re.split(r"<br\s*/?>|;", s)[0]
    m = re.search(r"\[\[([^\]|]*)(?:\|[^\]]*)?\]\]", s)
    if m:
        return m.group(1).strip()
    return strip_links(s).split("(")[0].strip() or None


def parse_dftype(raw):
    if not raw:
        return []
    s = strip_refs(raw)
    s = re.sub(r"</?small>", "", s)
    types = []
    for seg in re.split(r"<br\s*/?>|;|,", s):
        t = strip_links(seg).strip()
        t = t.strip("()").strip()
        if t:
            types.append(t)
    return types


def clean_dfname(raw):
    if not raw:
        return None
    s = strip_links(strip_refs(raw))
    s = re.sub(r"</?small>", "", s)
    s = re.sub(r"\((?:VIZ|Viz)[^)]*\)", "", s)
    parts = [p.strip() for p in re.split(r"<br\s*/?>|;", s) if p.strip()]
    if not parts:
        return None
    main = parts[0]
    extras = [p.strip("()").strip() for p in parts[1:]]
    if extras:
        return f"{main} ({'; '.join(extras)})"
    return main


ARC_RANGES = [
    ("Romance Dawn", 1, 7),
    ("Orange Town", 8, 21),
    ("Syrup Village", 22, 41),
    ("Baratie", 42, 68),
    ("Arlong Park", 69, 95),
    ("Loguetown", 96, 100),
    ("Reverse Mountain", 101, 105),
    ("Whisky Peak", 106, 114),
    ("Little Garden", 115, 129),
    ("Drum Island", 130, 154),
    ("Alabasta", 155, 217),
    ("Jaya", 218, 236),
    ("Skypiea", 237, 302),
    ("Long Ring Long Land", 303, 321),
    ("Water 7", 322, 374),
    ("Enies Lobby", 375, 430),
    ("Post-Enies Lobby", 431, 441),
    ("Thriller Bark", 442, 489),
    ("Sabaody Archipelago", 490, 513),
    ("Amazon Lily", 514, 524),
    ("Impel Down", 525, 549),
    ("Marineford", 550, 580),
    ("Post-War", 581, 597),
    ("Return to Sabaody", 598, 602),
    ("Fish-Man Island", 603, 653),
    ("Punk Hazard", 654, 699),
    ("Dressrosa", 700, 801),
    ("Zou", 802, 824),
    ("Whole Cake Island", 825, 902),
    ("Levely", 903, 908),
    ("Wano Country", 909, 1057),
    ("Egghead", 1058, 1125),
    ("Elbaf", 1126, 9999),
]


def arc_for_chapter(ch):
    if ch is None:
        return None
    for name, lo, hi in ARC_RANGES:
        if lo <= ch <= hi:
            return name
    return None


def main():
    roster = json.loads((HERE / "roster.json").read_text())
    names = roster["original"] + roster["additions"]
    print(f"{len(names)} characters")

    print("fetching haki categories...")
    haki_cats = {
        "Armament": set(fetch_category_members("Armament Haki Users")),
        "Observation": set(fetch_category_members("Observation Haki Users")),
        "Conqueror": set(fetch_category_members("Supreme King Haki Users")),
    }
    for k, v in haki_cats.items():
        print(f"  {k}: {len(v)} users")

    print("fetching page content...")
    content = fetch_content(names)

    # pages without a Char Box keep it inside their "Tabs Top" template
    need_sub = [rt for (rt, txt) in content.values()
                if txt is not None and extract_charbox(txt) is None]
    print(f"{len(need_sub)} pages need Tabs Top template")
    sub_content = {}
    if need_sub:
        subs = fetch_content([f"Template:{t} Tabs Top" for t in need_sub])
        for req, (rt, txt) in subs.items():
            base = req[len("Template:"):-len(" Tabs Top")]
            sub_content[base] = txt

    resolved_titles = [rt for (rt, txt) in content.values() if txt is not None]
    print("fetching categories...")
    cats = fetch_categories(resolved_titles)
    print("fetching images...")
    images = fetch_images(resolved_titles)

    records = []
    report = {"missing_page": [], "no_charbox": [], "issues": {}}
    for req_name in names:
        rt, txt = content[req_name]
        if txt is None:
            report["missing_page"].append(req_name)
            continue
        box = extract_charbox(txt) or extract_charbox(sub_content.get(rt))
        if box is None:
            report["no_charbox"].append(req_name)
            box = {}

        page_cats = cats.get(rt, [])
        gender = None
        if "Male Characters" in page_cats:
            gender = "Male"
        if "Female Characters" in page_cats:
            gender = "Female" if gender is None else gender
        haki = [h for h, members in haki_cats.items() if rt in members]

        chapter, episode = parse_first(box.get("first"))
        bounty = parse_bounty(box.get("bounty"))
        height_cm = parse_height(box.get("height"))
        affiliation = first_segment(box.get("affiliation"))
        origin = parse_origin(box.get("origin"))
        dftypes = parse_dftype(box.get("dftype"))
        dfname = clean_dfname(box.get("dfename") or box.get("dfname"))

        rec = {
            "name": rt,
            "requested": req_name,
            "gender": gender,
            "affiliation": affiliation,
            "dfTypes": dftypes,
            "dfName": dfname,
            "haki": haki,
            "bounty": bounty,
            "heightCm": height_cm,
            "origin": origin,
            "firstChapter": chapter,
            "firstEpisode": episode,
            "firstArc": arc_for_chapter(chapter),
            "image": images.get(rt),
        }
        issues = [k for k in ("gender", "affiliation", "origin", "firstChapter", "heightCm")
                  if rec[k] in (None, [])]
        if issues:
            report["issues"][req_name] = issues
        records.append(rec)

    (OUT / "characters.draft.json").write_text(
        json.dumps(records, indent=1, ensure_ascii=False))
    (OUT / "report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False))
    (OUT / "images.json").write_text(json.dumps(
        {r["name"]: r["image"] for r in records}, indent=1, ensure_ascii=False))
    print(f"wrote {len(records)} records")
    print(f"missing pages: {report['missing_page']}")
    print(f"no charbox: {report['no_charbox']}")
    print(f"records with issues: {len(report['issues'])}")


if __name__ == "__main__":
    main()
