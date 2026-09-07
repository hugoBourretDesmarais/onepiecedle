#!/usr/bin/env python3
"""Download character portraits (280px-wide thumbnails) into public/portraits/."""
import json
import re
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
DEST = HERE.parent / "public" / "portraits"
DEST.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "OnePieceDleFanProject/1.0 (personal, low-volume)"}


def slugify(name):
    return re.sub(r"[^A-Za-z0-9]+", "-", name).strip("-").lower()


def thumb_url(url, width=280):
    # .../X.png/revision/latest?cb=... -> .../X.png/revision/latest/scale-to-width-down/280?cb=...
    if "/revision/latest" in url:
        return url.replace("/revision/latest", f"/revision/latest/scale-to-width-down/{width}")
    return url


def main():
    recs = json.loads((HERE / "out" / "characters.draft.json").read_text())
    mapping = {}
    failed = []
    for r in recs:
        name = r["requested"]
        url = r.get("image")
        slug = slugify(name)
        if not url:
            failed.append(name)
            continue
        ext = ".png" if ".png" in url.lower() else ".jpg"
        out = DEST / f"{slug}{ext}"
        mapping[name] = out.name
        if out.exists() and out.stat().st_size > 500:
            continue
        req = urllib.request.Request(thumb_url(url), headers=UA)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
            out.write_bytes(data)
            time.sleep(0.25)
        except Exception as e:
            print(f"FAIL {name}: {e}")
            failed.append(name)
    (HERE / "out" / "portraits.json").write_text(json.dumps(mapping, indent=1, ensure_ascii=False))
    print(f"{len(mapping)} portraits, {len(failed)} failed: {failed}")


if __name__ == "__main__":
    main()
