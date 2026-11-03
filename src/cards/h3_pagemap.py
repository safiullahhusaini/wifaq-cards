"""Hidaya 3: positions in the Bushra 8-vol edition, vol 5 (printed pages, no estimation model).

A position is a float: printed page + fraction of that page's matn letters before the point (0 = top, 1 = bottom).
Pages shown on the site ARE these printed pages; the fraction is used only to order cards and headings.

The OCR (book text) is NOT kept in the public repo. Where it is on disk (env V5OCR, <repo>/.cache/v5ocr, or
/home/claude/wifaq/v5ocr) it is used, and the derived numbers (where each card's opening words and each heading
were found) are saved to h3_pagemap_cache.json, so the build gives the same pages without the OCR (GitHub workflows).
OCR layout: files pAAAA-BBBB.md by PDF page plus pages.csv (pdf_page, file, ...). pages.csv names the file to use for
each PDF page (some pages were re-done in single-page files); pages are numbered by position in that file, ignoring the
"PDF n" labels inside it. Printed page = PDF page - 1.
"""
import atexit, csv, glob, json, os, re
from rapidfuzz import fuzz

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(HERE, "h3_pagemap_cache.json")
FIRST_PAGE, LAST_PAGE = 253, 541        # كتاب الصرف … end of vol 5's matn (PDF 542); raise/lower with h3_toc


def _ocr_dir():
    for d in (os.environ.get("V5OCR"), os.path.join(HERE, "..", "..", ".cache", "v5ocr"), "/home/claude/wifaq/v5ocr"):
        if d and os.path.exists(os.path.join(d, "pages.csv")) and glob.glob(os.path.join(d, "p*.md")):
            return d
    return None


OCR = None if os.environ.get("V5OCR") == "none" else _ocr_dir()   # V5OCR=none: test the cache-only build
try:
    with open(CACHE_FILE, encoding="utf-8") as _f:
        CACHE = json.load(_f)
except Exception:
    CACHE = {"hits": {}, "heads": {}}
_dirty = [False]


def _save():
    if _dirty[0]:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(CACHE, f, ensure_ascii=False, indent=0, sort_keys=True)


atexit.register(_save)
TASHKEEL = re.compile("[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed\u0640]")


def norm(s):
    s = TASHKEEL.sub("", s)
    s = re.sub("[أإآٱ]", "ا", s).replace("ى", "ي").replace("ک", "ك").replace("ی", "ي").replace("ة", "ه").replace("ؤ", "و").replace("ئ", "ي")
    return re.sub("[^\u0621-\u064a]", "", s)


def _matn(section):
    m = re.search(r"\[متن\]\n(.*?)(?=\n\[بین السطور\]|\n\[حاشیہ\]|\Z)", section, re.S)
    return [l for l in (m.group(1) if m else "").split("\n") if l.strip() and l.strip() != "—"]


def load_pages():
    pages = {}
    if not OCR:
        return pages
    secs = {}
    with open(os.path.join(OCR, "pages.csv"), encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            pdf, fn = int(r["pdf_page"]), r["file"].strip()
            if not (FIRST_PAGE <= pdf - 1 <= LAST_PAGE) or not fn:
                continue
            if fn not in secs:
                txt = open(os.path.join(OCR, fn), encoding="utf-8").read()
                secs[fn] = re.split(r"^=== PDF [^\n]*\n", txt, flags=re.M)[1:]
            k = pdf - int(re.match(r"p(\d+)", fn).group(1))
            if 0 <= k < len(secs[fn]):
                pages[pdf - 1] = _matn(secs[fn][k])
    return pages


PAGES = load_pages()
_RUN = set()


def set_running(titles):
    """Running headers (kitab/bab names printed atop pages): dropped from a page's matn before measuring."""
    _RUN.update(norm(t) for t in titles)


def page_body(p):
    ls = PAGES.get(p, [])
    if ls and (norm(ls[0]) in _RUN or any(fuzz.ratio(norm(ls[0]), r) >= 90 for r in _RUN)):
        return ls[1:], ls[0]
    return ls, None


_TEXT = {}


def text(p):
    if p not in _TEXT:
        _TEXT[p] = norm(" ".join(page_body(p)[0]))
    return _TEXT[p]


def pos_of(page, start=None, frac=None, search=1):
    """Position of a passage: its opening words searched on page±search, else page + frac. -> (pos, hit or None);
    hit = (score, page, fraction)."""
    page = int(page)
    if start:
        q = norm(start)[:60]
        key = f"{page}|{search}|{q}"
        best = None
        if OCR and len(q) >= 8:
            for p in range(page - search, page + search + 1):
                t = text(p)
                if not t:
                    continue
                al = fuzz.partial_ratio_alignment(q, t)
                if al.score >= 80 and (best is None or al.score > best[0] + 2 or (abs(al.score - best[0]) <= 2 and p == page)):
                    best = (round(al.score, 1), p, round(al.dest_start / len(t), 4))
            val = list(best) if best else None
            if CACHE["hits"].get(key, "missing") != val:
                CACHE["hits"][key] = val; _dirty[0] = True
        elif CACHE["hits"].get(key):
            best = tuple(CACHE["hits"][key])
        if best:
            return best[1] + best[2], best
    return page + (frac or 0.0), None


def heading_pos(page, title, frac=None):
    """Position of a heading on its page: the matn line that is the heading; else a running header with that title
    (heading at the top of the page); else the given fraction."""
    key = f"{page}|{title}|{frac}"
    if not PAGES.get(page):
        if key in CACHE["heads"]:
            return page + CACHE["heads"][key]
        if frac is None:
            raise LookupError(f"heading {title!r} on v5 p.{page}: no OCR and no cache")
        return page + frac
    body, head = page_body(page)
    q = norm(title)
    total = len(text(page)) or 1
    acc, found = 0, None
    for l in body:
        nl = norm(l)
        if (nl == q or (len(q) > 6 and fuzz.partial_ratio(q, nl) >= 88)) and len(nl) < len(q) + 25:
            found = round(acc / total, 4)
            break
        acc += len(nl)
    if found is None:
        if head is not None and fuzz.partial_ratio(q, norm(head)) >= 88 and frac is None:
            found = 0.0
        elif frac is not None:
            found = frac
        else:
            raise LookupError(f"heading {title!r} not found on v5 p.{page}")
    if CACHE["heads"].get(key) != found:
        CACHE["heads"][key] = found; _dirty[0] = True
    return page + found
