import os, re, sys, math, random, shutil, tempfile
T = tempfile.mkdtemp()
OUT_DIR = os.path.join(T, "Wifaq 1448")
BOOK_ORDER = ["ہدایہ جلد رابع", "مشکوۃ المصابیح جلد اول"]
ONLY_BOOKS = []
WHISPER_MODEL = "large-v3"; MAX_HOURS = 1; REFIX = False; MOVE_GAPS_FOR_REDO = False
exec(open("tsfix_core.py", encoding="utf-8").read())
exec(open("tsfix_driver.py", encoding="utf-8").read())

raw = open('/tmp/claude-0/-home-claude/4e00c54e-83be-51e1-a1da-0b0a20c78828/scratchpad/t0601.md', encoding='utf-8').read()
raw = raw.replace('\\[', '[').replace('\\]', ']').replace('\\-', '-').replace('\\#', '#')
raw = "\n".join(l.rstrip() for l in raw.split("\n"))
audio = os.path.join(T, "audio.mp4"); open(audio, "wb").write(b"x" * 1000)
raw = re.sub(r"- راستہ: .*", f"- راستہ: {audio}", raw)
header, body = split_transcript(raw)
lines = parse_lines(body)
dur = 49.9 * 60
# synthetic whisper from TRUE times; transcript gets stretched times 1.3x
rnd = random.Random(3)
words = []
for l, t1 in zip(lines, [x["old"] for x in lines[1:]] + [dur]):
    toks = l["norm"].split(); span = max(t1 - l["old"], .5) * .9
    for j, w in enumerate(toks):
        w2 = "".join((rnd.choice("ابتثجحخدرسشعفقکلمنوہی") if rnd.random() < .2 else c) for c in w)
        words.append((l["old"] + span * j / len(toks), l["old"] + span * (j + 1) / len(toks), w2))
true = {l["k"]: l["old"] for l in lines}
b2 = list(body)
for l in lines:
    m = TS_LINE.match(b2[l["k"]]); b2[l["k"]] = f"{m.group(1)}[{fmt_hms(l['old'] * 1.3)}]{m.group(5)}"
stretched = header + "\n" + "\n".join(b2)
book_dir = os.path.join(OUT_DIR, "transcripts", "ہدایہ جلد رابع"); os.makedirs(book_dir)
tp = os.path.join(book_dir, "2025-06-01 الهدايه الرابع كتاب الشفعة.md")
open(tp, "w", encoding="utf-8").write(stretched)
# a broken one that must be skipped
open(os.path.join(book_dir, "broken.md"), "w", encoding="utf-8").write("# x\n\n- سبق: 2\n- جانچ: 0:00:00: no timestamps\n\n---\n\n[0:00:01] a\n")
calls = []
def fake_run_whisper(path):
    calls.append(path); return dur, words, "fake-large-v3"
run_whisper = fake_run_whisper
run_fix()
print("whisper calls:", len(calls))
out = open(tp, encoding="utf-8").read()
h, b = split_transcript(out)
print("---- header tail:\n" + "\n".join(h.split("\n")[-5:]))
nl = parse_lines(b)
errs = sorted(abs(x["old"] - true[x["k"]]) for x in nl)
print("lines", len(nl), "median err", errs[len(errs)//2], "max err", errs[-1])
print("original kept:", os.path.exists(os.path.join(OUT_DIR, "transcripts", "_original", "ہدایہ جلد رابع", os.path.basename(tp))))
print("cache:", os.listdir(os.path.join(OUT_DIR, "_whisper", "ہدایہ جلد رابع")))
print("---- second run")
run_fix()
print("whisper calls after 2nd run:", len(calls))
print(open(os.path.join(OUT_DIR, "timestamp_fix.md"), encoding="utf-8").read())
print(open(os.path.join(OUT_DIR, "timestamp_fix.csv"), encoding="utf-8-sig").read())
