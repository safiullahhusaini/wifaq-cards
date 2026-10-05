import nbformat as nbf
core = open("tsfix_core.py", encoding="utf-8").read().rstrip()
driver = open("tsfix_driver.py", encoding="utf-8").read().rstrip()

intro = """# Wifaq 1448 — timestamp repair v2

Gemini writes the lessons' text well, but on long clips its timestamps drift: some transcripts run past the end of the recording (49:21 in a 33-minute lesson), others stop minutes early. A green time on a card must land on the right sentence, so this notebook corrects every timestamp **from the audio itself**:

1. Whisper (free, on Colab's GPU) listens to the recording and notes when each word is spoken. Its text is weaker than Gemini's, so only its timings are used.
2. Each Gemini line is found in Whisper's words and gets Whisper's time. Lines Whisper didn't catch are placed in proportion between their neighbours.
3. Stretches where the audio has plenty of speech but the transcript has almost no text are listed as **text missing**, so only those lessons need transcribing again.

**No Gemini requests are used.** It runs side by side with the transcription notebook: it only touches finished transcripts, never the inventory, the log or `_pipeline`, and it leaves alone any transcript the transcription notebook is still going to redo.

**What changes in Drive**
- Each corrected transcript gets new timestamps and a `- وقت:` line in its header (and `- خلا:` when text is missing). The text itself is not changed.
- An untouched copy of every transcript it changes goes to `transcripts/_original/`.
- `_whisper/` keeps Whisper's word timings, so a lesson is never listened to twice.
- `timestamp_fix.csv` (one row per lesson) and `timestamp_fix.md` (summary: lessons with text missing, lessons that couldn't be matched, biggest corrections). Claude reads these.

**v2 (3 Oct):** reads the audio with ffmpeg (the first run stopped on every lesson with a PyAV error), understands lines written as `01:03 [0:01:03] …`, and adds cell 6, which makes light audio copies for the card pages.

**How to run:** Runtime → **Change runtime type → T4 GPU** → Save. Then Runtime → **Run all**. Hidaya 4 goes first. A 45-minute lesson takes roughly 1–3 minutes; it stops by itself after `MAX_HOURS`, and the next run carries on. Colab gives free GPU time in limited amounts per day; if it says no GPU is available, try again later."""

c1 = """# @title 1 · Connect Drive and install Whisper (2–3 minutes)
from google.colab import drive
drive.mount('/content/drive')
!pip -q install faster-whisper rapidfuzz
import torch
print("GPU:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "none — choose Runtime → Change runtime type → T4 GPU")"""

c2 = """# @title 2 · Settings
DRIVE = "/content/drive/MyDrive"
OUT_DIR = f"{DRIVE}/Wifaq 1448"

# Same order as the transcription notebook (Hidaya 3 last).
BOOK_ORDER = [
    "ہدایہ جلد رابع",
    "مشکوۃ المصابیح جلد اول",
    "مشکوۃ المصابیح جلد دوم",
    "تیسیر مصطلح الحدیث",
    "شرح نخبۃ الفکر",
    "التبیان فی علوم القرآن",
    "بیضاوی",
    "آئینہ قادیانیت",
    "ہدایہ جلد ثالث",
]
ONLY_BOOKS = []          # e.g. ["ہدایہ جلد رابع"] to do just that book; empty = every book, in the order above

WHISPER_MODEL = "large-v3"   # most accurate; "large-v3-turbo" is about 3× faster with slightly weaker Urdu
MAX_HOURS = 4                # stops by itself after this long (Colab's free GPU time is limited)
REFIX = False                # True = check transcripts that were already corrected once more

# Transcripts with text missing: False = just list them in timestamp_fix.md (recommended at first).
# True = also move them to transcripts/_redo, so the transcription notebook transcribes them again.
MOVE_GAPS_FOR_REDO = False"""

c3 = "# @title 3 · Functions (run once, no need to edit)\n" + core + "\n\n\n" + driver + "\n\nprint('✓ ready')"

c4 = """# @title 4 · Correct the timestamps (safe to stop and run again)
run_fix()"""

c5 = """# @title 5 · Check by ear (optional): open three corrected moments in Drive on a laptop
import random
ids = {}
try:
    with open(os.path.join(OUT_DIR, "recording_ids.csv"), encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            ids[r["file"]] = r["drive_id"]
except OSError:
    pass
fixed = [r for r in list_transcripts() if r["fixed"]]
if not fixed:
    print("Nothing corrected yet.")
else:
    row = random.choice(fixed)
    with open(row["path"], encoding="utf-8") as f:
        lines = parse_lines(split_transcript(f.read())[1])
    fid = ids.get(os.path.basename(row["audio"]), "")
    print(row["file"], "\\n")
    for ln in random.sample(lines, min(3, len(lines))):
        link = f"https://drive.google.com/file/d/{fid}/view?t={ln['old']}" if fid else "(no Drive ID)"
        print(f"[{fmt_hms(ln['old'])}] {ln['raw'].strip()[:90]}\\n   {link}\\n")
    print("The teacher should be saying that sentence within a few seconds of where Drive opens.")"""

c6 = """# @title 6 · Light audio copies for the card pages (no GPU needed · safe to stop and run again)
# A small copy of each recording (AAC, 24 kbps, about 8 MB for 45 minutes) goes to My Drive/Wifaq 1448/web_audio/.
# Claude puts these copies inside the card pages, so a tap on a green time plays the teacher right there.
# Claude can fetch files up to 10 MB from Drive, so longer lessons are cut into equal parts.
WEB_BOOKS = ["ہدایہ جلد رابع"]   # books to prepare, in this order (add more later)
WEB_KBPS = 24
MAX_MB = 9.5
MAKE_WEB_AUDIO = True  # @param {type:"boolean"}

import math
WEB_DIR = os.path.join(OUT_DIR, "web_audio")


def _web_targets():
    with open(os.path.join(OUT_DIR, "recordings_inventory.csv"), encoding="utf-8-sig") as f:
        recs = list(csv.reader(f))[1:]
    out = []
    for rec in recs:
        rec = rec + [""] * (12 - len(rec))
        file, book, date, path = rec[0], rec[1], rec[10], rec[11]
        ranks = [i for i, b in enumerate(WEB_BOOKS) if _norm_name(b) and _norm_name(b) in _norm_name(book)]
        if path and ranks:
            out.append((ranks[0], date or "9999", file, book, path))
    return sorted(out)


def _encode(src, start, seconds, dst, kbps):
    tmp = os.path.join(LOCAL, "web_tmp.m4a")
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", f"{start:.2f}", "-t", f"{seconds:.2f}", "-i", src,
                    "-vn", "-ac", "1", "-ar", "16000", "-c:a", "aac", "-b:a", f"{kbps}k", "-movflags", "+faststart", tmp],
                   check=True, capture_output=True, timeout=3600)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(tmp, dst + ".part")
    os.replace(dst + ".part", dst)
    return os.path.getsize(dst)


def make_web_audio():
    targets = _web_targets()
    print(f"{len(targets)} recordings in {', '.join(WEB_BOOKS)}", flush=True)
    made = 0
    for n, (_, _, file, book, path) in enumerate(targets, 1):
        stem = os.path.splitext(file)[0]
        side = os.path.join(WEB_DIR, book, stem + ".json")
        if os.path.exists(side):
            continue
        try:
            local = local_copy(path)
            dur = probe_seconds(local)
            parts = max(1, math.ceil((dur * WEB_KBPS * 125 * 1.04 + 60000) / (MAX_MB * 1e6)))
            step = dur / parts
            info = []
            for i in range(parts):
                name = f"{stem}.m4a" if parts == 1 else f"{stem} - {i + 1}.m4a"
                dst = os.path.join(WEB_DIR, book, name)
                size = _encode(local, i * step, step if i < parts - 1 else dur - i * step + 1, dst, WEB_KBPS)
                if size > MAX_MB * 1e6:      # rare: very dense audio, so squeeze a little more
                    size = _encode(local, i * step, step if i < parts - 1 else dur - i * step + 1, dst, 16)
                info.append({"web_file": f"{book}/{name}", "start": round(i * step, 2), "size_mb": round(size / 1e6, 2)})
            with open(side, "w", encoding="utf-8") as f:
                json.dump({"file": file, "book": book, "seconds": round(dur, 1), "parts": info}, f, ensure_ascii=False)
            made += 1
            print(f"[{n}/{len(targets)}] {file}: {len(info)} part(s), {sum(p['size_mb'] for p in info):.1f} MB", flush=True)
        except Exception as e:
            print(f"[{n}/{len(targets)}] {file}: ✗ {type(e).__name__}: {str(e)[:150]}", flush=True)
        finally:
            try:
                os.remove(local)
            except Exception:
                pass
    # one index for Claude
    rows = []
    for side in glob.glob(os.path.join(WEB_DIR, "*", "*.json")):
        with open(side, encoding="utf-8") as f:
            d = json.load(f)
        for i, p in enumerate(d["parts"], 1):
            rows.append([d["book"], d["file"], i, p["start"], d["seconds"], p["size_mb"], p["web_file"]])
    with open(os.path.join(WEB_DIR, "index.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["book", "file", "part", "start_sec", "lesson_seconds", "size_mb", "web_file"])
        w.writerows(sorted(rows))
    print(f"\\n✓ {made} new, {len(rows)} files listed in web_audio/index.csv")


if MAKE_WEB_AUDIO:
    make_web_audio()
else:
    print("Skipped. Tick MAKE_WEB_AUDIO to make the light copies.")"""

nb = nbf.v4.new_notebook()
nb.cells = [nbf.v4.new_markdown_cell(intro)] + [nbf.v4.new_code_cell(c) for c in (c1, c2, c3, c4, c5, c6)]
nb.metadata = {"colab": {"provenance": [], "name": "Wifaq 1448 — Timestamp repair v2.ipynb"},
               "accelerator": "GPU", "kernelspec": {"name": "python3", "display_name": "Python 3"},
               "language_info": {"name": "python"}}
nbf.write(nb, "Wifaq_1448_Timestamp_Repair_v2.ipynb")
# compile check of settings + functions + run cells (without Colab magics)
src = c2 + "\n" + c3.replace("!pip", "#pip") + "\n" + c5 + "\n" + c6
compile(src, "cells", "exec")
print("written + compiles")
