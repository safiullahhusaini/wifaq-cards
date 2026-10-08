"""Hidaya 4: gather every lesson's cards (h4/h4_<date>.py + the 18 May pilot in h4_cards.py), put them on the
colleagues' pages, and split them by kitab -> bab/fasl in book order.

build() -> {"lessons": {...}, "kitabs": [ {slug, title, page_from, page_to, units: [...], cards: [...], gaps: [...]} ]}
"""
import csv, glob, json, math, os, re, runpy

HERE = os.path.dirname(os.path.abspath(__file__))
import h4_pagemap as pm
import h4_toc
import h4_cards as pilot

MONTHS = ["جنوری", "فروری", "مارچ", "اپریل", "مئی", "جون", "جولائی", "اگست", "ستمبر", "اکتوبر", "نومبر", "دسمبر"]
URDU_DIGITS = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")

SLUGS = {"كتاب الشفعة": "shufa", "كتاب القسمة": "qisma", "كتاب المزارعة": "muzaraa", "كتاب المساقاة": "musaqat",
         "كتاب الذبائح": "dhabaih", "كتاب الأضحية": "udhiya", "كتاب الكراهية": "karahiya", "كتاب إحياء الموات": "ihya",
         "كتاب الأشربة": "ashriba", "كتاب الصيد": "sayd", "كتاب الرهن": "rahn", "كتاب الجنايات": "jinayat",
         "كتاب الديات": "diyat", "كتاب المعاقل": "maaqil", "كتاب الوصايا": "wasaya", "كتاب الخنثى": "khuntha",
         "مسائل شتى": "shatta"}

# Light audio published with the site (Ogg Opus) lives in the site itself: <repo>/hidaya4/audio/<date>.ogg, or
# <date>-1.ogg, <date>-2.ogg … for split lessons. audio/parts.json may give each part's start second
# ({"2025-06-14-2.ogg": 1743.31}); otherwise starts are summed from the earlier parts' durations (ffprobe).
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
AUDIO_DIR = os.path.join(REPO, "hidaya4", "audio")


# Two recordings on one date: the lesson key is the queue id without "h4-" (e.g. "2025-08-09-udhiya-2"); the card
# file sets LESSON to that key, its audio is hidaya4/audio/<key>.ogg (or <key>-1.ogg …), and LESSON_FILES names its
# recording in recordings.csv by its Drive id (file names mix Arabic letter forms). Plain-date keys work as before.
LESSON_FILES = {"2025-08-09-udhiya-2": "1T8bKxus3AK9NQgTdbUnB5KMuHbzZZIkm"}   # "2025-08-09 … كتاب الأضحية 2.m4a", 7 min
LESSON_SUFFIX = {"2025-08-09-udhiya-2": "دوسری ریکارڈنگ"}


def web_parts(date):
    one = os.path.join(AUDIO_DIR, f"{date}.ogg")
    if os.path.exists(one):
        return [(f"{date}.ogg", 0.0, one)]
    pat = re.compile(re.escape(date) + r"-(\d+)\.ogg$")
    others = {f"{k}.ogg" for k in LESSON_FILES if k != date}   # another lesson's own file is never a part of this one
    parts = sorted((p for p in glob.glob(os.path.join(AUDIO_DIR, f"{date}-*.ogg"))
                    if pat.search(os.path.basename(p)) and os.path.basename(p) not in others),
                   key=lambda p: int(pat.search(os.path.basename(p)).group(1)))
    known = {}
    pj = os.path.join(AUDIO_DIR, "parts.json")
    if os.path.exists(pj):
        with open(pj, encoding="utf-8") as f:
            known = json.load(f)
    out, start = [], 0.0
    for p in parts:   # in order; start of each = parts.json value, else the sum of the earlier durations
        name = os.path.basename(p)
        st = float(known.get(name, start))
        out.append((name, round(st, 2), p))
        start = st + _dur(p)
    return out


def _dur(path):
    import subprocess
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                       capture_output=True, text=True)
    return float(r.stdout.strip() or 0)


# Recordings whose file name has no day: the date in recordings.csv is our estimate, and the page says so.
# 2025-07-20 = "2025-07- … كتاب الذبائح", the kitab's first lesson: it falls between 07-19 (المساقاة) and 07-26,
# and 07-26 opens where it ends (the four veins). The user agreed to use this estimate on 5 Oct 2026.
ESTIMATED_DATES = {"2025-07-20"}


def label_of(key):
    date = key[:10]
    y, m, d = map(int, date.split("-"))
    s = f"{d} {MONTHS[m - 1]} {y}" if d != 1 else f"یکم {MONTHS[m - 1]} {y}"
    if key in LESSON_SUFFIX:
        s += f"، {LESSON_SUFFIX[key]}"
    return s + " (اندازاً)" if date in ESTIMATED_DATES else s


def recordings():
    path = os.path.join(HERE, "..", "data", "recordings.csv")   # trimmed copy of Drive's recording_ids.csv
    out = {}
    with open(path, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            r = {k.replace("\\", "").strip(): (v or "").replace("\\", "").strip() for k, v in r.items()}
            if "ہدایہ جلد رابع" in r.get("book", "") and r.get("date"):
                out.setdefault(r["date"], r)
                out["id:" + r["drive_id"]] = r
    for key, fid in LESSON_FILES.items():
        if "id:" + fid in out:
            out[key] = out["id:" + fid]
    return out


def v7_label(a, b):
    a, b = int(a), int(b)
    return f"بشریٰ ج٧ ص {a}" if a == b else f"بشریٰ ج٧ ص {a}–{b}"


def pages_from(lo, hi, floor_page=None):
    s, e = pm.colleague(lo), pm.colleague(max(lo, hi - 1))
    a, b = math.floor(s + 1e-6), math.floor(e + 1e-6)
    if floor_page:
        a = max(a, floor_page); b = max(b, a)
    return list(range(a, b + 1))


def plabel(ps):
    return str(ps[0]) if len(ps) == 1 else f"{ps[0]}–{ps[-1]}"


# ---- headings: offsets of every TOC entry inside our range (for unit assignment)
def headings():
    pts = []
    for h in pm.HEADINGS:
        p, t, cp = h[:3]
        off = pm.heading_offset(p, t, h[3] if len(h) > 3 else None)
        pts.append((off, cp))
    by_page = {cp: off for off, cp in pts}
    out = []
    for level, title, cp in h4_toc.TOC:
        if cp in by_page and title not in ("مقدمة", "منهج عملنا في هذا الكتاب"):
            out.append((by_page[cp], level, title, cp))
    return sorted(out)


HEADS = headings()


def unit_of(off):
    """-> (kitab, bab, fasl, unit title, unit colleague page) for a weighted offset."""
    kitab = bab = fasl = None
    kp = bp = fp = None
    for o, level, title, cp in HEADS:
        if o > off + 1:
            break
        if level == 1:
            kitab, bab, fasl, kp, bp, fp = title, None, None, cp, None, None
        elif level == 2:
            bab, fasl, bp, fp = title, None, cp, None
        else:
            fasl, fp = title, cp
    return kitab, bab, fasl, (fp or bp or kp)


def convert_tags(items, lo, hi):
    out = []
    for it in items or []:
        *head, ss = it
        new = []
        for s in ss:
            if s.get("t") == "k7":
                p = int(s["v"])
                a, b = max(lo, pm.START[p]), min(hi, pm.START[p] + pm.W[p])
                if a >= b:
                    a, b = pm.START[p], pm.START[p] + pm.W[p]
                new.append({"t": "k", "v": plabel(pages_from(a, b)), "v7": p})
            else:
                new.append(s)
        out.append((*head, new))
    return out


def lesson_cards():
    cards, gaps, notes = [], [], []
    for f in sorted(glob.glob(os.path.join(HERE, "h4", "h4_20*.py"))):
        d = runpy.run_path(f)
        date = d["LESSON"]
        for i, c in enumerate(d["CARDS"]):
            lo, hit = pm.offset_of(int(c["v7"]), c.get("start"), c.get("v7_frac") or 0.0)
            ve, vf = int(c.get("v7_end") or c["v7"]), c.get("v7_end_frac")
            hi = pm.START[ve] + (1.0 if vf is None else vf) * pm.W[ve]
            if hi <= lo + 20:
                hi = lo + 120
            v7a = hit[1] if hit else int(c["v7"])
            card = dict(c)
            card.update(lesson=date, off=lo, end=hi, src=f"{os.path.basename(f)}#{i + 1}", found=bool(hit),
                        v7a=v7a, v7b=max(v7a, ve if (vf is None or vf > 0.02) else ve - 1))
            for key in ("tamheed", "masala", "dalil", "ikhtilaf", "faida", "lughat"):
                card[key] = convert_tags(c.get(key), lo, hi)
            if date == "2025-05-17" and i == 0:
                card["badges"] = ["17 مئی کی دہرائی"]
            cards.append(card)
        for rng, text in d.get("GAPS", []):
            nums = [int(x) for x in re.findall(r"\d+", re.sub(r"^\s*v7\s*", "", rng))]
            if nums:
                a, b = nums[0], nums[-1]
                lo_, hi_ = pm.START[a], pm.START[b] + pm.W[b]
                gaps.append({"lesson": date, "off": lo_, "end": hi_, "mid": (lo_ + hi_) / 2, "v7": (a, b), "text": text})
        notes += [(date, n) for n in d.get("NOTES", [])]
    return cards, gaps, notes


def pilot_cards():
    out = []
    for i, c in enumerate(pilot.CARDS):
        lo, hit = pm.offset_of(30, c["start"], 0.0, search=2)
        card = dict(c)
        card.update(off=lo, end=lo + 300, src=f"h4_cards.py#{i + 1}", found=bool(hit), fixed_pages=True,
                    v7a=hit[1] if hit else None, v7b=hit[1] if hit else None)
        out.append(card)
    return out


def build():
    recs = recordings()
    cards, gaps, notes = lesson_cards()
    cards += pilot_cards()
    cards.sort(key=lambda c: c["off"])
    # pages + unit
    for n, c in enumerate(cards):
        kitab, bab, fasl, upage = unit_of(c["off"])
        c["kitab"], c["bab"], c["fasl"] = kitab, bab, fasl
        if not c.get("fixed_pages"):
            # end at the next card's start when they touch, so neighbours don't double-claim a page
            nxt = cards[n + 1]["off"] if n + 1 < len(cards) else None
            hi = c["end"]
            if nxt and abs(nxt - hi) < 150:
                hi = nxt
            nh = next((o for o, *_ in HEADS if o > c["off"] + 1), None)
            if nh is not None and hi > nh:
                hi = nh
            c["pages"] = pages_from(c["off"], hi, upage)
    # lessons used
    dates = sorted({c["lesson"] for c in cards if c.get("lesson")})
    lessons = {}
    for dte in dates:
        r = recs.get(dte, {})
        L = {"file": r.get("file", f"{dte}.mp4"), "minutes": float(r["minutes"]) if r.get("minutes") else None,
             "id": r.get("drive_id", ""), "size_mb": float(r["size_mb"]) if r.get("size_mb") else None,
             "label": label_of(dte)}
        parts = web_parts(dte)
        if parts:
            L["web"] = [{"src": f"audio/{name}", "start": st, "mb": round(os.path.getsize(fp) / 1e6, 1)} for name, st, fp in parts]
            L["web_mb"] = round(sum(os.path.getsize(p) for _, _, p in parts) / 1e6, 1)
            L["_files"] = {f"audio/{name}": p for name, _, p in parts}
        lessons[dte] = L
    # kitabs in book order
    kitabs = []
    toc = h4_toc.TOC
    for i, (level, title, cp) in enumerate(toc):
        if level != 1 or title in ("مقدمة", "منهج عملنا في هذا الكتاب", "فهارس مطالب «الهداية»"):
            continue
        nxt = next((p for lv, t, p in toc[i + 1:] if lv == 1), h4_toc.LAST_TEXT_PAGE + 1)
        units, cur_bab = [], None
        for lv, t, p in toc[i:]:
            if p >= nxt and lv == 1 and t != title:
                break
            if lv == 1 and t != title:
                break
            if lv == 1:
                units.append({"key": "u0", "level": 1, "title": t, "page": p})
            elif lv == 2:
                units.append({"key": f"u{len(units)}", "level": 2, "title": t, "page": p})
            else:
                units.append({"key": f"u{len(units)}", "level": 3, "title": t, "page": p})
        for j, u in enumerate(units):
            u["page_to"] = (units[j + 1]["page"] if j + 1 < len(units) else nxt) - 1
            u["page_to"] = max(u["page_to"], u["page"])
        kc = [c for c in cards if c["kitab"] == title]
        for c in kc:
            unit = c["fasl"] or c["bab"] or c["kitab"]
            c["unit"] = next(u["key"] for u in units if u["title"] == unit)
        kg = []
        for g in gaps:
            k, b, f, up = unit_of(g["mid"])
            if k == title:
                ps = pages_from(g["off"], g["end"], up)
                kg.append({"unit": next(u["key"] for u in units if u["title"] == (f or b or k)),
                           "pages": plabel(ps), "page_list": ps, "v7": v7_label(*g["v7"]), "text": g["text"],
                           "lesson": g["lesson"]})
        kitabs.append({"slug": SLUGS.get(title, f"k{cp}"), "title": title, "page_from": cp, "page_to": nxt - 1,
                       "units": units, "cards": kc, "gaps": kg})
    return {"lessons": lessons, "kitabs": kitabs, "notes": notes}


if __name__ == "__main__":
    D = build()
    for k in D["kitabs"]:
        if not k["cards"]:
            continue
        print(f"== {k['title']} ({k['slug']}) {k['page_from']}–{k['page_to']}: {len(k['cards'])} cards, {len(k['gaps'])} gaps")
        for u in k["units"]:
            cs = [c for c in k["cards"] if c["unit"] == u["key"]]
            print(f"   [{u['key']}] {'  ' * (u['level'] - 1)}{u['title']} {u['page']}–{u['page_to']}: {len(cs)} cards")
            for c in cs:
                print(f"        {plabel(c['pages']):>9}  {c.get('lesson') or '—':10} {c.get('ts') or '':8} v7 {c.get('v7a')}–{c.get('v7b')} {'' if c['found'] else '(start not found)'} {c['title'][:60]}")
    print({d: (L.get("web_mb"), L["id"][:6]) for d, L in D["lessons"].items()})
