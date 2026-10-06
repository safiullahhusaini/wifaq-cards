import nbformat as nbf
core = open("tsfix_core.py", encoding="utf-8").read().rstrip()
driver = open("tsfix_driver.py", encoding="utf-8").read().rstrip()

intro = """# Wifaq 1448 — timestamp repair v3

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

**v3 (6 Oct):** set to Hidaya 4 only (`ONLY_BOOKS` in cell 2), and cell 6 now makes the Opus copies (16 kbps) that the site uses, instead of the old AAC copies. Transcripts re-done with `cell_retranscribe.py` have no `- وقت:` line, so cell 4 picks them up.

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
ONLY_BOOKS = ["ہدایہ جلد رابع"]   # just this book; [] = every book, in the order above

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

c6 = open("../cell7_opus_audio.py", encoding="utf-8").read().rstrip().replace(
    "# @title 7 · Opus audio", "# @title 6 · Opus audio", 1).replace(
    "# Run cells 1–3 of the Timestamp Repair notebook first, then this cell.\n", "", 1)

nb = nbf.v4.new_notebook()
nb.cells = [nbf.v4.new_markdown_cell(intro)] + [nbf.v4.new_code_cell(c) for c in (c1, c2, c3, c4, c5, c6)]
nb.metadata = {"colab": {"provenance": [], "name": "Wifaq 1448 — Timestamp repair v3.ipynb"},
               "accelerator": "GPU", "kernelspec": {"name": "python3", "display_name": "Python 3"},
               "language_info": {"name": "python"}}
nbf.write(nb, "Wifaq_1448_Timestamp_Repair_v3.ipynb")
# compile check of settings + functions + run cells (without Colab magics)
src = c2 + "\n" + c3.replace("!pip", "#pip") + "\n" + c5 + "\n" + c6
compile(src, "cells", "exec")
print("written + compiles")
