# @title Wifaq 1448 · Drive IDs + missing transcripts (one cell, run it as it is)
# ─────────────────────────────────────────────────────────────────────────────
# What this does, in order:
#   1. Connects your Google Drive.
#   2. Lists every recording in the سابعہ vault and input_audio.
#   3. Saves  My Drive/Wifaq 1448/recording_ids.csv  — each recording with its Drive file ID,
#      so the card page can show "Download" and "Open in Drive" buttons for each lesson.
#   4. Refreshes My Drive/Wifaq 1448/recordings_inventory.csv.
#   5. Transcribes the recordings that were skipped because another file had the same name
#      (e.g. "2025-04-20 … الجنايات.mp4" next to the .m4a). Nothing already transcribed is redone.
# Safe to stop and run again. Needs the GEMINI_API_KEY secret only for step 5.
# ─────────────────────────────────────────────────────────────────────────────

# ======================= SETTINGS (change only these) ========================
DRIVE = "/content/drive/MyDrive"
SOURCE_FOLDERS = [f"{DRIVE}/سابعہ", f"{DRIVE}/input_audio"]
OUT_DIR = f"{DRIVE}/Wifaq 1448"

# Which recordings to transcribe in step 5:
#   "same-name"  → only files skipped because of the name clash (safe while another batch is running)
#   "missing"    → every untranscribed recording of the books below (don't run two batches at once)
#   "none"       → only make the CSV files, transcribe nothing
TRANSCRIBE = "same-name"
BOOKS = ["ہدایہ جلد رابع"]          # used by "missing"; add e.g. "ہدایہ جلد ثالث"
MODEL = "gemini-3.8-flash"           # or "gemini-flash-latest"
CHUNK_MINUTES = 15
# =============================================================================

import os, re, csv, glob, time, shutil, subprocess, datetime, unicodedata, importlib
from concurrent.futures import ThreadPoolExecutor

from google.colab import drive
drive.mount("/content/drive")

AUDIO_EXT = {".mp3", ".m4a", ".mp4", ".wav", ".ogg", ".opus", ".aac", ".amr",
             ".webm", ".3gp", ".flac", ".mkv", ".mov", ".wma"}


# ---------------------------------------------------------------- names and books
def norm(s):
    """Fold Arabic/Urdu letter variants so folder and file names match reliably."""
    s = unicodedata.normalize("NFC", s or "")
    table = str.maketrans({"ي": "ی", "ى": "ی", "ك": "ک", "ه": "ہ", "ة": "ہ", "ۃ": "ہ", "ۀ": "ہ", "ە": "ہ",
                           "أ": "ا", "إ": "ا", "آ": "ا", "ٰ": "", "ً": "", "ٌ": "", "ٍ": "",
                           "َ": "", "ُ": "", "ِ": "", "ّ": "", "ْ": "", "ـ": ""})
    return s.translate(table).lower()


def guess_book(path):
    p = norm(path)
    if "ہدایہ" in p or "hidaya" in p or "hedaya" in p:
        if "رابع" in p or "4" in os.path.basename(os.path.dirname(p)):
            return "ہدایہ جلد رابع"
        if "ثالث" in p:
            return "ہدایہ جلد ثالث"
        return ""
    if "مشکاہ" in p or "مشکوہ" in p or "مشکات" in p or "mishkat" in p:
        if "دوم" in p or "ثانی" in p or "الثانی" in p:
            return "مشکوٰۃ المصابیح جلد دوم"
        if "اول" in p or "الاول" in p:
            return "مشکوٰۃ المصابیح جلد اول"
        return ""
    if "قادیان" in p or "قادیانت" in p:
        return "آئینہ قادیانیت"
    if "بیضاوی" in p or "baidawi" in p or "baydawi" in p:
        return "بیضاوی (ربع پارہ اول)"
    if "تبیان" in p:
        return "التبیان فی علوم القرآن"
    if "نخبہ" in p or "نخبت" in p or "نزہہ النظر" in p:
        return "شرح نخبۃ الفکر"
    if "تیسیر" in p or "تیسیسر" in p or "مصطلح" in p:
        return "تیسیر مصطلح الحدیث"
    return ""


def resolve(folder):
    """Find the folder even if the shortcut's name is spelled slightly differently."""
    if os.path.isdir(folder):
        return folder
    parent, name = os.path.split(folder)
    if os.path.isdir(parent):
        for entry in os.listdir(parent):
            if norm(entry).strip() == norm(name).strip():
                return os.path.join(parent, entry)
    return folder


def ffprobe_minutes(path):
    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                              "-of", "default=nw=1:nk=1", path],
                             capture_output=True, text=True, timeout=180).stdout.strip()
        return round(float(out) / 60, 1)
    except Exception:
        return ""


def scan(folders):
    rows = []
    for root in folders:
        if not os.path.isdir(root):
            print(f"⚠ Folder not found, skipped: {root}")
            continue
        for dirpath, _, files in os.walk(root):
            for fn in sorted(files):
                if os.path.splitext(fn)[1].lower() not in AUDIO_EXT:
                    continue
                full = os.path.join(dirpath, fn)
                m = re.match(r"(\d{4}-\d{2}-\d{2})\s*(.*)", os.path.splitext(fn)[0])
                rows.append({"path": full, "file": fn,
                             "date": m.group(1) if m else "",
                             "topic": (m.group(2) if m else os.path.splitext(fn)[0]).strip(),
                             "book": guess_book(os.path.relpath(full, os.path.dirname(root))),
                             "size_mb": round(os.path.getsize(full) / 1e6, 1)})
    with ThreadPoolExecutor(8) as ex:                      # durations, 8 files at a time
        for r, mins in zip(rows, ex.map(lambda r: ffprobe_minutes(r["path"]), rows)):
            r["minutes"] = mins
    rows.sort(key=lambda r: (r["book"] or "~", r["date"] or "9999", r["file"]))
    counter = {}
    for r in rows:
        counter[r["book"]] = counter.get(r["book"], 0) + 1
        r["lesson"] = counter[r["book"]] if r["book"] else ""
    return rows


# ---------------------------------------------------------------- transcript file names
def transcript_path(out_dir, row):
    """'<name>.md' as before; if another recording already owns that name
    (same name, different extension), this one becomes '<name> (mp4).md'."""
    src = row["path"]
    stem, ext = os.path.splitext(os.path.basename(src))
    base = os.path.join(out_dir, "transcripts", row["book"] or "نامعلوم")
    plain = os.path.join(base, stem + ".md")
    tagged = os.path.join(base, f"{stem} ({ext.lstrip('.').lower()}).md")
    if os.path.exists(plain):
        with open(plain, encoding="utf-8", errors="ignore") as f:
            head = f.read(3000)
        return plain if os.path.basename(src) in head else tagged
    sibs = sorted(p for p in glob.glob(glob.escape(os.path.join(os.path.dirname(src), stem)) + ".*")
                  if os.path.splitext(p)[1].lower() in AUDIO_EXT)
    return plain if (not sibs or sibs[0] == src) else tagged


# ---------------------------------------------------------------- Drive file IDs
def xattr_id(path):
    try:
        return os.getxattr(path, "user.drive.id").decode().strip()
    except Exception:
        pass
    for cmd in (["xattr", "-p", "user.drive.id", path],
                ["getfattr", "--only-values", "-n", "user.drive.id", path]):
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=20).stdout.strip()
            if out:
                return out
        except Exception:
            pass
    return ""


def api_ids(rows_without_id):
    """Fallback: ask the Drive API, matching each file by name and size."""
    from google.colab import auth
    from googleapiclient.discovery import build
    auth.authenticate_user()
    svc = build("drive", "v3", cache_discovery=False)
    found = {}
    for r in rows_without_id:
        q = "name = '{}' and trashed = false".format(r["file"].replace("\\", "\\\\").replace("'", "\\'"))
        try:
            res = svc.files().list(q=q, fields="files(id,size)", pageSize=10,
                                   includeItemsFromAllDrives=True, supportsAllDrives=True).execute()
        except Exception as e:
            print("  Drive API error:", str(e)[:150])
            continue
        size = os.path.getsize(r["path"])
        hits = res.get("files", [])
        same = [h for h in hits if str(h.get("size")) == str(size)] or hits
        if same:
            found[r["path"]] = same[0]["id"]
    return found


# ---------------------------------------------------------------- transcription
TS = re.compile(r"\[(?:(\d{1,2}):)?(\d{1,2}):(\d{2})\]")


def fmt_hms(sec):
    sec = int(round(sec))
    return f"{sec // 3600}:{(sec % 3600) // 60:02d}:{sec % 60:02d}"


def shift_timestamps(text, offset_sec):
    def rep(m):
        h = int(m.group(1) or 0)
        return "[" + fmt_hms(offset_sec + h * 3600 + int(m.group(2)) * 60 + int(m.group(3))) + "]"
    return TS.sub(rep, text)


def split_audio(src, work_dir, chunk_min):
    if os.path.isdir(work_dir):
        shutil.rmtree(work_dir)
    os.makedirs(work_dir)
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", src, "-vn",
                    "-ac", "1", "-ar", "16000", "-c:a", "libmp3lame", "-b:a", "32k",
                    "-f", "segment", "-segment_time", str(chunk_min * 60), "-reset_timestamps", "1",
                    os.path.join(work_dir, "chunk_%03d.mp3")], check=True)
    return sorted(glob.glob(os.path.join(work_dir, "chunk_*.mp3")))


PROMPT = """This is part {part} of {parts} of a recorded dars in a Pakistani madrasa. The teacher explains in Urdu and reads passages of the Arabic book "{book}" aloud.

Transcribe this clip verbatim.
- Urdu in Urdu script, Arabic in Arabic script, exactly as spoken. Do not translate, summarise or correct anything.
- Start a new line with a timestamp [mm:ss], measured from the start of THIS clip, at least every 30 seconds and every time the teacher starts reading Arabic.
- Put ع: right after the timestamp on every line where the teacher reads the book's Arabic text aloud.
- If a word is unclear, write [؟] instead of guessing.
- If the teacher mentions a page number, keep it exactly.
- Output only the transcript lines, nothing else."""


def transcribe(client, row, model, chunk_min):
    from google.genai import types
    dest = transcript_path(OUT_DIR, row)
    if os.path.exists(dest):
        print("  ✓ already done")
        return dest
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    chunks = split_audio(row["path"], "/content/work", chunk_min)
    parts = []
    for i, ch in enumerate(chunks):
        text = None
        for attempt in range(6):
            try:
                up = client.files.upload(file=ch)
                for _ in range(60):
                    if getattr(getattr(up, "state", None), "name", "ACTIVE") != "PROCESSING":
                        break
                    time.sleep(3)
                    up = client.files.get(name=up.name)
                resp = client.models.generate_content(
                    model=model,
                    contents=[PROMPT.format(part=i + 1, parts=len(chunks), book=row["book"] or "درس نظامی"), up],
                    config=types.GenerateContentConfig(
                        temperature=0.0, max_output_tokens=65536,
                        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)))
                text = (resp.text or "").strip()
                first = TS.search(text)              # drop any chatter before the first timestamp
                if first:
                    text = text[first.start():]
                try:
                    client.files.delete(name=up.name)
                except Exception:
                    pass
                break
            except Exception as e:
                msg = str(e)
                if any(code in msg[:40] for code in ("400", "401", "403", "404")):
                    raise RuntimeError(f"Gemini refused the request (not retrying): {msg[:300]}")
                wait = min(60 * (attempt + 1), 300)
                print(f"  … part {i + 1}: {msg[:120]} — retrying in {wait}s")
                time.sleep(wait)
        parts.append(shift_timestamps(text or f"[⚠ حصہ {i + 1} کا ٹرانسکرپٹ نہیں بن سکا]", i * chunk_min * 60))
        print(f"  part {i + 1}/{len(chunks)} done")
    header = (f"# {row['file']}\n\n- کتاب: {row['book'] or '—'}\n- سبق: {row['lesson']}\n"
              f"- تاریخ: {row['date'] or '—'}\n- موضوع: {row['topic'] or '—'}\n- دورانیہ: {row['minutes']} منٹ\n"
              f"- ماڈل: {model}\n- حصے: {len(chunks)}\n- بنایا: {datetime.date.today().isoformat()}\n"
              f"- راستہ: {row['path']}\n\n---\n\n")
    tmp = dest + ".part"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(header + "\n\n".join(parts) + "\n")
    os.replace(tmp, dest)
    print("  ✓ saved:", os.path.relpath(dest, DRIVE))
    return dest


# =============================================================================
# 1–2 · find the recordings
SOURCE_FOLDERS = [resolve(f) for f in SOURCE_FOLDERS]
missing_folders = [f for f in SOURCE_FOLDERS if not os.path.isdir(f)]
if missing_folders:
    print("⚠ Not found:", missing_folders)
    print("  Top of My Drive has:", sorted(os.listdir(DRIVE))[:40])
os.makedirs(OUT_DIR, exist_ok=True)
print("Listing recordings and reading their lengths (a few minutes)…")
rows = scan(SOURCE_FOLDERS)
print(f"✓ {len(rows)} recordings found")

# 3 · Drive IDs
ids = {r["path"]: xattr_id(r["path"]) for r in rows}
without = [r for r in rows if not ids[r["path"]]]
if without:
    print(f"{len(without)} files had no ID from the Drive mount; asking the Drive API (allow access if asked)…")
    ids.update(api_ids(without))
ids_csv = os.path.join(OUT_DIR, "recording_ids.csv")
with open(ids_csv, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["file", "book", "lesson", "date", "minutes", "size_mb", "drive_id", "transcript", "path"])
    for r in rows:
        tp = transcript_path(OUT_DIR, r)
        w.writerow([r["file"], r["book"], r["lesson"], r["date"], r["minutes"], r["size_mb"],
                    ids.get(r["path"], ""), os.path.basename(tp) if os.path.exists(tp) else "", r["path"]])
n_ids = sum(1 for r in rows if ids.get(r["path"]))
print(f"✓ saved {os.path.relpath(ids_csv, DRIVE)} — {n_ids} of {len(rows)} recordings have a Drive ID")

# 4 · inventory (same columns as the tracker's ریکارڈنگز tab)
inv_csv = os.path.join(OUT_DIR, "recordings_inventory.csv")
with open(inv_csv, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["فائل کا نام", "کتاب", "سبق #", "استاد", "دورانیہ (منٹ)", "سے صفحہ", "تک صفحہ",
                "ٹرانسکرپٹ", "تمہیدی کارڈ", "نوٹ", "تاریخ", "راستہ"])
    for r in rows:
        done = "ہاں" if os.path.exists(transcript_path(OUT_DIR, r)) else "نہیں"
        w.writerow([r["file"], r["book"], r["lesson"], "", r["minutes"], "", "", done, "نہیں",
                    r["topic"], r["date"], r["path"]])
print(f"✓ refreshed {os.path.relpath(inv_csv, DRIVE)}")

# 5 · what's missing, and transcribe
groups = {}
for r in rows:
    groups.setdefault((r["book"], os.path.splitext(r["file"])[0]), []).append(r)
same_name = [r for rs in groups.values() if len(rs) > 1 for r in rs
             if not os.path.exists(transcript_path(OUT_DIR, r))]
missing = [r for r in rows if r["book"] in BOOKS and not os.path.exists(transcript_path(OUT_DIR, r))]
print(f"\nNot yet transcribed in {', '.join(BOOKS)}: {len(missing)}")
for r in missing:
    print(f"  · {r['file']} ({r['minutes']} min)")

todo = {"same-name": same_name, "missing": missing}.get(TRANSCRIBE, [])
if todo:
    from google.colab import userdata
    try:
        from google import genai
    except ImportError:
        subprocess.run(["pip", "-q", "install", "google-genai"], check=True)
        importlib.invalidate_caches()
        from google import genai
    client = genai.Client(api_key=userdata.get("GEMINI_API_KEY"))
    print(f"\nTranscribing {len(todo)} recording(s) with {MODEL}:")
    for n, r in enumerate(todo, 1):
        print(f"[{n}/{len(todo)}] {r['file']}")
        try:
            transcribe(client, r, MODEL, CHUNK_MINUTES)
        except Exception as e:
            print("  ✗ skipped:", str(e)[:200])
else:
    print("\nNothing to transcribe with TRANSCRIBE =", repr(TRANSCRIBE))
print("\n✓ All done. Tell Claude: recording_ids.csv is ready.")
