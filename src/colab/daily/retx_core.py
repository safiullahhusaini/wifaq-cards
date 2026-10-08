# Wifaq 1448 · re-transcription functions (shared by the Wifaq Daily notebook and, later, the GitHub pipeline).
# Made from cell_retranscribe.py (5 Oct, used for the الذبائح lessons): same prompt, same checks, same file handling.
# The caller sets OUT_DIR and TX_DIR, calls setup_lanes(get_secret), then redo(name) for each transcript file name.
import os, re, glob, time, shutil, subprocess, datetime, unicodedata
from zoneinfo import ZoneInfo
from google import genai
from google.genai import types

MODELS = ["gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.6-flash"]   # never 3.5 or 2.5 (bad timestamps)
AISTUDIO_SECRET = "GEMINI_API_KEY"
VERTEX_SECRET = "VERTEX_API_KEY"
CHUNK_MIN = 10
WORK = "/content/retx" if os.path.isdir("/content") else "/tmp/retx"
PK = ZoneInfo("Asia/Karachi")
TS_START = re.compile(r"^\s*\[(?:(\d{1,2}):)?(\d{1,2}):(\d{2})\]")
TS_ANY = re.compile(r"\[(?:(\d{1,2}):)?(\d{1,2}):(\d{2})\]")

PROMPT = """This is part {part} of {parts} of a recorded dars in a Pakistani madrasa. The teacher explains in Urdu and reads passages of the Arabic book "{book}" aloud.

Transcribe this clip verbatim.
- Urdu in Urdu script, Arabic in Arabic script, exactly as spoken. Do not translate, summarise or correct anything.
- Every line starts with a timestamp [mm:ss], measured from the start of THIS clip (which is {clip} long).
- Start a new line at every sentence boundary, every time the teacher starts or stops reading Arabic, and at least every 20 seconds. Keep lines short (one or two sentences).
- Put ع: right after the timestamp on every line where the teacher reads the book's Arabic text aloud.
- Include students' questions and the teacher's answers as they are spoken.
- If a word is unclear, write [؟] instead of guessing.
- If the teacher mentions a page number, keep it exactly.
- Output only the transcript lines, nothing else."""


def clock():
    return datetime.datetime.now(PK).strftime("%I:%M %p").lstrip("0").lower()


def say(*a):
    print(clock(), "·", *a, flush=True)


def hms(sec):
    sec = int(round(sec))
    return f"{sec // 3600}:{(sec % 3600) // 60:02d}:{sec % 60:02d}"


def mmss(sec):
    sec = int(round(sec))
    return f"{sec // 60}:{sec % 60:02d}"


def seconds(m):
    return int(m.group(1) or 0) * 3600 + int(m.group(2)) * 60 + int(m.group(3))


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                       capture_output=True, text=True)
    return float(r.stdout.strip() or 0)


def nfc(s):
    return unicodedata.normalize("NFC", s)


def find_transcript(name):
    for book_dir in sorted(glob.glob(os.path.join(TX_DIR, "*"))):
        if os.path.basename(book_dir).startswith("_") or not os.path.isdir(book_dir):
            continue
        for p in glob.glob(os.path.join(book_dir, "*.md")):
            if nfc(os.path.basename(p)) == nfc(name):
                return p
    return None


def split_header(text):
    lines = text.split("\n")
    for i, l in enumerate(lines[:80]):
        if l.strip() == "---":
            return lines[:i], lines[i + 1:]
    return [], lines


def field(header_lines, key):
    for l in header_lines:
        l = l.replace("\\", "").strip()
        if l.startswith("- ") and ":" in l and l[2:].split(":", 1)[0].strip() == key:
            return l.split(":", 1)[1].strip()
    return ""


def split_audio(src):
    shutil.rmtree(WORK, ignore_errors=True)
    os.makedirs(WORK)
    local = os.path.join(WORK, "src" + os.path.splitext(src)[1])
    shutil.copyfile(src, local)                       # one read from Drive, then ffmpeg works locally
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", local, "-vn",
                    "-ac", "1", "-ar", "16000", "-c:a", "libmp3lame", "-b:a", "32k",
                    "-f", "segment", "-segment_time", str(CHUNK_MIN * 60), "-reset_timestamps", "1",
                    os.path.join(WORK, "chunk_%03d.mp3")], check=True)
    total = probe(local)
    os.remove(local)
    return sorted(glob.glob(os.path.join(WORK, "chunk_*.mp3"))), total


def judge(text, clip_sec):
    """-> (ok, n_lines, last_sec, why). Dense, inside the clip, reaching its end, mostly in order."""
    stamps = [seconds(m) for m in (TS_START.match(l) for l in text.split("\n")) if m]
    if not stamps:
        return False, 0, 0, "no line timestamps"
    n, last = len(stamps), max(stamps)
    back = sum(1 for a, b in zip(stamps, stamps[1:]) if b < a - 2)
    need = max(12, int(clip_sec / 40))
    if n < need:
        return False, n, last, f"only {n} lines (want {need}+)"
    if last > clip_sec + 15:
        return False, n, last, f"times run past the clip ({mmss(last)} > {mmss(clip_sec)})"
    if last < 0.8 * clip_sec - 20:
        return False, n, last, f"stops early ({mmss(last)} of {mmss(clip_sec)})"
    if back > 0.1 * n:
        return False, n, last, f"{back} times go backwards"
    return True, n, last, "ok"


# ---- clients: (label, client) for each lane that has a key; built by setup_lanes()
LANES, COMBOS, DEAD = [], [], set()


def setup_lanes(get_secret):
    LANES.clear(); COMBOS.clear(); DEAD.clear()
    k = get_secret(AISTUDIO_SECRET)
    if k:
        LANES.append(("", genai.Client(api_key=k)))
    k = get_secret(VERTEX_SECRET)
    if k:
        LANES.append(("vx:", genai.Client(vertexai=True, api_key=k)))
    COMBOS.extend((lab, cl, m) for m in MODELS for lab, cl in LANES)   # model first, then lane
    return bool(LANES)


def transcribe_part(path, part, parts, book, clip_sec):
    data = open(path, "rb").read()
    prompt = PROMPT.format(part=part, parts=parts, book=book, clip=mmss(clip_sec))
    best = None                                        # (n_lines, text, who, why) of the best rejected answer
    for lab, cl, model in COMBOS:
        who = lab + model
        if who in DEAD:
            continue
        for attempt in range(3):
            try:
                resp = cl.models.generate_content(
                    model=model,
                    contents=[prompt, types.Part.from_bytes(data=data, mime_type="audio/mpeg")],
                    config=types.GenerateContentConfig(temperature=0.0, max_output_tokens=65536))
                text = (resp.text or "").strip()
                break
            except Exception as e:
                msg = str(e)
                if "429" in msg[:60] or "RESOURCE_EXHAUSTED" in msg:
                    say(f"   {who}: out of quota for today, trying the next one")
                    DEAD.add(who); text = None; break
                if any(c in msg[:60] for c in ("400", "401", "403", "404")) or "NOT_FOUND" in msg:
                    say(f"   {who}: not available ({msg[:100]}), trying the next one")
                    DEAD.add(who); text = None; break
                wait = 30 * (attempt + 1)
                say(f"   {who}: {msg[:100]} — retrying in {wait}s")
                time.sleep(wait); text = None
        if who in DEAD or text is None:
            continue
        ok, n, last, why = judge(text, clip_sec)
        if ok:
            say(f"   part {part}/{parts}: {who}, {n} lines, last {mmss(last)} of {mmss(clip_sec)}")
            return text, who, f"part {part}: {n} lines"
        say(f"   part {part}/{parts}: {who} rejected ({why}), trying the next one")
        if best is None or n > best[0]:
            best = (n, text, who, why)
    if best:
        say(f"   part {part}/{parts}: nothing passed; keeping the best answer from {best[2]} ({best[3]})")
        return best[1], best[2], f"part {part}: weak ({best[3]})"
    return None, None, f"part {part}: no answer"


def redo(name):
    say(f"▶ {name}")
    path = find_transcript(name)
    if not path:
        say(f"  ✗ transcript not found under {TX_DIR}/<book>/ — check the name in TARGETS"); return False
    book = os.path.basename(os.path.dirname(path))
    old = open(path, encoding="utf-8").read()
    head, _ = split_header(old)
    src = field(head, "راستہ")
    if not src or not os.path.exists(src):
        say(f"  ✗ recording not found: {src or '(no راستہ line)'} — is the سابعہ shortcut in My Drive?"); return False
    chunks, total = split_audio(src)
    say(f"  {len(chunks)} parts of up to {CHUNK_MIN} min, {mmss(total)} in all")
    texts, used, checks = [], [], []
    for i, ch in enumerate(chunks):
        clip = probe(ch)
        text, who, note = transcribe_part(ch, i + 1, len(chunks), book, clip)
        if text is None:
            say(f"  ✗ stopped: part {i + 1} got no answer from any model (quota?). The old transcript is untouched.")
            return False
        off = i * CHUNK_MIN * 60
        texts.append(TS_ANY.sub(lambda m: "[" + hms(off + seconds(m)) + "]", text))
        used.append(who); checks.append(note)
    body = "\n".join(texts)
    last = max((seconds(m) for m in (TS_START.match(l) for l in body.split("\n")) if m), default=0)
    title = next((l for l in head if l.startswith("#")), f"# {os.path.splitext(name)[0]}")
    keep = [(k, field(head, k)) for k in ("کتاب", "سبق", "تاریخ", "موضوع", "دورانیہ")]
    new_head = [title.replace("\\", ""), ""] + [f"- {k}: {v or '—'}" for k, v in keep] + [
        f"- ماڈل: {', '.join(dict.fromkeys(used))}",
        f"- حصے: {len(chunks)}",
        f"- بنایا: {datetime.date.today().isoformat()} (دوبارہ)",
        f"- راستہ: {src}",
        f"- جانچ: last timestamp {mmss(last)} of {mmss(total)} · " + " · ".join(checks),
    ]
    out = "\n".join(new_head) + "\n\n---\n\n" + body + "\n"
    stamp = datetime.datetime.now(PK).strftime("%Y%m%d-%H%M")
    rep_dir = os.path.join(TX_DIR, "_replaced", book)
    os.makedirs(rep_dir, exist_ok=True)
    shutil.copyfile(path, os.path.join(rep_dir, f"{stamp} {name}"))
    orig = os.path.join(TX_DIR, "_original", book, name)
    if os.path.exists(orig):                               # so _original will hold the new text before repair
        shutil.move(orig, os.path.join(rep_dir, f"{stamp} (original) {name}"))
    tmp = path + ".part"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(out)
    os.replace(tmp, path)
    say(f"  ✓ saved ({len(body.splitlines())} lines, models: {', '.join(dict.fromkeys(used))}); old copy in _replaced/{book}/")
    return True


def already_redone(name, since):
    """True if the transcript was re-made on or after the date `since` (YYYY-MM-DD)."""
    path = find_transcript(name)
    if not path:
        return False
    head, _ = split_header(open(path, encoding="utf-8").read(6000))
    made = field(head, "بنایا")
    return "دوبارہ" in made and made[:10] >= since
