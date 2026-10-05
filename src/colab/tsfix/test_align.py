import re, random, math, sys
sys.path.insert(0, '.')
from tsfix_core import *

raw = open('/tmp/claude-0/-home-claude/4e00c54e-83be-51e1-a1da-0b0a20c78828/scratchpad/t0601.md', encoding='utf-8').read()
raw = raw.replace('\\[', '[').replace('\\]', ']').replace('\\-', '-').replace('\\#', '#').replace('\\*', '*')
raw = "\n".join(l.rstrip() for l in raw.split("\n"))
header, body = split_transcript(raw)
lines = parse_lines(body)
dur = 49.9 * 60
print("lines", len(lines), "header ok", header.strip().endswith('---'))

def run_case(name, warp_true, distort_old, drop_range=None, noise=0.15, seed=1):
    rnd = random.Random(seed)
    # TRUE time for each line = warp of the original timestamp (pretend originals are the truth source)
    true = [warp_true(l["old"]) for l in lines]
    # Whisper words: from every line's text (even ones Gemini 'skipped'), noisy
    words = []
    for l, t0, t1 in zip(lines, true, true[1:] + [dur]):
        toks = l["norm"].split()
        if not toks: continue
        span = max(t1 - t0, 0.5) * 0.9
        for j, w in enumerate(toks):
            if rnd.random() < 0.08: continue                 # whisper drops a word
            w2 = "".join((rnd.choice("ابتثجحخدذرزسشصضطظعغفقکلمنوہی") if rnd.random() < noise else ch) for ch in w)
            words.append((t0 + span * j / len(toks), t0 + span * (j + 1) / len(toks), w2))
    wt = WhisperText(words)
    # GEMINI transcript under test: distorted timestamps, optionally some lines missing
    test_lines = []
    for l, t in zip(lines, true):
        if drop_range and drop_range[0] <= t <= drop_range[1]:
            continue
        d = dict(l); d["old"] = int(distort_old(t)); d["true"] = t
        test_lines.append(d)
    new, kept, st = align(test_lines, wt, dur)
    if new is None:
        print(name, "NOT ALIGNED", st); return
    err = [abs(n - l["true"]) for n, l in zip(new, test_lines)]
    err_old = [abs(l["old"] - l["true"]) for l in test_lines]
    err.sort(); err_old.sort()
    gaps = find_gaps(test_lines, kept, wt, dur)
    print(f"{name:28s} cov {st['coverage']:.2f}  before: median {err_old[len(err_old)//2]:6.1f}s max {err_old[-1]:6.1f}s"
          f"  after: median {err[len(err)//2]:5.1f}s p95 {err[int(.95*len(err))]:5.1f}s max {err[-1]:5.1f}s  gaps {[(fmt_hms(a),fmt_hms(b)) for a,b in gaps]}")

ident = lambda t: t
run_case("clean, same times", ident, ident)
run_case("stretch 1.35x (overshoot)", ident, lambda t: t * 1.35)
run_case("compress 0.85x", ident, lambda t: t * 0.85)
run_case("wavy drift ±120s", ident, lambda t: t + 120 * math.sin(t / 400))
run_case("stretch + 25% noise", ident, lambda t: t * 1.3, noise=0.25)
run_case("skip 20:00-24:00", ident, lambda t: t * 1.2, drop_range=(1200, 1440))
run_case("skip last 5 min", ident, ident, drop_range=(dur - 300, dur))
run_case("true timeline warped", lambda t: t * 0.95 + 30, lambda t: t)
run_case("very noisy whisper 40%", ident, lambda t: t * 1.3, noise=0.40)
run_case("hopeless whisper 60%", ident, lambda t: t * 1.3, noise=0.60)
