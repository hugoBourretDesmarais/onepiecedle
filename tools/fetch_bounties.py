#!/usr/bin/env python3
"""Fetch each character's full bounty history from the One Piece wiki.

The Char Box `bounty` field lists every bounty newest-first, each one carrying a
{{Qref}} that names the chapter the value was revealed in. That chapter is what a
spoiler limit needs: it is when the *reader* learned the number, not when the
in-story raise happened.

Outputs:
  tools/out/bounties.json        - {character: [{amount, chapter, current}]}
  tools/out/bounties_report.json - entries whose chapter could not be resolved
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
CACHE = HERE / "cache" / "bounty"
OUT = HERE / "out"
CACHE.mkdir(parents=True, exist_ok=True)
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
            time.sleep(0.3)
            return data
        except Exception as e:
            print(f"  retry {attempt+1} for {cache_key}: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"failed: {cache_key}")


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def fetch_content(titles):
    """{requested_title: (resolved_title, wikitext or None)}"""
    result = {}
    for batch in chunks(titles, 20):
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
        by_title = {}
        for pid, p in q["pages"].items():
            if int(pid) < 0:
                by_title[p.get("title", "")] = None
                continue
            revs = p.get("revisions")
            by_title[p["title"]] = revs[0]["slots"]["main"]["*"] if revs else None
        for t in batch:
            r, seen = t, set()
            while r in redir and r not in seen:
                seen.add(r)
                r = redir[r]
            result[t] = (r, by_title.get(r))
    return result


# ---------- wikitext helpers ----------

def find_template(text, name):
    """Return the full source of the first {{name ...}} block, braces balanced."""
    if not text:
        return None
    m = re.search(r"\{\{\s*" + re.escape(name), text)
    if not m:
        return None
    i, depth, j = m.start(), 0, m.start()
    while j < len(text):
        if text[j:j + 2] == "{{":
            depth += 1
            j += 2
        elif text[j:j + 2] == "}}":
            depth -= 1
            j += 2
            if depth == 0:
                return text[i:j]
        else:
            j += 1
    return None


def split_fields(box):
    """Top-level |key=value pairs of a template block."""
    fields, depth, cur, parts, k = {}, 0, [], [], 0
    while k < len(box):
        c2 = box[k:k + 2]
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


def iter_templates(text, recurse=True):
    """Yield (name, {params}, source) for every balanced {{...}}, outermost first.

    Nested templates are yielded too: a Qref that dates a bounty usually sits
    several levels down inside {{#ifeq:}} -> {{Char Box}} -> the field.
    """
    k = 0
    while k < len(text):
        if text[k:k + 2] == "{{":
            depth, j = 0, k
            while j < len(text):
                if text[j:j + 2] == "{{":
                    depth += 1
                    j += 2
                elif text[j:j + 2] == "}}":
                    depth -= 1
                    j += 2
                    if depth == 0:
                        break
                else:
                    j += 1
            block = text[k:j]
            inner = block[2:-2]
            name = inner.split("|")[0].split("=")[0].strip()
            params = {}
            for part in split_raw_params(inner)[1:]:
                if "=" in part:
                    a, _, b = part.partition("=")
                    params[a.strip().lower()] = b.strip()
            yield name, params, block
            if recurse:
                yield from iter_templates(inner, recurse)
            k = j
        else:
            k += 1


def split_raw_params(inner):
    """Split a template body on top-level pipes."""
    out, depth, cur, k = [], 0, [], 0
    while k < len(inner):
        c2 = inner[k:k + 2]
        if c2 in ("{{", "[["):
            depth += 1
            cur.append(c2)
            k += 2
        elif c2 in ("}}", "]]"):
            depth -= 1
            cur.append(c2)
            k += 2
        elif inner[k] == "|" and depth == 0:
            out.append("".join(cur))
            cur = []
            k += 1
        else:
            cur.append(inner[k])
            k += 1
    out.append("".join(cur))
    return out


# cover=N is a chapter's cover page, so it dates the reveal just as chap= does.
CHAP_KEYS = ("chap", "chapter", "cover")
# Everything the wiki cites that isn't the manga itself. A bounty known only
# from one of these was never on the page, so it needs a release date instead.
SOURCE_KEYS = ("data", "special", "novel", "magazine", "movie", "other", "sbs",
               "vol", "ep", "game", "databook")


def qref_chapter(params):
    """First chapter number a {{Qref}} points at, if it states one inline."""
    for key in CHAP_KEYS:
        v = params.get(key)
        if v:
            m = re.search(r"(\d+)", v)
            if m:
                return int(m.group(1))
    return None


def qref_source(params):
    for key in SOURCE_KEYS:
        v = params.get(key)
        if v:
            return f"{key}={re.sub(r'\\s+', ' ', v).strip()[:40]}"
    return None


def harvest_ref_names(text, into):
    """Record name= -> {chapters, sources} for every Qref that defines them."""
    if not text:
        return
    for name, params, _ in iter_templates(text):
        if name.lower() not in ("qref", "ref"):
            continue
        ref_name = params.get("name")
        if not ref_name:
            continue
        slot = into.setdefault(ref_name.strip(), {"chapters": set(), "sources": set()})
        chap = qref_chapter(params)
        if chap:
            slot["chapters"].add(chap)
        src = qref_source(params)
        if src:
            slot["sources"].add(src)


# ---------- bounty field parsing ----------

AMOUNT_RE = re.compile(r"([\d][\d,\.]{2,})")
UNKNOWN_RE = re.compile(r"\b(unknown|undisclosed|至\?|\?\?\?)\b", re.I)


def lookup_ref(ref_name, local, glob, notes, debug_name):
    """-> (chapter, source) for a {{Qref|name=...}} back-reference.

    Named refs are page-scoped, so the character's own page wins; short names
    like "infobox" or "vivre card" mean different things on different pages and
    would otherwise pick up a stranger's chapter.
    """
    ref_name = ref_name.strip()
    # A ref can only be cited on the page that defines it, so if the name occurs
    # here at all, what this page says about it is the whole answer. Falling
    # through to the global map on a bare name like "bounty" or "infobox" is how
    # you end up dating Bepo's bounty from Boa Hancock's reference.
    if ref_name in local:
        slot = local[ref_name]
        if slot["chapters"]:
            return min(slot["chapters"]), None
        if slot["sources"]:
            return None, sorted(slot["sources"])[0]
        notes.append(f"{debug_name}: ref {ref_name!r} is defined here without a chapter")
        return None, None
    m = re.fullmatch(r"c\.?\s*(\d{1,4})(?:[ps]\d+)?", ref_name, re.I)
    if m:
        notes.append(f"{debug_name}: dated ref {ref_name!r} from its own name")
        return int(m.group(1)), None
    slot = glob.get(ref_name)
    if slot and slot["chapters"]:
        notes.append(f"{debug_name}: ref {ref_name!r} resolved from another page")
        return min(slot["chapters"]), None
    if slot and slot["sources"]:
        return None, sorted(slot["sources"])[0]
    notes.append(f"{debug_name}: unresolved ref name {ref_name!r}")
    return None, None


def parse_bounty_field(raw, local_refs, glob_refs, debug_name=""):
    """-> ([{amount, chapter, source, struck}], [unresolved notes])"""
    if not raw:
        return [], []
    raw = re.sub(r"<!--.*?-->", "", raw, flags=re.S)
    # One bounty per line: the wiki separates them with <br>, occasionally ';'
    lines = re.split(r"<br\s*/?>|\n(?=\s*\{\{\s*[Bb]\}\})", raw)
    entries, notes = [], []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        struck = "<s>" in line or "<strike>" in line
        # strip the ฿ template so it can't be read as a number
        body = re.sub(r"\{\{\s*[Bb]\s*\}\}", " ", line)
        chapters, sources = [], []
        for name, params, block in iter_templates(body):
            if name.lower() not in ("qref", "ref", "web ref", "vol ref"):
                continue
            c = qref_chapter(params)
            s = qref_source(params) if c is None else None
            if c is None and s is None and params.get("name"):
                c, s = lookup_ref(params["name"], local_refs, glob_refs, notes, debug_name)
            if c:
                chapters.append(c)
            elif s:
                sources.append(s)
        # remove templates and tags before reading the amount
        plain = body
        for _, _, block in list(iter_templates(body)):
            plain = plain.replace(block, " ")
        plain = re.sub(r"<[^>]+>", " ", plain)
        plain = re.sub(r"\[\[([^\]|]*\|)?([^\]]*)\]\]", r"\2", plain)
        m = AMOUNT_RE.search(plain)
        if not m:
            if UNKNOWN_RE.search(plain):
                notes.append(f"{debug_name}: unknown amount in {line[:60]!r}")
            continue
        amount = int(m.group(1).replace(",", "").replace(".", ""))
        entries.append({
            "amount": amount,
            "chapter": min(chapters) if chapters else None,
            "source": None if chapters else (sources[0] if sources else None),
            "struck": struck,
            "raw": re.sub(r"\s+", " ", line).strip(),
        })
    return entries, notes


def main():
    data = json.loads((HERE.parent / "src" / "data" / "characters.json").read_text())
    pages = {c["name"]: c["wikiPage"] for c in data}
    titles = sorted(set(pages.values()))
    print(f"{len(titles)} wiki pages")

    print("fetching articles...")
    content = fetch_content(titles)
    need_sub = [rt for (rt, txt) in content.values()
                if txt is not None and find_template(txt, "Char Box") is None]
    print(f"{len(need_sub)} need their Tabs Top template")
    sub = {}
    if need_sub:
        got = fetch_content([f"Template:{t} Tabs Top" for t in need_sub])
        for req, (rt, txt) in got.items():
            sub[req[len("Template:"):-len(" Tabs Top")]] = txt

    # Named refs are defined once per page and reused; collect them per page so
    # a bounty line that only says {{Qref|name=...}} can still be dated.
    local_refs, glob_refs = {}, {}
    for rt, txt in content.values():
        into = local_refs.setdefault(rt, {})
        harvest_ref_names(txt, into)
        harvest_ref_names(sub.get(rt), into)
        for k, v in into.items():
            slot = glob_refs.setdefault(k, {"chapters": set(), "sources": set()})
            slot["chapters"] |= v["chapters"]
            slot["sources"] |= v["sources"]
    print(f"{len(glob_refs)} distinct named refs")

    result, notes, missing = {}, [], []
    for name, page in sorted(pages.items()):
        rt, txt = content[page]
        box_src = find_template(txt, "Char Box") or find_template(sub.get(rt), "Char Box")
        if not box_src:
            missing.append(name)
            continue
        raw = split_fields(box_src).get("bounty")
        entries, n = parse_bounty_field(raw, local_refs.get(rt, {}), glob_refs, name)
        notes += n
        if entries:
            result[name] = entries

    (OUT / "bounties.json").write_text(json.dumps(result, indent=1, ensure_ascii=False))
    unresolved = {k: [e for e in v if e["chapter"] is None] for k, v in result.items()}
    unresolved = {k: v for k, v in unresolved.items() if v}
    (OUT / "bounties_report.json").write_text(json.dumps({
        "no_charbox": missing,
        "entries_without_chapter": unresolved,
        "notes": sorted(set(notes)),
    }, indent=1, ensure_ascii=False))
    print(f"{len(result)} characters with a bounty, "
          f"{sum(len(v) for v in result.values())} entries")
    print(f"{sum(len(v) for v in unresolved.values())} entries missing a chapter "
          f"across {len(unresolved)} characters")
    print(f"no charbox: {missing}")


if __name__ == "__main__":
    main()
