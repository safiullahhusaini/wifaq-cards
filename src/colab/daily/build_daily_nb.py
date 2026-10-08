# Builds "Wifaq 1448 — Daily.ipynb": one notebook the user runs once a day (T4 GPU, Run all).
# It does what Claude's scheduled runs put in Drive `Wifaq 1448/automation/daily_config.json`:
#   1. re-transcribes the transcripts in `redo` (Gemini 3.8 / 3.7 / 3.6 Flash, same as cell_retranscribe.py),
#   2. repairs timestamps of every unrepaired transcript in `repair_books` (Timestamp Repair v3 code),
#   3. makes Opus copies for `opus_books` (cell 7 code),
#   4. writes `automation/daily_done.md` so the next Claude run knows what happened.
# Run from src/colab/daily:  python3 build_daily_nb.py
import nbformat as nbf

retx = open("retx_core.py", encoding="utf-8").read().rstrip()
core = open("../tsfix/tsfix_core.py", encoding="utf-8").read().rstrip()
driver = open("../tsfix/tsfix_driver.py", encoding="utf-8").read().rstrip()
opus = open("../cell7_opus_audio.py", encoding="utf-8").read().rstrip()
opus = opus[opus.index("import csv, glob, json, math, os, shutil, subprocess"):]
opus = opus[:opus.index("if MAKE_OPUS:")].rstrip()

intro = """# Wifaq 1448 — Daily

**Once a day, after 12:00 pm** (1:00 pm from 1 Nov, when the free Gemini quota resets):
Runtime → **Change runtime type → T4 GPU** → Save, then Runtime → **Run all**. Nothing to edit.

Claude's scheduled card runs decide what this notebook does and write it to `My Drive/Wifaq 1448/automation/daily_config.json`. In order:

1. **Re-transcribe** the lessons whose transcripts are broken or have text missing (Gemini 3.8 / 3.7 / 3.6 Flash, your two keys, 10-minute parts, each part checked). The old transcript is kept in `transcripts/_replaced/`.
2. **Repair timestamps** of every transcript that hasn't been repaired yet (Whisper on the GPU, no Gemini quota). Hidaya 4 first.
3. **Opus copies** of the recordings for the card site.
4. Writes `automation/daily_done.md` for Claude.

When it says ✓ Finished, run your transcription notebook (v2.5) as usual: it uses whatever quota is left.

It is safe to stop and run again: finished work is skipped. If Colab says no GPU is available, try again later; step 1 still works on the CPU."""

c1 = """# @title 1 · Connect Drive and install (2–3 minutes)
from google.colab import drive, userdata
drive.mount('/content/drive')
!pip -q install faster-whisper rapidfuzz google-genai
import torch
print("GPU:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "none — Runtime → Change runtime type → T4 GPU (step 1 still works)")"""

c2 = """# @title 2 · Read today's to-do from Drive (written by Claude)
import os, json, datetime
DRIVE = "/content/drive/MyDrive"
OUT_DIR = f"{DRIVE}/Wifaq 1448"
TX_DIR = os.path.join(OUT_DIR, "transcripts")
AUTO_DIR = os.path.join(OUT_DIR, "automation")
os.makedirs(AUTO_DIR, exist_ok=True)

CONFIG = {"redo": [], "repair_books": ["ہدایہ جلد رابع"], "opus_books": ["ہدایہ جلد رابع"],
          "skip_books": ["ہدایہ جلد ثالث"], "whisper_model": "large-v3", "max_hours": 3}
try:
    with open(os.path.join(AUTO_DIR, "daily_config.json"), encoding="utf-8") as f:
        CONFIG.update(json.load(f))
    print("To-do updated by Claude:", CONFIG.get("updated", "?"))
except FileNotFoundError:
    print("No daily_config.json yet — using the defaults.")

# Settings used by the repair and Opus code below
BOOK_ORDER = ["ہدایہ جلد رابع", "مشکوۃ المصابیح جلد اول", "مشکوۃ المصابیح جلد دوم", "تیسیر مصطلح الحدیث",
              "شرح نخبۃ الفکر", "التبیان فی علوم القرآن", "بیضاوی", "آئینہ قادیانیت", "ہدایہ جلد ثالث"]
ONLY_BOOKS = CONFIG["repair_books"]
WHISPER_MODEL = CONFIG.get("whisper_model", "large-v3")
MAX_HOURS = float(CONFIG.get("max_hours", 3))
REFIX = False
MOVE_GAPS_FOR_REDO = False
WEB_BOOKS = CONFIG["opus_books"]
OPUS_KBPS, MAX_MB = 16, 5.0

print(f"1 · re-transcribe: {len(CONFIG['redo'])} lesson(s)")
for t in CONFIG["redo"]:
    print("     ", t["file"])
print(f"2 · repair: {', '.join(ONLY_BOOKS) or 'all books'}")
print(f"3 · Opus copies: {', '.join(WEB_BOOKS) or 'none'}")"""

c3 = "%%writefile /content/retx_core.py\n" + retx

c4 = "# @title 4 · Functions (no need to edit)\n" + core + "\n\n\n" + driver + "\n\n\n" + opus + "\n\nprint('✓ ready')"

c5 = """# @title 5 · Re-transcribe (Gemini) — safe to stop and run again
import importlib, sys
sys.path.insert(0, "/content")
import retx_core as rx
importlib.reload(rx)
rx.OUT_DIR, rx.TX_DIR = OUT_DIR, TX_DIR

def _secret(name):
    try:
        return userdata.get(name)
    except Exception:
        return None

DONE_LOG = []
todo = [t for t in CONFIG["redo"] if not rx.already_redone(t["file"], t.get("added", "2000-01-01"))]
if not todo:
    print("Nothing to re-transcribe today.")
elif not rx.setup_lanes(_secret):
    print("No API key found: add GEMINI_API_KEY (and VERTEX_API_KEY) in Colab Secrets with Notebook access. Skipping step 1.")
else:
    rx.say(f"{len(todo)} to re-transcribe · lanes: {', '.join('Vertex express' if l else 'AI Studio' for l, _ in rx.LANES)}")
    for t in todo:
        ok = rx.redo(t["file"])
        DONE_LOG.append(("✓" if ok else "✗") + " " + t["file"])
        if not ok and len(rx.DEAD) >= len(rx.COMBOS):
            rx.say("All models are out of quota for today; the rest waits for tomorrow.")
            break
    print(f"\\n{sum(1 for x in DONE_LOG if x.startswith('✓'))} of {len(todo)} re-transcribed.")"""

c6 = """# @title 6 · Repair timestamps (GPU) — stops by itself after max_hours
run_fix()"""

c7 = """# @title 7 · Opus copies for the card site
make_opus_audio()"""

c8 = """# @title 8 · Note for Claude
import csv
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5)))
lines = [f"# Daily run {now:%d %b %Y, %I:%M %p}", "", "## Re-transcribed"] + [f"- {x}" for x in DONE_LOG or ["(none)"]]
try:
    with open(os.path.join(OUT_DIR, "timestamp_fix.csv"), encoding="utf-8-sig") as f:
        rows = [r for r in csv.DictReader(f) if r.get("time_pk", "").startswith(now.strftime("%Y-%m-%d"))]
    lines += ["", f"## Repaired today: {len(rows)}"] + [f"- {r['file']}: {r['status']} {r['matched_pct']}%" for r in rows]
except Exception as e:
    lines += ["", f"(could not read timestamp_fix.csv: {e})"]
with open(os.path.join(AUTO_DIR, "daily_done.md"), "w", encoding="utf-8") as f:
    f.write("\\n".join(lines) + "\\n")
print("\\n".join(lines))
print("\\n✓ Finished. Now run the transcription notebook (v2.5) as usual.")"""

nb = nbf.v4.new_notebook()
nb.cells = [nbf.v4.new_markdown_cell(intro)] + [nbf.v4.new_code_cell(c) for c in (c1, c2, c3, c4, c5, c6, c7, c8)]
nb.metadata = {"colab": {"provenance": [], "name": "Wifaq 1448 — Daily.ipynb"},
               "accelerator": "GPU", "kernelspec": {"name": "python3", "display_name": "Python 3"},
               "language_info": {"name": "python"}}
nbf.write(nb, "Wifaq_1448_Daily.ipynb")
compile(c2 + "\n" + c4 + "\n" + c8, "cells", "exec")
compile(retx, "retx_core", "exec")
print("written + compiles")
