# Builds "Wifaq 1448 — Daily.ipynb": one notebook the user runs once a day (T4 GPU, Run all).
# It does what Claude's scheduled runs put in Drive `Wifaq 1448/automation/daily_config.json`:
#   1. re-transcribes the transcripts in `redo` (Gemini 3.8 / 3.7 / 3.6 Flash, same as cell_retranscribe.py),
#   2. repairs timestamps of every unrepaired transcript in `repair_books` (Timestamp Repair v3 code),
#   3. makes Opus copies for `opus_books` (cell 7 code),
#   4. writes `automation/daily_done.md` so the next Claude run knows what happened,
#   5. copies what the runs need to the private repo wifaq-data (src/auto/DATA_REPO.md).
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
5. Copies what Claude's night runs need (transcripts, book text, status files, Opus audio) to your **private** GitHub repo `wifaq-data`, so the runs don't have to read Drive. Needs the Colab secret `GITHUB_DATA_TOKEN`; without it this step is skipped. Setup: `src/auto/DATA_REPO.md` in the wifaq-cards repo.

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

# Claude's night runs keep the to-do in the private repo wifaq-data; Drive is the fallback.
import shutil, subprocess
DATA_REPO = "safiullahhusaini/wifaq-data"
DATA_DIR = "/content/wifaq-data"

def _secret(name):
    try:
        return userdata.get(name)
    except Exception:
        return None

DATA_TOKEN = _secret("GITHUB_DATA_TOKEN")
DATA_OK = False
if DATA_TOKEN:
    shutil.rmtree(DATA_DIR, ignore_errors=True)
    r = subprocess.run(["git", "clone", "-q", "--depth", "1",
                        f"https://safiullahhusaini:{DATA_TOKEN}@github.com/{DATA_REPO}.git", DATA_DIR],
                       capture_output=True, text=True)
    DATA_OK = r.returncode == 0
    if DATA_OK:
        for k, v in (("user.name", "Wifaq Daily"), ("user.email", "safiullahhusaini@users.noreply.github.com")):
            subprocess.run(["git", "-C", DATA_DIR, "config", k, v])
        print("wifaq-data opened.")
    else:
        print("Could not open wifaq-data (step 9 will be skipped):", r.stderr.replace(DATA_TOKEN, "***").strip()[-300:])

DATA_CFG = os.path.join(DATA_DIR, "automation", "daily_config.json")
DRIVE_CFG = os.path.join(AUTO_DIR, "daily_config.json")
CFG_FROM = None
for path, label in ((DATA_CFG, "wifaq-data"), (DRIVE_CFG, "Drive")):
    if (DATA_OK or label == "Drive") and os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            CONFIG.update(json.load(f))
        CFG_FROM = label
        break
if CFG_FROM == "wifaq-data":
    shutil.copyfile(DATA_CFG, DRIVE_CFG)   # keep the Drive copy current
if CFG_FROM:
    print(f"To-do from {CFG_FROM}, updated by Claude:", CONFIG.get("updated", "?"))
else:
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
print("\\n".join(lines))"""

c9 = """# @title 9 · Copy to wifaq-data for Claude's night runs (skipped without the GITHUB_DATA_TOKEN secret)
import os, shutil, subprocess, datetime

TEXT_EXT = (".md", ".txt", ".csv", ".json")

def _git(*args, check=True):
    r = subprocess.run(["git", "-C", DATA_DIR, *args], capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(r.stderr.replace(DATA_TOKEN or "\\0", "***").strip()[-400:])
    return r

def _mirror(src, dst, *, delete=False, exts=None, max_mb=50, keep=()):
    # Copy the tree src -> dst. Skips folders starting with "_"; an .ogg already in dst
    # with the same size is not copied again. delete=True removes dst files that src no longer has.
    seen, copied = set(), 0
    if not os.path.isdir(src):
        return 0
    for root, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if not d.startswith("_")]
        for fn in files:
            if exts and not fn.lower().endswith(exts):
                continue
            s = os.path.join(root, fn)
            rel = os.path.relpath(s, src)
            seen.add(rel)
            if rel in keep:
                continue
            try:
                size = os.path.getsize(s)
            except OSError:
                continue
            if size > max_mb * 1e6:
                continue
            d = os.path.join(dst, rel)
            if fn.lower().endswith(".ogg") and os.path.exists(d) and os.path.getsize(d) == size:
                continue
            os.makedirs(os.path.dirname(d), exist_ok=True)
            shutil.copyfile(s, d)
            copied += 1
    if delete and os.path.isdir(dst):
        for root, dirs, files in os.walk(dst):
            for fn in files:
                rel = os.path.relpath(os.path.join(root, fn), dst)
                if rel not in seen and rel not in keep:
                    os.remove(os.path.join(root, fn))
    return copied

if not DATA_OK:
    print("Skipped: wifaq-data isn't set up (see src/auto/DATA_REPO.md in the wifaq-cards repo).")
else:
    if _git("rev-parse", "HEAD", check=False).returncode != 0:      # repo created without a README
        _git("checkout", "-q", "-b", "main")
    counts = {}
    counts["transcripts"] = _mirror(TX_DIR, f"{DATA_DIR}/transcripts", delete=True, exts=TEXT_EXT)
    os.makedirs(f"{DATA_DIR}/status", exist_ok=True)
    n = 0
    for fn in os.listdir(OUT_DIR):
        p = os.path.join(OUT_DIR, fn)
        if os.path.isfile(p) and fn.lower().endswith(TEXT_EXT) and os.path.getsize(p) < 50e6:
            shutil.copyfile(p, f"{DATA_DIR}/status/{fn}")
            n += 1
    counts["status"] = n
    counts["ocr"] = _mirror(f"{OUT_DIR}/Books/text", f"{DATA_DIR}/ocr", delete=True, exts=TEXT_EXT)
    audio_books = CONFIG.get("data_audio_books", CONFIG["opus_books"])
    opus_root = f"{OUT_DIR}/web_audio_opus"
    n = 0
    if os.path.exists(f"{opus_root}/index.csv"):
        os.makedirs(f"{DATA_DIR}/audio", exist_ok=True)
        shutil.copyfile(f"{opus_root}/index.csv", f"{DATA_DIR}/audio/index.csv")
    for book in audio_books:
        n += _mirror(f"{opus_root}/{book}", f"{DATA_DIR}/audio/{book}", max_mb=95)
    counts["audio"] = n
    keep = {"daily_config.json"} if os.path.exists(DATA_CFG) else set()
    counts["automation"] = _mirror(AUTO_DIR, f"{DATA_DIR}/automation", max_mb=20, keep=keep)
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5)))
    with open(f"{DATA_DIR}/SYNCED.md", "w", encoding="utf-8") as f:
        f.write(f"# Synced {now:%d %b %Y, %I:%M %p} PKT\\n\\n")
        f.write("Files copied this time: " + ", ".join(f"{k} {v}" for k, v in counts.items()) + "\\n")
        f.write(f"Audio books: {', '.join(audio_books) or 'none'}\\n")
    _git("add", "-A")
    if not _git("status", "--porcelain").stdout.strip():
        print("wifaq-data was already up to date.")
    else:
        _git("commit", "-q", "-m", f"sync {now:%d %b %Y %I:%M %p}")
        print("Pushing to wifaq-data (the first time takes several minutes) …")
        if _git("push", "-q", "origin", "HEAD:main", check=False).returncode != 0:
            _git("pull", "-q", "--rebase", "origin", "main")   # a night run pushed meanwhile
            _git("push", "-q", "origin", "HEAD:main")
        print("✓ wifaq-data updated:", ", ".join(f"{k} {v}" for k, v in counts.items()))
print("\\n✓ Finished. Now run the transcription notebook (v2.5) as usual.")"""

nb = nbf.v4.new_notebook()
nb.cells = [nbf.v4.new_markdown_cell(intro)] + [nbf.v4.new_code_cell(c) for c in (c1, c2, c3, c4, c5, c6, c7, c8, c9)]
nb.metadata = {"colab": {"provenance": [], "name": "Wifaq 1448 — Daily.ipynb"},
               "accelerator": "GPU", "kernelspec": {"name": "python3", "display_name": "Python 3"},
               "language_info": {"name": "python"}}
nbf.write(nb, "Wifaq_1448_Daily.ipynb")
compile(c2 + "\n" + c4 + "\n" + c8 + "\n" + c9, "cells", "exec")
compile(retx, "retx_core", "exec")
print("written + compiles")


# ---------------------------------------------------------------- the same code as one plain script for GitHub Actions
# (.github/workflows/daily.yml): Drive is mounted with rclone at /content/drive/MyDrive, secrets come from environment
# variables, Whisper runs on the CPU (WIFAQ_CPU_MODEL). Steps 2-9 are the notebook's cells, unchanged.
shim = """# Generated by build_daily_nb.py: Wifaq 1448 Daily for GitHub Actions. Do not edit; edit the pieces and rebuild.
import os, sys, types, json, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _env_get(name):
    # GitHub secrets cannot start with GITHUB_, so the Colab secret GITHUB_DATA_TOKEN is WIFAQ_DATA_TOKEN here
    v = os.environ.get({"GITHUB_DATA_TOKEN": "WIFAQ_DATA_TOKEN"}.get(name, name))
    if not v:
        raise KeyError(name)
    return v


userdata = types.SimpleNamespace(get=_env_get)
"""
ci_c2 = c2.replace("# @title 2 · Read today's to-do from Drive (written by Claude)\n", "")
ci_c4 = c4.replace("# @title 4 · Functions (no need to edit)\n", "").replace("\nprint('✓ ready')", "")
ci_c5 = c5.replace("# @title 5 · Re-transcribe (Gemini) — safe to stop and run again\n", "").replace("import importlib, sys\nsys.path.insert(0, \"/content\")\n", "import importlib, sys\n")
ci_over = """# Test knobs for the workflow (never set by the schedule): WIFAQ_MAX_HOURS, WIFAQ_SKIP (comma list of step numbers)
if os.environ.get("WIFAQ_MAX_HOURS"):
    MAX_HOURS = float(os.environ["WIFAQ_MAX_HOURS"])
SKIP = {s.strip() for s in os.environ.get("WIFAQ_SKIP", "").split(",") if s.strip()}
print("steps skipped by test knob:", sorted(SKIP) or "none")
"""
ci_c5 = ci_c5.replace("\nDONE_LOG = []\n", "\nDONE_LOG = []\nif '5' in SKIP:\n    CONFIG['redo'] = []\n", 1)
ci_c6 = c6.replace("run_fix()", "if '6' not in SKIP:\n    run_fix()")
ci_c7 = c7.replace("make_opus_audio()", "if '7' not in SKIP:\n    make_opus_audio()")
ci_c9 = c9.replace("if not DATA_OK:\n", "if '9' in SKIP or not DATA_OK:\n", 1)
ci_parts = [shim, ci_c2, ci_over, ci_c4, ci_c5, ci_c6, ci_c7, c8, ci_c9]
ci_parts = [p.split("\n", 1)[1] if p.startswith("# @title") else p for p in ci_parts]
script = "\n\n# " + "-" * 70 + "\n\n".join([""] + ci_parts)
open("daily_ci.py", "w", encoding="utf-8").write(script)
compile(script, "daily_ci.py", "exec")
print("daily_ci.py written + compiles")
