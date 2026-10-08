"""Map positions in the 8-vol Bushra edition (vol 7) to the colleagues' edition (continuous pages).

How: the matn of vol 7 is measured in letters (OCR in /home/claude/wifaq/v7ocr). The colleagues' contents page
gives the page on which each kitab/bab/fasl starts; two mid-page anchors (start of pp. 1610 and 1611) come from
photos of the colleagues' book. Each heading sits somewhere on its page (fraction unknown), so the fractions are
fitted so that letters-per-page is as even as possible; positions in between are interpolated by letters.
Result: estimated colleague page (float) for any vol-7 text position. Expect ±0.3 page; edges can be off by one.

The OCR (book text) is NOT kept in the public repo. Where it is on disk (env V7OCR, <repo>/.cache/v7ocr, or
/home/claude/wifaq/v7ocr) it is used and the derived numbers (letters per page, where each card's opening words
were found) are saved to h4_pagemap_cache.json. Without the OCR, the cache gives the same pages as before;
pages missing from the OCR on disk fall back to the cache one by one, so only new pages need downloading.
Download the OCR from Drive folder 15KT9EQxSPcCWGKwCvJ73ElIVCL8rSl2U (file pAAAA-BBBB.md = PDF pages AAAA–BBBB).
"""
import atexit, glob, json, os, re
import numpy as np
from rapidfuzz import fuzz

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(HERE, "h4_pagemap_cache.json")


def _ocr_dir():
    for d in (os.environ.get("V7OCR"), os.path.join(HERE, "..", "..", ".cache", "v7ocr"), "/home/claude/wifaq/v7ocr"):
        if d and glob.glob(os.path.join(d, "p*.md")):
            return d
    return None


OCR = _ocr_dir()
try:
    with open(CACHE_FILE, encoding="utf-8") as _f:
        CACHE = json.load(_f)
except Exception:
    CACHE = {"lens": {}, "hits": {}, "heads": {}}
_dirty = [False]


def _save():
    if _dirty[0]:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(CACHE, f, ensure_ascii=False, indent=0, sort_keys=True)


atexit.register(_save)
TASHKEEL = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۭـ]")


def norm(s):
    s = TASHKEEL.sub("", s)
    s = re.sub("[أإآٱ]", "ا", s).replace("ى", "ي").replace("ک", "ك").replace("ی", "ي").replace("ة", "ه").replace("ؤ", "و").replace("ئ", "ي")
    return re.sub(r"[^ء-ي]", "", s)


RUNNING = {norm(x) for x in ["كتاب الذبائح", "كتاب الأضحية", "كتاب القسمة", "باب طلب الشفعة والخصومة فيها", "كتاب المزارعة",
                             "باب ما تجب فيه الشفعة وما لا تجب", "كتاب الشفعة", "باب دعوى الغلط في القسمة والاستحقاق فيها",
                             "باب ما تبطل به الشفعة", "الهداية", "كتاب المساقاة", "كتاب الكراهية"]}


def load_pages():
    pages = {}
    if not OCR:
        return pages
    for f in sorted(glob.glob(os.path.join(OCR, "p*.md"))):
        a, b = map(int, re.match(r"p(\d+)-(\d+)", os.path.basename(f)).groups())
        txt = open(f, encoding="utf-8").read()
        secs = re.split(r"^=== PDF [^\n]*===\n", txt, flags=re.M)[1:]
        if len(secs) != b - a + 1:
            raise ValueError(f"{f}: {len(secs)} sections for PDF {a}-{b}")
        for k, body in enumerate(secs):
            m = re.search(r"\[متن\]\n(.*?)(?=\n\[بین السطور\]|\n\[حاشیہ\]|\Z)", body, re.S)
            lines = [l for l in (m.group(1) if m else "").split("\n") if l.strip()]
            pages[a + k - 1] = lines          # printed page = PDF page - 1
    return pages


PAGES = load_pages()


def page_body(p):
    """matn lines of printed page p without the running header."""
    ls = PAGES.get(p, [])
    if ls and norm(ls[0]) in RUNNING:
        return ls[1:], ls[0]
    return ls, None


TEXT, START, W = {}, {}, {}   # page -> normalized matn; cumulative weight at page start; page weight
LAST_PAGE = 184                # pages with neither OCR nor cached letters get the median weight
for p in range(0, LAST_PAGE + 1):
    body, _ = page_body(p)
    TEXT[p] = norm(" ".join(body))
LENS = {}
for p in range(0, LAST_PAGE + 1):
    if TEXT[p]:
        LENS[p] = len(TEXT[p])
        if CACHE["lens"].get(str(p)) != LENS[p]:
            CACHE["lens"][str(p)] = LENS[p]; _dirty[0] = True
    else:   # page not in the OCR on disk (or no OCR at all): letters counted earlier, else median below
        LENS[p] = int(CACHE["lens"].get(str(p), 0))
_lens = sorted(v for v in LENS.values() if v)
MEDIAN = _lens[len(_lens) // 2] if _lens else 480
_cum = 0.0
for p in range(0, LAST_PAGE + 1):
    n = LENS[p]
    # OCR sometimes drops lines (p.76, p.92) or pours footnotes into the matn (p.20–24, 80–86): use the median there
    W[p] = n if 150 <= n <= 800 else MEDIAN
    START[p] = _cum
    _cum += W[p]
TOTAL = _cum


def _pos(p, letter):
    n = LENS[p] or 1
    return START[p] + min(letter / n, 1.0) * W[p]


def offset_of(page, text=None, frac=None, search=1):
    """Weighted offset of a passage: located by its opening words near `page`, else page + fraction."""
    if text:
        q = norm(text)[:60]
        key = f"{page}|{search}|{q}"
        best = None
        if OCR and any(TEXT.get(p) for p in range(page - search, page + search + 1)):
            for p in range(page - search, page + search + 1):
                if p not in TEXT or len(q) < 8:
                    continue
                al = fuzz.partial_ratio_alignment(q, TEXT[p])
                if al.score >= 80 and (best is None or al.score > best[0] + 2 or (abs(al.score - best[0]) <= 2 and p == page)):
                    best = (al.score, p, al.dest_start)
            val = [best[1], best[2], best[0]] if best else None
            if CACHE["hits"].get(key, "missing") != val:
                CACHE["hits"][key] = val; _dirty[0] = True
        elif CACHE["hits"].get(key):
            hp, hl, hs = CACHE["hits"][key]
            best = (hs, hp, hl)
        if best:
            return _pos(best[1], best[2]), best
    if frac is None:
        frac = 0.0
    return START[page] + frac * W[page], None


def heading_offset(page, title, frac=None):
    """Offset of a heading on `page` (a running header => page start; missing in the OCR => fraction)."""
    key = f"{page}|{title}|{frac}"
    if not OCR or not PAGES.get(page):
        kind = CACHE["heads"].get(key)
        if kind is None and frac is None:
            raise LookupError(f"heading {title!r} on v7 p.{page}: no OCR and no cache")
        if kind and kind[0] == "start":
            return START[page]
        if kind and kind[0] == "pos":
            return _pos(page, kind[1])
        return START[page] + (frac or 0.0) * W[page]

    def note(v):
        if CACHE["heads"].get(key) != v:
            CACHE["heads"][key] = v; _dirty[0] = True

    body, head = page_body(page)
    q = norm(title)
    if head is not None and fuzz.partial_ratio(q, norm(head)) >= 90 and frac is None:
        note(["start"])
        return START[page]
    acc = 0
    for l in body:
        nl = norm(l)
        if (nl == q or (len(q) > 6 and fuzz.partial_ratio(q, nl) >= 88)) and len(nl) < len(q) + 25:
            note(["pos", acc])
            return _pos(page, acc)
        acc += len(nl)
    if frac is not None:
        note(["frac"])
        return START[page] + frac * W[page]
    raise LookupError(f"heading {title!r} not found on v7 p.{page}")


# (vol-7 page, heading as printed, colleagues' page from the contents[, fraction if the OCR lost the heading])
HEADINGS = [
    (3, "كتاب الشفعة", 1597), (14, "باب طلب الشفعة والخصومة فيها", 1602), (24, "فصل في الاختلاف", 1607),
    (28, "فصل فيما يؤخذ به المشفوع", 1609), (32, "فصل", 1612), (38, "باب ما تجب فيه الشفعة وما لا تجب", 1614),
    (48, "باب ما تبطل به الشفعة", 1619), (53, "فصل", 1622), (56, "مسائل متفرقة", 1623), (60, "كتاب القسمة", 1626),
    (70, "فصل فيما يقسم وما لا يقسم", 1630), (76, "فصل في كيفية القسمة", 1633, 0.1), (86, "باب دعوى الغلط في القسمة", 1638),
    (88, "فصل", 1639), (92, "فصل في المهايأة", 1641, 0.6), (99, "كتاب المزارعة", 1644),
    (117, "كتاب المساقاة", 1652, 0.0), (126, "كتاب الذبائح", 1657),
    (145, "فصل فيما يحل أكله وما لا يحل", 1666), (154, "كتاب الأضحية", 1672),
    (179, "كتاب الكراهية", 1684),
]
# exact: these words open the colleague page
EXACT = [(29, "أخذها بمثله", 1610), (31, "إنما يثبت بالبيع", 1611)]


def _fit():
    pts = []      # (offset, colleague page, fixed?)
    for h in HEADINGS:
        p, t, cp = h[:3]
        pts.append((heading_offset(p, t, h[3] if len(h) > 3 else None), cp, False, f"{t} v7 {p}"))
    for p, t, cp in EXACT:
        o, hit = offset_of(p, t)
        pts.append((o, cp, True, f"«{t}» v7 {p}"))
    pts.sort()
    # unknowns: f_i for free points (0..0.95), and k = pages per letter
    free = [i for i, x in enumerate(pts) if not x[2]]
    n = len(free) + 1
    rows, rhs = [], []
    for i in range(len(pts) - 1):
        (o1, c1, x1, _), (o2, c2, x2, _) = pts[i], pts[i + 1]
        r = np.zeros(n)
        # (c2 + f2) - (c1 + f1) = k * (o2 - o1)
        if not x2: r[free.index(i + 1)] += 1
        if not x1: r[free.index(i)] -= 1
        r[-1] = -(o2 - o1)
        rows.append(r); rhs.append(c1 - c2)
    from scipy.optimize import lsq_linear
    lb = [0.0] * len(free) + [0.0]; ub = [0.95] * len(free) + [1.0]
    sol = lsq_linear(np.array(rows), np.array(rhs), bounds=(lb, ub))
    fr = {i: sol.x[j] for j, i in enumerate(free)}
    anchors = [(o, c + fr.get(i, 0.0), lab) for i, (o, c, x, lab) in enumerate(pts)]
    return anchors, sol.x[-1]


ANCHORS, K = _fit()


def colleague(offset):
    """letter offset -> colleague page as a float (page + fraction)."""
    xs = [a[0] for a in ANCHORS]; ys = [a[1] for a in ANCHORS]
    if offset <= xs[0]:
        return ys[0] + (offset - xs[0]) * K
    if offset >= xs[-1]:
        return ys[-1] + (offset - xs[-1]) * K
    return float(np.interp(offset, xs, ys))


def v7_to_colleague(page, text=None, frac=None):
    o, hit = offset_of(page, text, frac)
    return colleague(o), hit


if __name__ == "__main__":
    print("letters per colleague page ≈", round(1 / K))
    prev = None
    for o, c, lab in ANCHORS:
        dens = "" if prev is None else f"  {round((o - prev[0]) / max(c - prev[1], 1e-6))} letters/page"
        print(f"{c:8.2f}  off {o:7.0f}  {lab}{dens}")
        prev = (o, c)
