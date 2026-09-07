#!/usr/bin/env python3
"""Fetch the backdrop artwork from the One Piece wiki and encode it for the web.

Each image is cropped to a wide ratio, resized, and written as WebP (with a JPEG
fallback for older Safari). Sources are hand-picked landscape pieces — colour
spreads and anime stills — rather than whatever a page happens to expose.
"""
import json
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
DEST = HERE.parent / "public" / "backgrounds"
DEST.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "OnePieceDleFanProject/1.0 (personal, low-volume)"}

# slug -> (wiki page, human label shown as a credit)
SOURCES = {
    "wano": ("Wano Country Saga", "Wano Country"),
    "new-age": ("Dressrosa Saga", "New Age"),
    "loguetown": ("Loguetown Arc", "Loguetown"),
    "marineford": ("Marineford Arc", "Marineford"),
    "elbaf": ("Elbaph", "Elbaf"),
    "alabasta": ("Arabasta Arc", "Alabasta"),
}

TARGET_W = 1920
TARGET_RATIO = 16 / 9


def api(params):
    q = urllib.parse.urlencode({**params, "format": "json"})
    req = urllib.request.Request("https://onepiece.fandom.com/api.php?" + q, headers=UA)
    return json.load(urllib.request.urlopen(req, timeout=60))


def main():
    from PIL import Image
    import io

    titles = [v[0] for v in SOURCES.values()]
    d = api({"action": "query", "titles": "|".join(titles),
             "prop": "pageimages", "piprop": "original", "redirects": 1})
    by_title = {}
    for _, p in d["query"]["pages"].items():
        if p.get("original"):
            by_title[p["title"]] = p["original"]["source"]
    # follow redirects back to the slug we asked for
    for r in d["query"].get("redirects", []) + d["query"].get("normalized", []):
        if r["to"] in by_title:
            by_title[r["from"]] = by_title[r["to"]]

    manifest = []
    for slug, (title, label) in SOURCES.items():
        url = by_title.get(title)
        if not url:
            print(f"SKIP {slug}: no image for {title}")
            continue
        raw = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120).read()
        im = Image.open(io.BytesIO(raw)).convert("RGB")

        # centre-crop to 16:9 so the focal point survives on wide screens
        w, h = im.size
        if w / h > TARGET_RATIO:
            new_w = int(h * TARGET_RATIO)
            im = im.crop(((w - new_w) // 2, 0, (w - new_w) // 2 + new_w, h))
        else:
            new_h = int(w / TARGET_RATIO)
            top = int((h - new_h) * 0.32)  # bias upward; faces sit high in these pieces
            im = im.crop((0, top, w, top + new_h))
        im = im.resize((TARGET_W, int(TARGET_W / TARGET_RATIO)), Image.LANCZOS)

        jpg = DEST / f"{slug}.jpg"
        im.save(jpg, "JPEG", quality=82, optimize=True, progressive=True)
        webp = DEST / f"{slug}.webp"
        subprocess.run(["cwebp", "-q", "76", "-quiet", str(jpg), "-o", str(webp)], check=True)

        manifest.append({"slug": slug, "label": label, "page": title})
        print(f"{slug:12} jpg {jpg.stat().st_size // 1024:4d}KB   webp {webp.stat().st_size // 1024:4d}KB")

    (HERE.parent / "src" / "data" / "backgrounds.json").write_text(
        json.dumps(manifest, indent=1, ensure_ascii=False))
    print(f"\n{len(manifest)} backgrounds -> {DEST}")


if __name__ == "__main__":
    main()
