# ------------------------------------------------------------------ timestamp repair: pure functions
# Gemini writes good text but its timestamps can drift on long clips. Whisper's text is weaker, but its
# timings come from the audio itself. We line Gemini's sentences up against Whisper's words and take
# the time from Whisper. No Gemini request is used.
import re, unicodedata, bisect
import numpy as np
from rapidfuzz import fuzz

# "[0:01:03] text", also "01:03 [0:01:03] text", "- [0:01:03] text", "**[0:01:03]** text" (some models add these)
TS_LINE = re.compile(r"^(\s*(?:[-*•]\s+)?)(?:\*\*)?(?:\(?\d{1,2}:\d{2}(?::\d{2})?\)?\s+)?"
                     r"\[(?:(\d{1,2}):)?(\d{1,4}):(\d{2})\](?:\*\*)?(.*)$")
_FOLD = str.maketrans({
    "ي": "ی", "ى": "ی", "ې": "ی", "ے": "ی", "ئ": "ی", "ك": "ک", "ه": "ہ", "ة": "ہ", "ۃ": "ہ", "ۀ": "ہ",
    "ۂ": "ہ", "ھ": "ہ", "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ؤ": "و", "ء": None, "ـ": None,
    "٠": None, "١": None, "٢": None, "٣": None, "٤": None, "٥": None, "٦": None, "٧": None, "٨": None, "٩": None,
    "۰": None, "۱": None, "۲": None, "۳": None, "۴": None, "۵": None, "۶": None, "۷": None, "۸": None, "۹": None,
})
_KEEP = re.compile(r"[^\w\s]|\d|_")


def norm_text(s):
    """Fold Arabic/Urdu spelling variants, drop diacritics, punctuation and digits."""
    s = unicodedata.normalize("NFC", s or "")
    s = s.replace("[؟]", " ").replace("ع:", " ")
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn").translate(_FOLD)
    s = _KEEP.sub(" ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def fmt_hms(sec):
    sec = int(round(max(sec, 0)))
    return f"{sec // 3600}:{(sec % 3600) // 60:02d}:{sec % 60:02d}"


def split_transcript(text):
    """-> (header, body_lines). Header is everything up to and including the '---' line."""
    lines = text.split("\n")
    for i, l in enumerate(lines[:80]):
        if l.strip() == "---":
            return "\n".join(lines[:i + 1]), lines[i + 1:]
    return "", lines


def parse_lines(body_lines):
    """Timestamped lines -> list of dicts with index into body_lines, old seconds, normalized text."""
    out = []
    for k, line in enumerate(body_lines):
        m = TS_LINE.match(line)
        if not m:
            continue
        sec = int(m.group(2) or 0) * 3600 + int(m.group(3)) * 60 + int(m.group(4))
        out.append({"k": k, "old": sec, "raw": m.group(5), "norm": norm_text(m.group(5))})
    return out


# ------------------------------------------------------------------ whisper side
class WhisperText:
    """Whisper words joined into one normalized string, with a time for every character."""

    def __init__(self, words):
        parts, times = [], []
        for start, end, w in words:
            t = norm_text(w)
            if not t:
                continue
            if parts:
                parts.append(" ")
                times.append(start)
            span = max(end - start, 0.01)
            for j, _ in enumerate(t):
                times.append(start + span * j / max(len(t), 1))
            parts.append(t)
        self.text = "".join(parts)
        self.times = np.array(times, dtype=float) if times else np.zeros(1)

    def time_at(self, i):
        if len(self.text) == 0:
            return 0.0
        i = int(min(max(round(i), 0), len(self.text) - 1))
        return float(self.times[i])

    def char_at_time(self, t):
        return int(np.searchsorted(self.times, t))


# ------------------------------------------------------------------ alignment
def _weighted_lis(anchors):
    """Keep the heaviest subset of anchors whose Whisper positions rise with the line order."""
    n = len(anchors)
    if n == 0:
        return []
    best = [a["score"] for a in anchors]
    prev = [-1] * n
    for i in range(n):
        for j in range(max(0, i - 60), i):           # neighbours are enough; keeps it fast
            if anchors[j]["w0"] < anchors[i]["w0"] and best[j] + anchors[i]["score"] > best[i]:
                best[i], prev[i] = best[j] + anchors[i]["score"], j
    i = int(np.argmax(best))
    keep = []
    while i != -1:
        keep.append(anchors[i])
        i = prev[i]
    return keep[::-1]


def align(lines, wt, duration, min_chars=10):
    """Find each Gemini line in Whisper's text. Returns (new_times, anchors, stats)."""
    W, n = wt.text, len(lines)
    if not lines or len(W) < 50:
        return None, [], {"reason": "Whisper heard almost nothing"}
    # Gemini character positions (cumulative), so a line between two anchors can be placed in proportion.
    cg, pos = [], 0
    for ln in lines:
        cg.append(pos)
        pos += len(ln["norm"]) + 1
    g_total = max(pos, 1)
    ratio = len(W) / g_total                          # Whisper chars per Gemini char, roughly 1
    def find(q, lo, hi, need):
        lo, hi = int(max(0, lo)), int(min(len(W), hi))
        if hi - lo < len(q):
            return None
        r = fuzz.partial_ratio_alignment(q, W[lo:hi], score_cutoff=min(need, 100))
        return None if r is None else (r.score, lo + r.dest_start, lo + r.dest_end)

    def need_for(q):
        return 64 if len(q) >= 45 else (72 if len(q) >= 25 else 82)

    def confirmed(i, w_end, g_end):
        """After a long jump, the next lines must also be found right after it."""
        hits = tries = 0
        for j in range(i + 1, n):
            q2 = lines[j]["norm"]
            if len(q2.replace(" ", "")) < 15:
                continue
            tries += 1
            e2 = w_end + (cg[j] - g_end) * ratio
            if find(q2, e2 - 1200, e2 + 1200 + len(q2), need_for(q2)):
                hits += 1
            if tries == 4:
                break
        return tries > 0 and hits >= min(2, tries)

    anchors = []
    last_w, last_g = 0, 0
    for i, ln in enumerate(lines):
        q = ln["norm"]
        if len(q.replace(" ", "")) < min_chars:
            continue
        need = need_for(q)
        expect = last_w + (cg[i] - last_g) * ratio
        half = max(1500, 0.6 * (cg[i] - last_g) * ratio, len(q) * 4)
        hit = find(q, min(expect - half, len(W) - len(q)), expect + half + len(q), need)
        if hit is None and len(q) >= 25:
            # Gemini may have skipped a stretch: look further ahead, but ask for a closer match
            # and check that the following lines carry on from there.
            far = find(q, expect + half, expect + 9000 + len(q), need + 6)
            if far and confirmed(i, far[2], cg[i] + len(q)):
                hit = far
        if hit is None:
            continue
        score, w0, w1 = hit
        anchors.append({"i": i, "w0": w0, "w1": w1, "score": score * min(len(q), 120) / 120})
        last_w, last_g = w1, cg[i] + len(q)
    eligible = sum(1 for ln in lines if len(ln["norm"].replace(" ", "")) >= min_chars)
    kept = _weighted_lis(anchors)
    stats = {"eligible": eligible, "found": len(anchors), "kept": len(kept),
             "coverage": round(len(kept) / max(eligible, 1), 3)}
    if len(kept) < max(8, 0.25 * eligible):
        stats["reason"] = f"only {len(kept)} of {eligible} lines could be matched"
        return None, kept, stats
    # place every line: anchors exactly, the rest in proportion between neighbouring anchors
    ka = [(a["i"], a["w0"]) for a in kept]
    idx = [a[0] for a in ka]
    new = []
    for i in range(n):
        j = bisect.bisect_left(idx, i)
        if j < len(idx) and idx[j] == i:
            w = ka[j][1]
        elif j == 0:                                   # before the first anchor
            i1, w1 = ka[0]
            w = w1 - (cg[i1] - cg[i]) * ratio
        elif j == len(idx):                            # after the last anchor
            i0, w0 = ka[-1]
            w = w0 + (cg[i] - cg[i0]) * ratio
        else:
            (i0, w0), (i1, w1) = ka[j - 1], ka[j]
            f = (cg[i] - cg[i0]) / max(cg[i1] - cg[i0], 1)
            w = w0 + f * (w1 - w0)
        new.append(min(max(wt.time_at(w), 0.0), duration))
    for i in range(1, n):                              # never go backwards
        new[i] = max(new[i], new[i - 1])
    shifts = [abs(new[i] - lines[i]["old"]) for i in range(n)]
    stats.update({"median_shift": round(float(np.median(shifts)), 1), "max_shift": round(float(max(shifts)), 1),
                  "end_old": lines[-1]["old"], "end_new": round(new[-1], 1)})
    return new, kept, stats


def find_gaps(lines, kept, wt, duration, min_sec=75):
    """Stretches where Whisper heard a lot of speech but Gemini wrote little: likely skipped text."""
    if not kept:
        return []
    cg, pos = [], 0
    for ln in lines:
        cg.append(pos)
        pos += len(ln["norm"]) + 1
    g_end = pos
    ratio = len(wt.text) / max(g_end, 1)
    pts = [(-1, 0, 0)] + [(a["i"], a["w0"], cg[a["i"]]) for a in kept] + [(len(lines), len(wt.text), g_end)]
    gaps = []
    for (ia, wa, ga), (ib, wb, gb) in zip(pts, pts[1:]):
        ta, tb = wt.time_at(wa), (wt.time_at(wb) if wb < len(wt.text) else duration)
        w_chars, g_chars = wb - wa, (gb - ga) * ratio
        if tb - ta >= min_sec and w_chars >= 700 and g_chars < 0.35 * w_chars:
            gaps.append((round(ta), round(tb)))
    return gaps


def render(header, body_lines, lines, new_times, note_lines):
    body = list(body_lines)
    for ln, t in zip(lines, new_times):
        m = TS_LINE.match(body[ln["k"]])
        body[ln["k"]] = f"{m.group(1)}[{fmt_hms(t)}]{m.group(5)}"
    head = header.split("\n")
    # put our notes just above the closing '---' (after an existing '- جانچ:' line, if any)
    while head and head[-1].strip() in ("", "---"):
        head.pop()
    head = [h for h in head if not h.startswith("- وقت:") and not h.startswith("- خلا:")]
    return "\n".join(head + note_lines + ["", "---"] + body)
