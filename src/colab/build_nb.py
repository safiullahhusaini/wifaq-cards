import nbformat as nbf

core = open("core.py", encoding="utf-8").read()

md0 = """# Wifaq 1448 — recordings pipeline

This notebook does two jobs, entirely inside your Google account:

1. **Lists every recording** in your folders (including the shared `سابعہ` vault) with its book, date and length, and saves `recordings_inventory.csv` to `My Drive/Wifaq 1448/`. The columns match the tracker's ریکارڈنگز tab, so you can paste it straight in.
2. **Transcribes recordings with Gemini**, 15 minutes at a time, with timestamps for the whole lesson. Each transcript is saved as a `.md` file in `My Drive/Wifaq 1448/transcripts/<book>/`. Claude reads these through your Drive connection and turns them into تمہیدی کارڈز and the page → audio index.

It is safe to stop and re-run: files already transcribed are skipped.

### One-time setup (5 minutes)
1. **Add the vault to My Drive:** open the shared `سابعہ` folder in Google Drive → right-click → **Organize → Add shortcut** → **My Drive**. (Colab can only see shared folders through a shortcut.)
2. **Get a Gemini API key:** go to [aistudio.google.com](https://aistudio.google.com) → **Get API key** → create a key.
3. **Store the key in Colab:** click the 🔑 **Secrets** icon in the left sidebar → **Add new secret** → name `GEMINI_API_KEY`, paste the key, and switch on **Notebook access**.

Then run the cells in order. No GPU is needed; a normal CPU runtime is fine."""

c1 = """# @title 1 · Connect Drive and install the Gemini library
from google.colab import drive
drive.mount('/content/drive')
try:
    import google.genai  # Colab usually has it already
except ImportError:
    !pip -q install google-genai
print("✓ ready")"""

c2 = """# @title 2 · Settings (edit the folder list if your recordings live elsewhere)
import os
DRIVE = "/content/drive/MyDrive"

SOURCE_FOLDERS = [
    f"{DRIVE}/سابعہ",        # the shared vault (after adding the shortcut)
    f"{DRIVE}/input_audio",   # your own recordings
    # f"{DRIVE}/another folder",
]
OUT_DIR = f"{DRIVE}/Wifaq 1448"

# gemini-2.5-pro is closed to new API users. Use the newest Flash from the list this cell prints;
# "gemini-flash-latest" always points at the current one.
MODEL = "gemini-3.8-flash"
CHUNK_MINUTES = 15

from google.colab import userdata
from google import genai
client = genai.Client(api_key=userdata.get("GEMINI_API_KEY"))

names = [m.name.replace("models/", "") for m in client.models.list()
         if "generateContent" in (getattr(m, "supported_actions", None) or ["generateContent"])]
print("Models your key can use:", ", ".join(n for n in names if n.startswith("gemini")))
print("Using:", MODEL)"""

c3 = "# @title 3 · Pipeline functions (run once, no need to edit)\n" + core + """

# Find the vault shortcut even if its name is spelled slightly differently.
def _resolve(folder):
    if os.path.isdir(folder):
        return folder
    parent, name = os.path.split(folder)
    if os.path.isdir(parent):
        for entry in os.listdir(parent):
            if norm(entry).strip() == norm(name).strip():
                return os.path.join(parent, entry)
    return folder

SOURCE_FOLDERS = [_resolve(f) for f in SOURCE_FOLDERS]
missing = [f for f in SOURCE_FOLDERS if not os.path.isdir(f)]
if missing:
    print("⚠ Not found:", missing)
    print("  Top of My Drive has:", sorted(os.listdir(DRIVE))[:40])
    print("  Did you add the سابعہ shortcut to My Drive (setup step 1)?")
else:
    print("✓ all folders found")"""

c4 = """# @title 4 · Step 1: list every recording and save the inventory
rows = scan(SOURCE_FOLDERS)
print(f"{len(rows)} recordings found\\n")
summarize(rows)
inv = write_inventory(rows, OUT_DIR)
print("\\n✓ Inventory saved to", inv)
print("Rows with an empty کتاب column need the book typed in by hand.")"""

c5 = """# @title 5 · Step 2: pilot — transcribe ONE recording
# Pick the file by part of its name. BOOK fills in the book when the folder name doesn't say it.
PILOT_NAME_CONTAINS = "fiqh july11"
BOOK = "ہدایہ جلد ثالث"   # or "" to keep the guessed book

pick = [r for r in rows if PILOT_NAME_CONTAINS in r["file"]]
if not pick:
    print("No file matches", repr(PILOT_NAME_CONTAINS))
else:
    row = dict(pick[0])
    if BOOK:
        row["book"] = BOOK
    print("Transcribing:", row["file"], f"({row['minutes']} min) as", row["book"] or "unknown book")
    path = transcribe_file(client, row, OUT_DIR, MODEL, CHUNK_MINUTES)
    print("\\nFirst lines:\\n")
    print(open(path, encoding="utf-8").read()[:1500])"""

c6 = """# @title 6 · Step 3: transcribe a whole book (safe to stop and re-run)
BOOKS_TO_DO = ["ہدایہ جلد ثالث", "ہدایہ جلد رابع", "مشکوٰۃ المصابیح جلد اول", "مشکوٰۃ المصابیح جلد دوم",
               "بیضاوی (ربع پارہ اول)", "تیسیر مصطلح الحدیث", "التبیان فی علوم القرآن"]

ROUND_ROBIN = True   # True: lesson 1 of every book, then lesson 2 of every book, ... so each book's opening is ready first

todo = [r for r in rows if r["book"] in BOOKS_TO_DO]
if ROUND_ROBIN:
    todo.sort(key=lambda r: (r["lesson"] or 0, BOOKS_TO_DO.index(r["book"])))
else:
    todo.sort(key=lambda r: (BOOKS_TO_DO.index(r["book"]), r["lesson"] or 0))
print(len(todo), "recordings queued")
for n, r in enumerate(todo, 1):
    print(f"\\n[{n}/{len(todo)}] {r['book']} · lesson {r['lesson']} · {r['file']}")
    try:
        transcribe_file(client, r, OUT_DIR, MODEL, CHUNK_MINUTES)
    except Exception as e:
        print("  ✗ skipped:", str(e)[:200])
write_inventory(rows, OUT_DIR)
print("\\n✓ Done. Inventory refreshed with the ٹرانسکرپٹ column updated.")"""

nb = nbf.v4.new_notebook()
nb.cells = [nbf.v4.new_markdown_cell(md0), nbf.v4.new_code_cell(c1), nbf.v4.new_code_cell(c2),
            nbf.v4.new_code_cell(c3), nbf.v4.new_code_cell(c4), nbf.v4.new_code_cell(c5),
            nbf.v4.new_code_cell(c6)]
nb.metadata = {"colab": {"provenance": [], "name": "Wifaq 1448 — Recordings Pipeline.ipynb"},
               "kernelspec": {"name": "python3", "display_name": "Python 3"},
               "language_info": {"name": "python"}}
nbf.write(nb, "Wifaq_1448_Recordings_Pipeline.ipynb")
print("written")
