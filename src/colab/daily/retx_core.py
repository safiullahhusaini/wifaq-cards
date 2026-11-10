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


# Gemini sometimes ignores the "[mm:ss] text" format: "00:12 text", "(00:12) text", "**00:12** - text", or the
# timestamp alone on its own line with the text on the next line. Before 10 Nov 2026 such a part counted as
# "no line timestamps", was kept as weak, and the repair then reported 10 minutes of "missing text" although the
# text was there (1 Aug, 19 and 20 Sep 2026). normalize() rewrites all of these to "[mm:ss] text".
_LEAD = r"^\s*(?:[-*•>]\s*)*(?:\*\*)?"
TS_LOOSE = re.compile(_LEAD + r"[\[(]?\s*((?:\d{1,2}:)?\d{1,3}:\d{2})\s*[\])]?(?:\*\*)?\s*(?:[-–—:|]\s*)?(.*)$")


def _sec_of(t):
    p = [int(x) for x in t.split(":")]
    return p[0] * 3600 + p[1] * 60 + p[2] if len(p) == 3 else p[0] * 60 + p[1]


def normalize(text):
    """Every timestamped line -> "[h:mm:ss] text" or "[mm:ss] text"; lone stamps join the next text line;
    untimed text lines join the line before them. Times are kept as given (clip-relative or absolute)."""
    out, pending = [], None
    for raw in (text or "").split("\n"):
        line = raw.strip()
        if not line or line.startswith("```"):
            continue
        m = TS_LOOSE.match(line)
        if m:
            if pending is not None and pending[1] == "":
                pass                                  # two stamps in a row: the first had no text, drop it
            elif pending is not None:
                out.append(pending)
            pending = [m.group(1), m.group(2).strip()]
        elif pending is not None:
            pending[1] = (pending[1] + " " + line).strip()
        elif out:
            out[-1][1] = (out[-1][1] + " " + line).strip()
    if pending is not None and pending[1]:
        out.append(pending)
    return "\n".join(f"[{t}] {x}" for t, x in out if x)


def judge(text, clip_sec):
    """-> (ok, n_lines, last_sec, why). Dense, inside the clip, reaching its end, mostly in order."""
    stamps = [seconds(m) for m in (TS_START.match(l) for l in text.split("\n")) if m]
    if not stamps:
        return False, 0, 0, "no line timestamps"
    n, last = len(stamps), max(stamps)
    back = sum(1 for a, b in zip(stamps, stamps[1:]) if b < a - 2)
    need = max(12, int(clip_sec / 40)) if clip_sec >= 240 else max(2, int(clip_sec / 20))
    if n < need:
        return False, n, last, f"only {n} lines (want {need}+)"
    if last > clip_sec + 15:
        return False, n, last, f"times run past the clip ({mmss(last)} > {mmss(clip_sec)})"
    if last < 0.8 * clip_sec - 20 and clip_sec - last > 75:     # a quiet last minute (class ending) is fine
        return False, n, last, f"stops early ({mmss(last)} of {mmss(clip_sec)})"
    if back > 0.1 * n:
        return False, n, last, f"{back} times go backwards"
    return True, n, last, "ok"


# ---- clients: (label, client) for each lane that has a key; built by setup_lanes()
LANES, COMBOS, DEAD = [], [], set()
REQUEST_TIMEOUT_S = 300          # one clip of 10 min normally answers in 1-3 min
GEMINI_BUDGET_MIN = 150          # all Gemini work of one Daily; the repair, Opus copies and sync always get their turn
DEADLINE = float("inf")


def out_of_time():
    return time.time() > DEADLINE


def setup_lanes(get_secret):
    LANES.clear(); COMBOS.clear(); DEAD.clear()
    global DEADLINE
    DEADLINE = time.time() + GEMINI_BUDGET_MIN * 60
    # 8 Nov 2026: one request hung for 5 h 43 min with no answer, the 6-hour job limit killed the run, and that day's
    # repair, Opus copies and sync were lost. Every request now gives up after REQUEST_TIMEOUT_S.
    http = types.HttpOptions(timeout=REQUEST_TIMEOUT_S * 1000)
    k = get_secret(AISTUDIO_SECRET)
    if k:
        LANES.append(("", genai.Client(api_key=k, http_options=http)))
    k = get_secret(VERTEX_SECRET)
    if k:
        LANES.append(("vx:", genai.Client(vertexai=True, api_key=k, http_options=http)))
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
        if out_of_time():
            say(f"   Gemini time budget ({GEMINI_BUDGET_MIN} min) used up; the rest waits for tomorrow")
            break
        for attempt in range(3):
            try:
                resp = cl.models.generate_content(
                    model=model,
                    contents=[prompt, types.Part.from_bytes(data=data, mime_type="audio/mpeg")],
                    config=types.GenerateContentConfig(temperature=0.0, max_output_tokens=65536))
                text = normalize((resp.text or "").strip())
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


def transcribe_audio(src, book, only=None):
    """Transcribe a recording in CHUNK_MIN parts (all, or just the part numbers in `only`, counted from 1).
    Returns (body, models, checks, chunks, seconds) or None."""
    chunks, total = split_audio(src)
    say(f"  {len(chunks)} parts of up to {CHUNK_MIN} min, {mmss(total)} in all"
        + (f"; only part(s) {', '.join(map(str, sorted(only)))} this time" if only else ""))
    texts, used, checks = [], [], []
    for i, ch in enumerate(chunks):
        if only and i + 1 not in only:
            continue
        clip = probe(ch)
        text, who, note = transcribe_part(ch, i + 1, len(chunks), book, clip)
        if text is None:
            say(f"  ✗ stopped: part {i + 1} got no answer from any model (quota?).")
            return None
        off = i * CHUNK_MIN * 60
        texts.append(TS_ANY.sub(lambda m: "[" + hms(off + seconds(m)) + "]", text))
        used.append(who); checks.append(note)
    return "\n".join(texts), used, checks, chunks, total


def redo(name):
    say(f"▶ {name}")
    path = find_transcript(name)
    if not path:
        say(f"  ✗ transcript not found under {TX_DIR}/<book>/ — check the name in TARGETS"); return False
    book = os.path.basename(os.path.dirname(path))
    old = open(path, encoding="utf-8").read()
    head, _ = split_header(old)
    if heal(name):
        return True                                    # the text was there; no Gemini request needed
    src = field(head, "راستہ")
    if not src or not os.path.exists(src):
        say(f"  ✗ recording not found: {src or '(no راستہ line)'} — is the سابعہ shortcut in My Drive?"); return False
    parts = parts_to_redo(head)
    got = transcribe_audio(src, book, only=parts)
    if got is None:
        say("  The old transcript is untouched."); return False
    body, used, checks, chunks, total = got
    if parts and len(parts) < len(chunks):             # splice the new parts into the existing text
        body, used, checks = splice_parts(old, parts, body, used, checks, len(chunks))
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


# ------------------------------------------------------------ cheaper redos (10 Nov 2026)
GAP_LINE = re.compile(r"(\d+):(\d{2}):(\d{2})\s*[–-]\s*(\d+):(\d{2}):(\d{2})")


def gap_ranges(head):
    """[(start_sec, end_sec)] from the header's '- خلا:' line (written by the repair step)."""
    g = field(head, "خلا")
    return [(int(a) * 3600 + int(b) * 60 + int(c), int(d) * 3600 + int(e) * 60 + int(f))
            for a, b, c, d, e, f in GAP_LINE.findall(g)]


def parts_to_redo(head):
    """Part numbers (from 1) that need Gemini again: parts marked weak / no answer in '- جانچ:', and parts
    overlapping a '- خلا:' range. Empty set = redo everything (nothing tells us which part is bad)."""
    bad = {int(n) for n, why in re.findall(r"part (\d+): (weak|no answer)", field(head, "جانچ"))}
    for a, b in gap_ranges(head):
        first, last = (a + 30) // (CHUNK_MIN * 60), max(a, b - 30) // (CHUNK_MIN * 60)   # ±30 s: gaps end/begin at part edges
        bad.update(range(first + 1, last + 2))
    return bad


def _abs_lines(body_lines):
    """Body lines -> [(seconds, text)], also for parts where the model wrote bare '00:12 text' times (those are
    clip-relative: they get the start of their CHUNK_MIN part added) or put the stamp alone on a line."""
    out, base, prev_abs, prev_rel = [], None, 0, None
    for raw in body_lines:
        line = raw.strip()
        if not line:
            continue
        m = TS_LOOSE.match(line)
        if not m:
            if out:
                out[-1][1] = (out[-1][1] + " " + line).strip()
            continue
        bare = "[" not in line[:m.end(1) + 2]
        t = _sec_of(m.group(1))
        if not bare:
            base, prev_rel, sec = None, None, t
        else:
            if base is None:
                step = CHUNK_MIN * 60
                base = 0 if prev_abs == 0 else -(-max(prev_abs - 30, 0) // step) * step
            elif prev_rel is not None and t < prev_rel - 60:
                base += CHUNK_MIN * 60
            prev_rel, sec = t, base + t
        prev_abs = sec
        if out and out[-1][1] == "":
            out.pop()                                   # a stamp with no text: the text came on the next line
        out.append([sec, m.group(2).strip()])
    return [(s, x) for s, x in out if x]


def _write_with_backup(path, book, name, text):
    stamp = datetime.datetime.now(PK).strftime("%Y%m%d-%H%M")
    rep_dir = os.path.join(TX_DIR, "_replaced", book)
    os.makedirs(rep_dir, exist_ok=True)
    shutil.copyfile(path, os.path.join(rep_dir, f"{stamp} {name}"))
    orig = os.path.join(TX_DIR, "_original", book, name)
    if os.path.exists(orig):                            # the repair step makes a fresh _original from this text
        shutil.move(orig, os.path.join(rep_dir, f"{stamp} (original) {name}"))
    with open(path + ".part", "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(path + ".part", path)


def heal(name):
    """Fix a transcript whose 'missing' text is only badly formatted timestamps (bare '00:12 text' or a lone
    stamp line). Uses no Gemini request. Takes the text from the _original copy (Gemini's words before the repair
    step) when there is one. Drops the '- وقت:'/'- خلا:' lines so today's repair step aligns it again.
    -> True if it rewrote the file."""
    path = find_transcript(name)
    if not path:
        return False
    book = os.path.basename(os.path.dirname(path))
    cur = open(path, encoding="utf-8").read()
    head, body = split_header(cur)
    if not field(head, "خلا") and "no line timestamps" not in field(head, "جانچ"):
        return False
    orig = os.path.join(TX_DIR, "_original", book, os.path.basename(path))
    src_body = split_header(open(orig, encoding="utf-8").read())[1] if os.path.exists(orig) else body
    strict = sum(1 for l in src_body if TS_START.match(l) and TS_START.sub("", l).strip())
    lines = _abs_lines(src_body)
    gained = len(lines) - strict
    gaps = gap_ranges(head)
    in_gaps = sum(1 for s_, _ in lines if any(a <= s_ < b for a, b in gaps))
    need = sum(max(6, (b - a) // 30) for a, b in gaps)
    if gained < 5 or (gaps and in_gaps < need):
        return False
    keep = [l for l in head if not re.match(r"^\s*-\s*(وقت|خلا)\s*:", l)]
    keep.append(f"- درست: {datetime.date.today().isoformat()} · {gained} سطروں کے وقت کی شکل ٹھیک کی (Gemini دوبارہ نہیں)")
    text = "\n".join(keep) + "\n\n---\n\n" + "\n".join(f"[{hms(s_)}] {x}" for s_, x in lines) + "\n"
    _write_with_backup(path, book, os.path.basename(path), text)
    say(f"  ✓ healed {os.path.basename(path)}: {gained} lines had badly written times; "
        f"{in_gaps} lines now inside the old gap(s). No Gemini request used; the repair step re-aligns it today.")
    return True


def heal_all():
    """heal() every transcript that has a '- خلا:' line or a part with no line timestamps. -> names healed."""
    done = []
    for p in sorted(glob.glob(os.path.join(TX_DIR, "*", "*.md"))):
        if os.path.basename(os.path.dirname(p)).startswith("_"):
            continue
        try:
            head, _ = split_header(open(p, encoding="utf-8").read(6000))
        except OSError:
            continue
        if (field(head, "خلا") or "no line timestamps" in field(head, "جانچ")) and heal(os.path.basename(p)):
            done.append(os.path.basename(p))
    return done


def splice_parts(old_text, parts, new_body, used, checks, n_chunks):
    """Replace the lines of `parts` (numbers from 1) in the existing transcript with the newly transcribed ones."""
    head, body = split_header(old_text)
    step = CHUNK_MIN * 60
    keep = [(s_, x) for s_, x in _abs_lines(body) if s_ // step + 1 not in parts]
    new = _abs_lines(new_body.split("\n"))
    lines = sorted(keep + new, key=lambda t: t[0])
    old_checks = {int(n): c for n, c in re.findall(r"(?:^|·\s*)part (\d+): ([^·]+)", field(head, "جانچ"))}
    for c in checks:
        m = re.match(r"part (\d+): (.*)", c)
        if m:
            old_checks[int(m.group(1))] = m.group(2).strip()
    all_checks = [f"part {i}: {old_checks.get(i, '?').strip()}" for i in range(1, n_chunks + 1)]
    old_models = [m.strip() for m in field(head, "ماڈل").split(",") if m.strip()]
    say(f"  spliced part(s) {', '.join(map(str, sorted(parts)))} into the existing text ({len(new)} new lines)")
    return "\n".join(f"[{hms(s_)}] {x}" for s_, x in lines), old_models + used, all_checks


def already_redone(name, since):
    """True if the transcript was re-made on or after the date `since` (YYYY-MM-DD)."""
    path = find_transcript(name)
    if not path:
        return False
    head, _ = split_header(open(path, encoding="utf-8").read(6000))
    made = field(head, "بنایا")
    healed = field(head, "درست")
    return ("دوبارہ" in made and made[:10] >= since) or (healed[:10] >= since if healed else False)


# ------------------------------------------------------------ this year's class recordings (since 3 Nov 2026)
# The user drops this year's recordings into My Drive/input_audio (e.g. "Hidaya Saalis 20 Sep 2026.m4a"). They get a
# first transcript here, with the same prompt and checks as redo(). The card runs prefer them over last year's vault.
AUDIO_EXT = (".mp3", ".m4a", ".mp4", ".wav", ".ogg", ".opus", ".aac", ".amr", ".webm", ".3gp", ".flac", ".mkv", ".mov")
MONTHS = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
BOOK_WORDS = [("ہدایہ جلد ثالث", ("saalis", "salis", "salith", "thalith", "ثالث", "سالس")),
              ("ہدایہ جلد رابع", ("rabi", "raabi", "رابع"))]


def class_recording(path):
    """(book, 'YYYY-MM-DD') for a class recording named like 'Hidaya Saalis 6 Sep 26.m4a', else None."""
    low = nfc(path).lower()
    if not low.endswith(AUDIO_EXT):
        return None
    name = os.path.basename(low)
    book = next((b for b, words in BOOK_WORDS if any(w in low for w in words)), None)
    if not book or not any(w in low for w in ("hidaya", "hedaya", "hidayah", "ہدایہ", "هدايه", "الهدايه")):
        return None
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", name)
    if m:
        return book, m.group(0)
    m = re.search(r"(\d{1,2})[\s_.-]*([a-z]{3,9})[\s_.,-]*(\d{4}|\d{2})(?!\d)", name)
    if not m or m.group(2)[:3] not in MONTHS:
        return None
    y = int(m.group(3)); y = y + 2000 if y < 100 else y
    try:
        return book, datetime.date(y, MONTHS[m.group(2)[:3]], int(m.group(1))).isoformat()
    except ValueError:
        return None


def transcript_for_audio(src):
    """Path of the transcript whose راستہ line is this recording, or None."""
    key = nfc(src)
    for p in glob.glob(os.path.join(TX_DIR, "*", "*.md")):
        if os.path.basename(os.path.dirname(p)).startswith("_"):
            continue
        try:
            head, _ = split_header(open(p, encoding="utf-8").read(4000))
        except OSError:
            continue
        if nfc(field(head, "راستہ")) == key:
            return p
    return None


def transcribe_new(src, book, date, year="1448"):
    """First transcript of a new class recording. Returns (transcript file name, minutes), or None."""
    say(f"▶ new recording: {os.path.basename(src)} ({book}, {date})")
    got = transcribe_audio(src, book)
    if got is None:
        return None
    body, used, checks, chunks, total = got
    last = max((seconds(m) for m in (TS_START.match(l) for l in body.split("\n")) if m), default=0)
    out_dir = os.path.join(TX_DIR, book)
    os.makedirs(out_dir, exist_ok=True)
    base = f"{date} {book} {year}"
    name, n = base + ".md", 2
    while os.path.exists(os.path.join(out_dir, name)):
        name, n = f"{base} {n}.md", n + 1
    head = [f"# {os.path.splitext(name)[0]}", "",
            f"- کتاب: {book}", "- سبق: —", f"- تاریخ: {date}", f"- سال: {year} (اس سال کی کلاس)", "- موضوع: —",
            f"- دورانیہ: {mmss(total)}", f"- ماڈل: {', '.join(dict.fromkeys(used))}", f"- حصے: {len(chunks)}",
            f"- بنایا: {datetime.date.today().isoformat()} (نیا)", f"- راستہ: {src}",
            f"- جانچ: last timestamp {mmss(last)} of {mmss(total)} · " + " · ".join(checks)]
    path = os.path.join(out_dir, name)
    with open(path + ".part", "w", encoding="utf-8") as f:
        f.write("\n".join(head) + "\n\n---\n\n" + body + "\n")
    os.replace(path + ".part", path)
    say(f"  ✓ saved {book}/{name} ({len(body.splitlines())} lines)")
    return name, round(total / 60, 1)
