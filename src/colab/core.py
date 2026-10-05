# === Wifaq 1448 recordings pipeline: core functions ===
import os, re, csv, json, time, glob, shutil, subprocess, datetime, unicodedata

AUDIO_EXT = {".mp3", ".m4a", ".mp4", ".wav", ".ogg", ".opus", ".aac", ".amr",
             ".webm", ".3gp", ".flac", ".mkv", ".mov", ".wma"}

BOOKS = [
    "التبیان فی علوم القرآن", "تیسیر مصطلح الحدیث", "شرح نخبۃ الفکر", "آئینہ قادیانیت",
    "بیضاوی (ربع پارہ اول)", "مشکوٰۃ المصابیح جلد اول", "مشکوٰۃ المصابیح جلد دوم",
    "ہدایہ جلد ثالث", "ہدایہ جلد رابع",
]


def norm(s):
    """Fold Arabic/Urdu letter variants so folder and file names match reliably."""
    s = unicodedata.normalize("NFC", s or "")
    table = str.maketrans({"ي": "ی", "ى": "ی", "ك": "ک", "ه": "ہ", "ة": "ہ", "ۃ": "ہ", "ۀ": "ہ", "ە": "ہ",
                           "أ": "ا", "إ": "ا", "آ": "ا", "ٰ": "", "ً": "", "ٌ": "", "ٍ": "",
                           "َ": "", "ُ": "", "ِ": "", "ّ": "", "ْ": "", "ـ": ""})
    return s.translate(table).lower()


def guess_book(path):
    """Best guess of the syllabus book from the folder and file name; '' when unsure."""
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


def ffprobe_minutes(path):
    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                              "-of", "default=nw=1:nk=1", path],
                             capture_output=True, text=True, timeout=120).stdout.strip()
        return round(float(out) / 60, 1)
    except Exception:
        return ""


def scan(folders):
    """Walk the folders and return one row per audio/video file."""
    rows = []
    for root_folder in folders:
        if not os.path.isdir(root_folder):
            print(f"⚠ Folder not found, skipped: {root_folder}")
            continue
        for dirpath, _, files in os.walk(root_folder):
            for fn in sorted(files):
                if os.path.splitext(fn)[1].lower() not in AUDIO_EXT:
                    continue
                full = os.path.join(dirpath, fn)
                m = re.match(r"(\d{4}-\d{2}-\d{2})\s*(.*)", os.path.splitext(fn)[0])
                rows.append({
                    "path": full,
                    "file": fn,
                    "date": m.group(1) if m else "",
                    "topic": (m.group(2) if m else os.path.splitext(fn)[0]).strip(),
                    "book": guess_book(os.path.relpath(full, os.path.dirname(root_folder))),
                    "minutes": ffprobe_minutes(full),
                    "size_mb": round(os.path.getsize(full) / 1e6, 1),
                })
    # lesson number = order by date (then name) inside each book
    rows.sort(key=lambda r: (r["book"] or "~", r["date"] or "9999", r["file"]))
    counter = {}
    for r in rows:
        counter[r["book"]] = counter.get(r["book"], 0) + 1
        r["lesson"] = counter[r["book"]] if r["book"] else ""
    return rows


TRACKER_HEADERS = ["فائل کا نام", "کتاب", "سبق #", "استاد", "دورانیہ (منٹ)", "سے صفحہ",
                   "تک صفحہ", "ٹرانسکرپٹ", "تمہیدی کارڈ", "نوٹ", "تاریخ", "راستہ"]


def transcript_path(out_dir, row):
    sub = row["book"] or "نامعلوم"
    return os.path.join(out_dir, "transcripts", sub, os.path.splitext(row["file"])[0] + ".md")


def write_inventory(rows, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "recordings_inventory.csv")
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(TRACKER_HEADERS)
        for r in rows:
            done = "ہاں" if os.path.exists(transcript_path(out_dir, r)) else "نہیں"
            w.writerow([r["file"], r["book"], r["lesson"], "", r["minutes"], "", "", done, "نہیں",
                        r["topic"], r["date"], r["path"]])
    return path


def summarize(rows):
    by = {}
    for r in rows:
        b = r["book"] or "کتاب نامعلوم — ہاتھ سے لکھیں"
        n, mins = by.get(b, (0, 0.0))
        by[b] = (n + 1, mins + (r["minutes"] or 0))
    for b, (n, mins) in sorted(by.items()):
        print(f"{b:40s} {n:4d} files  {mins / 60:6.1f} hours")
    return by


# ---------------------------------------------------------------- timestamps
TS = re.compile(r"\[(?:(\d{1,2}):)?(\d{1,2}):(\d{2})\]")


def fmt_hms(sec):
    sec = int(round(sec))
    return f"{sec // 3600}:{(sec % 3600) // 60:02d}:{sec % 60:02d}"


def shift_timestamps(text, offset_sec):
    """Turn clip-relative [mm:ss] / [h:mm:ss] into whole-recording [h:mm:ss]."""
    def rep(m):
        h = int(m.group(1) or 0)
        return "[" + fmt_hms(offset_sec + h * 3600 + int(m.group(2)) * 60 + int(m.group(3))) + "]"
    return TS.sub(rep, text)


def split_audio(src, work_dir, chunk_min):
    """Mono 16 kHz 32 kbps mp3 chunks: small uploads, plenty for speech."""
    if os.path.isdir(work_dir):
        shutil.rmtree(work_dir)
    os.makedirs(work_dir)
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", src, "-vn",
           "-ac", "1", "-ar", "16000", "-c:a", "libmp3lame", "-b:a", "32k",
           "-f", "segment", "-segment_time", str(chunk_min * 60), "-reset_timestamps", "1",
           os.path.join(work_dir, "chunk_%03d.mp3")]
    subprocess.run(cmd, check=True)
    return sorted(glob.glob(os.path.join(work_dir, "chunk_*.mp3")))


TRANSCRIBE_PROMPT = """This is part {part} of {parts} of a recorded dars in a Pakistani madrasa. The teacher explains in Urdu and reads passages of the Arabic book "{book}" aloud.

Transcribe this clip verbatim.
- Urdu in Urdu script, Arabic in Arabic script, exactly as spoken. Do not translate, summarise or correct anything.
- Start a new line with a timestamp [mm:ss], measured from the start of THIS clip, at least every 30 seconds and every time the teacher starts reading Arabic.
- Put ع: right after the timestamp on every line where the teacher reads the book's Arabic text aloud.
- If a word is unclear, write [؟] instead of guessing.
- If the teacher mentions a page number, keep it exactly.
- Output only the transcript lines, nothing else."""


def transcribe_file(client, row, out_dir, model, chunk_min=15, max_retries=6, log=print):
    """Transcribe one recording to Markdown in Drive. Skips files already done."""
    from google.genai import types
    dest = transcript_path(out_dir, row)
    if os.path.exists(dest):
        log(f"✓ already done: {row['file']}")
        return dest
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    chunks = split_audio(row["path"], "/content/work" if os.path.isdir("/content") else "/tmp/wifaq_work", chunk_min)
    parts = []
    for i, ch in enumerate(chunks):
        prompt = TRANSCRIBE_PROMPT.format(part=i + 1, parts=len(chunks), book=row["book"] or "درس نظامی")
        text = None
        for attempt in range(max_retries):
            try:
                up = client.files.upload(file=ch)
                for _ in range(60):
                    state = getattr(getattr(up, "state", None), "name", "ACTIVE")
                    if state != "PROCESSING":
                        break
                    time.sleep(3)
                    up = client.files.get(name=up.name)
                resp = client.models.generate_content(
                    model=model, contents=[prompt, up],
                    config=types.GenerateContentConfig(
                        temperature=0.0, max_output_tokens=65536,
                        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)))
                text = (resp.text or "").strip()
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
                log(f"  … part {i + 1}: {str(e)[:120]} — retrying in {wait}s")
                time.sleep(wait)
        if not text:
            text = f"[⚠ حصہ {i + 1} کا ٹرانسکرپٹ نہیں بن سکا]"
        parts.append(shift_timestamps(text, i * chunk_min * 60))
        log(f"  part {i + 1}/{len(chunks)} done")
    header = (f"# {row['file']}\n\n"
              f"- کتاب: {row['book'] or '—'}\n- تاریخ: {row['date'] or '—'}\n- موضوع: {row['topic'] or '—'}\n"
              f"- دورانیہ: {row['minutes']} منٹ\n- ماڈل: {model}\n"
              f"- بنایا: {datetime.date.today().isoformat()}\n- راستہ: {row['path']}\n\n---\n\n")
    tmp = dest + ".part"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(header + "\n\n".join(parts) + "\n")
    os.replace(tmp, dest)
    log(f"✓ saved: {dest}")
    return dest
