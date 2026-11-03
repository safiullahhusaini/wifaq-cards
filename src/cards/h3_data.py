"""Hidaya 3: gather every lesson's cards (h3/h3_<key>.py), place them in Bushra vol 5 (printed pages), and split them
by kitab -> bab/fasl in book order. Page numbers are Bushra vol-5 printed pages (no colleagues' edition yet).

Lesson keys: this year's class = "<date>-1448" (e.g. 2026-07-11-1448), last year's = "<date>" (e.g. 2025-02-22),
plus an optional "-<suffix>" for a second recording on one date. Audio: <repo>/hidaya3/audio/<key>.ogg, or
<key>-1.ogg, <key>-2.ogg … (split; starts from audio/parts.json, else summed durations), as on hidaya4.

build() -> {"lessons": {...}, "kitabs": [ {slug, title, page_from, page_to, units, cards, gaps} ]}
"""
import glob, json, math, os, re, runpy

HERE = os.path.dirname(os.path.abspath(__file__))
import h3_pagemap as pm
import h3_toc

pm.set_running(h3_toc.RUNNING)
MONTHS = ["جنوری", "فروری", "مارچ", "اپریل", "مئی", "جون", "جولائی", "اگست", "ستمبر", "اکتوبر", "نومبر", "دسمبر"]
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
AUDIO_DIR = os.path.join(REPO, "hidaya3", "audio")
SOURCES = {"this-year": "اس سال کی کلاس", "last-year": "پچھلے سال کی کلاس"}
V5 = "٥"


def v5_label(a, b):
    return f"بشریٰ ج{V5} ص {a}" if a == b else f"بشریٰ ج{V5} ص {a}–{b}"


def label_of(key, source):
    y, m, d = map(int, key[:10].split("-"))
    s = f"{d} {MONTHS[m - 1]} {y}" if d != 1 else f"یکم {MONTHS[m - 1]} {y}"
    return f"{s}، {SOURCES[source]}"


def _dur(path):
    import subprocess
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                       capture_output=True, text=True)
    return float(r.stdout.strip() or 0)


def web_parts(key, all_keys):
    one = os.path.join(AUDIO_DIR, f"{key}.ogg")
    if os.path.exists(one):
        return [(f"{key}.ogg", 0.0, one)]
    pat = re.compile(re.escape(key) + r"-p?(\d{1,2})\.ogg$")    # parts are 1–2 digits, so 2025-07-11 never takes 2025-07-11-1448
    others = {f"{k}.ogg" for k in all_keys if k != key}
    parts = sorted((p for p in glob.glob(os.path.join(AUDIO_DIR, f"{key}-*.ogg"))
                    if pat.search(os.path.basename(p)) and os.path.basename(p) not in others),
                   key=lambda p: int(pat.search(os.path.basename(p)).group(1)))
    known = {}
    pj = os.path.join(AUDIO_DIR, "parts.json")
    if os.path.exists(pj):
        with open(pj, encoding="utf-8") as f:
            known = json.load(f)
    out, start = [], 0.0
    for p in parts:
        name = os.path.basename(p)
        st = float(known.get(name, start))
        out.append((name, round(st, 2), p))
        start = st + _dur(p)
    return out


# ---- headings in book order: (position, level, title, page)
HEADS = sorted(((pm.heading_pos(h[2], h[3], h[4] if len(h) > 4 else None), i, h[0], h[1], h[2])
                for i, h in enumerate(h3_toc.TOC)))
HEADS = [(pos, lv, t, p) for pos, _, lv, t, p in HEADS]


def unit_of(pos):
    """-> (kitab, bab, fasl, page of the unit's heading) for a position."""
    kitab = bab = fasl = None
    kp = bp = fp = None
    for o, level, title, p in HEADS:
        if o > pos + 1e-6:
            break
        if level == 1:
            kitab, bab, fasl, kp, bp, fp = title, None, None, p, None, None
        elif level == 2:
            bab, fasl, bp, fp = title, None, p, None
        else:
            fasl, fp = title, p
    return kitab, bab, fasl, (fp or bp or kp)


def pages_from(lo, hi, floor_page=None):
    a = math.floor(lo + 1e-6)
    b = max(a, math.floor(hi - 1e-6))
    if floor_page:
        a = max(a, floor_page); b = max(b, a)
    return list(range(a, b + 1))


def plabel(ps):
    return str(ps[0]) if len(ps) == 1 else f"{ps[0]}–{ps[-1]}"


def convert_tags(items):
    """K5(page) -> the site's book-page chip; the page is the Bushra page itself."""
    out = []
    for it in items or []:
        *head, ss = it
        out.append((*head, [{"t": "k", "v": str(s["v"])} if s.get("t") == "k5" else s for s in ss]))
    return out


def lesson_files():
    return sorted(glob.glob(os.path.join(HERE, "h3", "h3_20*.py")))


def lesson_cards():
    cards, gaps, notes, meta = [], [], [], {}
    for f in lesson_files():
        d = runpy.run_path(f)
        key = d["LESSON"]
        if os.path.basename(f) != f"h3_{key}.py":
            raise ValueError(f"{f}: LESSON = {key!r} must match the file name h3_<LESSON>.py")
        src = d.get("SOURCE", "this-year" if key.split("-")[3:4] == ["1448"] else "last-year")
        if src not in SOURCES:
            raise ValueError(f"{f}: SOURCE must be one of {list(SOURCES)}")
        meta[key] = {"source": src, "file": d.get("RECORDING", ""), "minutes": d.get("MINUTES")}
        for i, c in enumerate(d["CARDS"]):
            lo, hit = pm.pos_of(int(c["v5"]), c.get("start"), c.get("v5_frac") or 0.0)
            ve, vf = int(c.get("v5_end") or c["v5"]), c.get("v5_end_frac")
            hi = ve + (1.0 if vf is None else vf)
            if hi <= lo + 0.05:
                hi = lo + 0.25
            v5a = hit[1] if hit else int(c["v5"])
            card = dict(c)
            card.update(lesson=key, off=lo, end=hi, src=f"{os.path.basename(f)}#{i + 1}", found=bool(hit),
                        v5a=v5a, v5b=max(v5a, ve if (vf is None or vf > 0.02) else ve - 1))
            for k in ("tamheed", "masala", "dalil", "ikhtilaf", "faida", "lughat"):
                card[k] = convert_tags(c.get(k))
            cards.append(card)
        for rng, text in d.get("GAPS", []):
            if not rng.strip().startswith("v5"):
                continue
            plain = re.sub(r"\([^)]*\)", " ", re.sub(r"^\s*v5\s*", "", rng))
            nums = [int(x) for x in re.findall(r"(?<![\d.])\d{1,4}(?![\d.])", plain)]
            if nums:
                a, b = nums[0], nums[-1]
                gaps.append({"lesson": key, "off": a, "end": b + 1.0, "mid": (a + b + 1) / 2, "v5": (a, b), "text": text})
        notes += [(key, n) for n in d.get("NOTES", [])]
    return cards, gaps, notes, meta


def build():
    cards, gaps, notes, meta = lesson_cards()
    cards.sort(key=lambda c: c["off"])
    for n, c in enumerate(cards):
        kitab, bab, fasl, upage = unit_of(c["off"])
        c["kitab"], c["bab"], c["fasl"] = kitab, bab, fasl
        nxt = cards[n + 1]["off"] if n + 1 < len(cards) else None
        hi = c["end"]
        if nxt is not None and abs(nxt - hi) < 0.3:      # neighbours touch: don't double-claim a page
            hi = nxt
        nh = next((o for o, *_ in HEADS if o > c["off"] + 1e-6), None)
        if nh is not None and hi > nh:
            hi = nh
        c["pages"] = pages_from(c["off"], hi, upage)
    keys = sorted({c["lesson"] for c in cards})
    lessons = {}
    for key in keys:
        M = meta[key]
        L = {"file": M["file"] or f"{key}.m4a", "minutes": float(M["minutes"]) if M.get("minutes") else None,
             "id": "", "size_mb": None, "label": label_of(key, M["source"]), "source": M["source"]}
        parts = web_parts(key, keys)
        if parts:
            L["web"] = [{"src": f"audio/{name}", "start": st, "mb": round(os.path.getsize(fp) / 1e6, 1)} for name, st, fp in parts]
            L["web_mb"] = round(sum(os.path.getsize(p) for _, _, p in parts) / 1e6, 1)
            L["_files"] = {f"audio/{name}": p for name, _, p in parts}
        lessons[key] = L
    kitabs = []
    toc = h3_toc.TOC
    for i, (level, title, page, *_) in enumerate(toc):
        if level != 1:
            continue
        nxt = next((t[2] for t in toc[i + 1:] if t[0] == 1), h3_toc.LAST_TEXT_PAGE + 1)
        units = []
        for lv, t, p, *_ in toc[i:]:
            if lv == 1 and t != title:
                break
            units.append({"key": "u0" if lv == 1 else f"u{len(units)}", "level": lv, "title": t, "page": p})
        for j, u in enumerate(units):
            u["page_to"] = max((units[j + 1]["page"] if j + 1 < len(units) else nxt) - 1, u["page"])
        kc = [c for c in cards if c["kitab"] == title]
        for c in kc:
            unit = c["fasl"] or c["bab"] or c["kitab"]
            c["unit"] = next(u["key"] for u in units if u["title"] == unit)
        kg = []
        for g in gaps:
            k, b, f, up = unit_of(g["off"] + 0.01)
            if k == title:
                ps = pages_from(g["off"], g["end"], up)
                kg.append({"unit": next(u["key"] for u in units if u["title"] == (f or b or k)),
                           "pages": plabel(ps), "page_list": ps, "v7": v5_label(*g["v5"]), "text": g["text"],
                           "lesson": g["lesson"]})
        kitabs.append({"slug": h3_toc.SLUGS.get(title, f"k{page}"), "title": title, "page_from": page, "page_to": nxt - 1,
                       "units": units, "cards": kc, "gaps": kg})
    return {"lessons": lessons, "kitabs": kitabs, "notes": notes}


if __name__ == "__main__":
    D = build()
    for o, lv, t, p in HEADS:
        print(f"  {o:8.3f} {'  ' * (lv - 1)}{t}")
    for k in D["kitabs"]:
        if not k["cards"]:
            continue
        print(f"== {k['title']} ({k['slug']}) {k['page_from']}–{k['page_to']}: {len(k['cards'])} cards, {len(k['gaps'])} gaps")
        for c in k["cards"]:
            print(f"   {plabel(c['pages']):>9}  {c['lesson']:16} {c.get('ts') or '':8} {c['unit']} v5 {c['v5a']}–{c['v5b']} "
                  f"{'' if c['found'] else '(start not found)'} {c['title'][:50]}")
