#!/usr/bin/env python3
"""Download pre-timeskip portraits into public/portraits/<slug>-pre.png.

The spoiler limit rewinds a character's card to how they were known at a point
in the story, and for anyone introduced before the two-year timeskip that
includes how they looked. The wiki files them under a naming convention —
"<Name> Anime Pre Timeskip Infobox.png" — so this is a straight lookup rather
than a judgement call. Roughly a third of pre-timeskip characters have one;
the rest never changed enough for the wiki to bother, and keep their portrait.

Outputs:
  public/portraits/<slug>-pre.(png|jpg)
  tools/out/portraits_pre.json   - {character: filename}
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
DEST = HERE.parent / "public" / "portraits"
OUT = HERE / "out"
DATA = HERE.parent / "src" / "data"
API = "https://onepiece.fandom.com/api.php"
UA = {"User-Agent": "OnePieceDleFanProject/1.0 (personal, low-volume)"}

TIMESKIP_CHAPTER = 598
PRE_RE = re.compile(r"pre[- ]timeskip.*infobox|infobox.*pre[- ]timeskip", re.I)


def slugify(name):
    return re.sub(r"[^A-Za-z0-9]+", "-", name).strip("-").lower()


def api(params):
    qs = urllib.parse.urlencode({**params, "format": "json"})
    for attempt in range(3):
        try:
            req = urllib.request.Request(f"{API}?{qs}", headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except Exception as e:
            print(f"  retry {attempt+1}: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"failed: {params}")


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def thumb_url(url, width=280):
    if "/revision/latest" in url:
        return url.replace("/revision/latest", f"/revision/latest/scale-to-width-down/{width}")
    return url


def main():
    chars = json.loads((DATA / "characters.json").read_text())
    # Anyone who debuts after the timeskip only ever had the one look.
    candidates = [c for c in chars
                  if c["firstChapter"] and c["firstChapter"] <= TIMESKIP_CHAPTER]
    by_page = {c["wikiPage"]: c for c in candidates}
    print(f"{len(candidates)} characters debut before chapter {TIMESKIP_CHAPTER}")

    wanted = {}
    for batch in chunks(sorted(by_page), 20):
        d = api({"action": "query", "titles": "|".join(batch),
                 "prop": "images", "imlimit": "max", "redirects": 1})
        for p in d["query"]["pages"].values():
            files = [im["title"] for im in p.get("images", []) if PRE_RE.search(im["title"])]
            if not files:
                continue
            # Anime stills match the portraits already in use; manga panels are
            # a fallback so the two don't sit side by side in different styles.
            files.sort(key=lambda t: (0 if "Anime" in t else 1, len(t)))
            wanted[p["title"]] = files[0]
    print(f"{len(wanted)} have pre-timeskip infobox art")

    urls = {}
    for batch in chunks(sorted(set(wanted.values())), 20):
        d = api({"action": "query", "titles": "|".join(batch),
                 "prop": "imageinfo", "iiprop": "url"})
        for p in d["query"]["pages"].values():
            info = p.get("imageinfo")
            if info:
                urls[p["title"]] = info[0]["url"]

    # The API resolves redirects, so map the resolved title back to our roster.
    resolved = {c["wikiPage"]: c for c in candidates}
    mapping, failed = {}, []
    for page_title, file_title in sorted(wanted.items()):
        c = resolved.get(page_title) or by_page.get(page_title)
        if not c:
            continue
        url = urls.get(file_title)
        if not url:
            failed.append(c["name"])
            continue
        ext = ".png" if ".png" in url.lower() else ".jpg"
        out = DEST / f"{slugify(c['name'])}-pre{ext}"
        mapping[c["name"]] = out.name
        if out.exists() and out.stat().st_size > 500:
            continue
        try:
            req = urllib.request.Request(thumb_url(url), headers=UA)
            with urllib.request.urlopen(req, timeout=30) as resp:
                out.write_bytes(resp.read())
            time.sleep(0.2)
        except Exception as e:
            print(f"FAIL {c['name']}: {e}")
            failed.append(c["name"])
            mapping.pop(c["name"], None)

    (OUT / "portraits_pre.json").write_text(
        json.dumps(mapping, indent=1, ensure_ascii=False))
    print(f"{len(mapping)} pre-timeskip portraits, {len(failed)} failed: {failed}")


if __name__ == "__main__":
    main()
