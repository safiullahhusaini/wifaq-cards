# ------------------------------------------------------------------ timestamp repair: the run
import os, csv, json, glob, time, shutil, hashlib, subprocess, datetime
from zoneinfo import ZoneInfo

PK = ZoneInfo("Asia/Karachi")
TX_DIR = os.path.join(OUT_DIR, "transcripts")
ORIG_DIR = os.path.join(TX_DIR, "_original")     # untouched copies of every transcript we change
REDO_DIR = os.path.join(TX_DIR, "_redo")         # transcripts moved here are done again by the transcription notebook
WH_DIR = os.path.join(OUT_DIR, "_whisper")       # Whisper's word timings, kept so nothing is heard twice
LOG_PATH = os.path.join(OUT_DIR, "timestamp_fix.csv")
REPORT_PATH = os.path.join(OUT_DIR, "timestamp_fix.md")
LOCAL = "/content/tsfix" if os.path.isdir("/content") else "/tmp/tsfix"
BROKEN_MARK = "ٹرانسکرپٹ نہیں بن سکا"
HARD_FAILS = ("no timestamps", "empty answer", "blocked")


def now_pk():
    return datetime.datetime.now(PK)


def clock(dt):
    return dt.strftime("%I:%M %p").lstrip("0").lower()


def _norm_name(s):
    return norm_text(s).replace(" ", "")


def book_rank(book):
    nb = _norm_name(book)
    for i, b in enumerate(BOOK_ORDER):
        if _norm_name(b) and _norm_name(b) in nb:
            return i
    return len(BOOK_ORDER)


def header_fields(header):
    f = {}
    for line in header.split("\n"):
        if line.startswith("- ") and ":" in line:
            k, v = line[2:].split(":", 1)
            f[k.strip()] = v.strip()
    return f


def list_transcripts():
    rows = []
    for book_dir in sorted(glob.glob(os.path.join(TX_DIR, "*"))):
        book = os.path.basename(book_dir)
        if not os.path.isdir(book_dir) or book.startswith("_"):
            continue
        if ONLY_BOOKS and not any(_norm_name(b) in _norm_name(book) for b in ONLY_BOOKS):
            continue
        for path in glob.glob(os.path.join(book_dir, "*.md")):
            try:
                with open(path, encoding="utf-8") as f:
                    head = f.read(4000)
            except OSError:
                continue
            fields = header_fields(split_transcript(head)[0] or head)
            lesson = fields.get("سبق", "")
            rows.append({"path": path, "book": book, "file": os.path.basename(path),
                         "lesson": int(lesson) if lesson.isdigit() else 9999,
                         "audio": fields.get("راستہ", ""), "model": fields.get("ماڈل", ""),
                         "check": fields.get("جانچ", ""), "fixed": "وقت" in fields})
    rows.sort(key=lambda r: (book_rank(r["book"]), r["lesson"], r["file"]))
    return rows


def unfinished(text, check):
    """True when the transcription notebook will redo this transcript anyway."""
    if BROKEN_MARK in text or any(h in check for h in HARD_FAILS):
        return True
    for a, b in re.findall(r"(?<!nothing transcribed \()stopped at (\d+:\d\d) of (\d+:\d\d)", check):
        sec = lambda x: int(x.split(":")[0]) * 60 + int(x.split(":")[1])
        if sec(a) < 0.25 * sec(b):
            return True
    return False


# ------------------------------------------------------------------ Whisper
_PIPE = []


def _preload_cuda_libs():
    """Colab sometimes can't find cuDNN for faster-whisper; load the copies pip installed with torch."""
    import ctypes, site
    for sp in site.getsitepackages():
        for pat in ("nvidia/cublas/lib/libcublas*.so*", "nvidia/cudnn/lib/libcudnn*.so*"):
            for lib in sorted(glob.glob(os.path.join(sp, pat))):
                try:
                    ctypes.CDLL(lib, mode=ctypes.RTLD_GLOBAL)
                except OSError:
                    pass


def whisper_pipe():
    if _PIPE:
        return _PIPE[0]
    _preload_cuda_libs()
    import torch
    from faster_whisper import WhisperModel, BatchedInferencePipeline
    if torch.cuda.is_available():
        name, dev, ctype, batch = WHISPER_MODEL, "cuda", "float16", 16
    else:
        print("⚠ No GPU in this runtime (Runtime → Change runtime type → T4 GPU). "
              "Using the small model on the CPU — this is slow and less accurate.")
        name, dev, ctype, batch = "small", "cpu", "int8", 4
    print(f"Loading Whisper {name} on {dev}…", flush=True)
    model = WhisperModel(name, device=dev, compute_type=ctype)
    _PIPE.append((BatchedInferencePipeline(model=model), batch, name))
    return _PIPE[0]


def probe_seconds(path):
    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                              "-of", "default=nw=1:nk=1", path], capture_output=True, text=True, timeout=300).stdout
        return float(out.strip())
    except Exception:
        return 0.0


def local_copy(src):
    """Copy the recording to the Colab disk first: reading straight from Drive can cut audio short."""
    os.makedirs(LOCAL, exist_ok=True)
    dst = os.path.join(LOCAL, "src_" + hashlib.md5(src.encode("utf-8")).hexdigest()[:12] + os.path.splitext(src)[1])
    want = os.path.getsize(src)
    for _ in range(3):
        if os.path.exists(dst) and os.path.getsize(dst) == want:
            return dst
        try:
            shutil.copyfile(src, dst + ".part")
            os.replace(dst + ".part", dst)
        except OSError as e:
            print(f"   … copying from Drive failed ({e}); trying again", flush=True)
            time.sleep(10)
    if os.path.exists(dst) and os.path.getsize(dst) == want:
        return dst
    raise RuntimeError("the recording could not be copied from Drive completely")


def load_audio(path, sr=16000):
    """Decode with ffmpeg (not PyAV: Colab's newer PyAV breaks faster-whisper's own decoder)."""
    out = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", str(sr),
                          "-f", "f32le", "-"], capture_output=True, check=True, timeout=3600).stdout
    return np.frombuffer(out, np.float32).copy()


def run_whisper(audio_path):
    """-> (duration_sec, [(start, end, word), ...], model_name)"""
    pipe, batch, name = whisper_pipe()
    audio = load_audio(audio_path)
    segs, info = pipe.transcribe(audio, language="ur", batch_size=batch, word_timestamps=True)
    words = []
    for s in segs:
        if getattr(s, "words", None):
            words += [(round(w.start, 2), round(w.end, 2), w.word) for w in s.words]
        else:
            words.append((round(s.start, 2), round(s.end, 2), s.text))
    return len(audio) / 16000, words, name


def whisper_for(row):
    cache = os.path.join(WH_DIR, row["book"], os.path.splitext(row["file"])[0] + ".json")
    if os.path.exists(cache):
        with open(cache, encoding="utf-8") as f:
            d = json.load(f)
        return d["duration"], [tuple(w) for w in d["words"]], d.get("model", ""), True
    src = row["audio"]
    if not src or not os.path.exists(src):
        raise FileNotFoundError(f"recording not found: {src or '(no path in the header)'}")
    local = local_copy(src)
    try:
        t0 = time.time()
        dur, words, name = run_whisper(local)
        dur = dur or probe_seconds(local)
        print(f"   Whisper heard {len(words)} words in {time.time() - t0:.0f}s", flush=True)
    finally:
        try:
            os.remove(local)
        except OSError:
            pass
    os.makedirs(os.path.dirname(cache), exist_ok=True)
    tmp = cache + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"file": row["file"], "audio": src, "duration": dur, "model": name, "words": words},
                  f, ensure_ascii=False)
    os.replace(tmp, cache)
    return dur, words, name, False


# ------------------------------------------------------------------ one transcript
def _log(row, status, stats=None, gaps=(), note=""):
    stats = stats or {}
    new = not os.path.exists(LOG_PATH)
    with open(LOG_PATH, "a", newline="", encoding="utf-8-sig" if new else "utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["time_pk", "book", "lesson", "file", "transcribed_by", "lines", "matched_pct",
                        "typical_shift_s", "biggest_shift_s", "end_before", "end_after", "gaps", "status", "note"])
        w.writerow([now_pk().strftime("%Y-%m-%d %I:%M %p"), row["book"], row["lesson"] if row["lesson"] != 9999 else "",
                    row["file"], row["model"], stats.get("eligible", ""),
                    round(100 * stats["coverage"]) if "coverage" in stats else "",
                    stats.get("median_shift", ""), stats.get("max_shift", ""),
                    fmt_hms(stats["end_old"]) if "end_old" in stats else "",
                    fmt_hms(stats["end_new"]) if "end_new" in stats else "",
                    " ".join(f"{fmt_hms(a)}–{fmt_hms(b)}" for a, b in gaps), status, note])


def fix_one(row):
    with open(row["path"], encoding="utf-8") as f:
        text = f.read()
    stamp = (os.path.getmtime(row["path"]), len(text))
    if unfinished(text, row["check"]):
        return "skipped", "the transcription notebook will redo it"
    header, body = split_transcript(text)
    lines = parse_lines(body)
    if len(lines) < 15:
        return "skipped", f"only {len(lines)} timestamped lines found"
    dur, words, wmodel, cached = whisper_for(row)
    wt = WhisperText(words)
    new, kept, stats = align(lines, wt, dur)
    if new is None:
        _log(row, "not aligned", stats, note=stats.get("reason", ""))
        return "not aligned", stats.get("reason", "")
    gaps = find_gaps(lines, kept, wt, dur)
    notes = [f"- وقت: Whisper ({wmodel}) سے ملایا، {now_pk().date().isoformat()} · {round(100 * stats['coverage'])}% سطریں ملیں"
             f" · سب سے بڑی تبدیلی {fmt_hms(stats['max_shift'])} · اصل: transcripts/_original"]
    if gaps:
        notes.append("- خلا: " + " · ".join(f"{fmt_hms(a)}–{fmt_hms(b)}" for a, b in gaps)
                     + " (یہاں آواز ہے مگر متن بہت کم — دوبارہ ٹرانسکرائب کرنا بہتر)")
    out = render(header, body, lines, new, notes)
    # the transcription notebook may have rewritten the file meanwhile: then leave it for the next run
    with open(row["path"], encoding="utf-8") as f:
        again = f.read()
    if (os.path.getmtime(row["path"]), len(again)) != stamp:
        return "skipped", "the transcript changed while we worked; next run"
    orig = os.path.join(ORIG_DIR, row["book"], row["file"])
    if not os.path.exists(orig):
        os.makedirs(os.path.dirname(orig), exist_ok=True)
        shutil.copyfile(row["path"], orig)
    tmp = row["path"] + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(out)
    os.replace(tmp, row["path"])
    status = "fixed, text missing" if gaps else "fixed"
    if gaps and MOVE_GAPS_FOR_REDO:
        dst = os.path.join(REDO_DIR, row["book"], row["file"])
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.move(row["path"], dst)
        status += ", moved for redo"
    _log(row, status, stats, gaps)
    return status, (f"{round(100 * stats['coverage'])}% matched · typical shift {stats['median_shift']:.0f}s · "
                    f"biggest {fmt_hms(stats['max_shift'])}" + (f" · text missing at " + ", ".join(
                        f"{fmt_hms(a)}–{fmt_hms(b)}" for a, b in gaps) if gaps else ""))


# ------------------------------------------------------------------ report
def write_report():
    if not os.path.exists(LOG_PATH):
        return
    with open(LOG_PATH, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    last = {}
    for r in rows:                                     # latest result per transcript
        last[(r["book"], r["file"])] = r
    out = [f"# Timestamp repair — {now_pk().strftime('%d %b %Y, ')}{clock(now_pk())}", ""]
    fixed = [r for r in last.values() if r["status"].startswith("fixed")]
    gappy = [r for r in fixed if r["gaps"]]
    bad = [r for r in last.values() if r["status"] == "not aligned"]
    out += [f"- Fixed: {len(fixed)} transcripts ({len(gappy)} of them have stretches with text missing)",
            f"- Could not be matched: {len(bad)}", ""]
    if gappy:
        out += ["## Text missing (worth transcribing again)", "",
                "| کتاب | سبق | فائل | کہاں | ماڈل |", "|---|---|---|---|---|"]
        out += [f"| {r['book']} | {r['lesson']} | {r['file']} | {r['gaps']} | {r['transcribed_by']} |" for r in gappy]
        out.append("")
    if bad:
        out += ["## Could not be matched", ""] + [f"- {r['book']} · {r['file']}: {r['note']}" for r in bad] + [""]
    big = sorted(fixed, key=lambda r: -float(r["biggest_shift_s"] or 0))[:25]
    if big:
        out += ["## Biggest corrections", "", "| کتاب | فائل | ماڈل | سب سے بڑی تبدیلی | آخری وقت پہلے → اب |", "|---|---|---|---|---|"]
        out += [f"| {r['book']} | {r['file']} | {r['transcribed_by']} | {fmt_hms(float(r['biggest_shift_s'] or 0))} | "
                f"{r['end_before']} → {r['end_after']} |" for r in big]
    tmp = REPORT_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    os.replace(tmp, REPORT_PATH)


# ------------------------------------------------------------------ main loop
def run_fix():
    deadline = time.time() + MAX_HOURS * 3600
    rows = list_transcripts()
    todo = [r for r in rows if REFIX or not r["fixed"]]
    print(f"{len(rows)} transcripts in Drive, {len(todo)} to check"
          + (f" (books: {', '.join(ONLY_BOOKS)})" if ONLY_BOOKS else "") + ".")
    print(f"Stops by itself after {MAX_HOURS} h (at {clock(now_pk() + datetime.timedelta(hours=MAX_HOURS))}); "
          "stopping earlier is safe.\n", flush=True)
    done = {}
    try:
        for n, row in enumerate(todo, 1):
            if time.time() > deadline:
                print(f"\nTime limit reached (MAX_HOURS = {MAX_HOURS}). Run it again to carry on.")
                break
            print(f"[{n}/{len(todo)}] {row['book']} · {row['file']}", flush=True)
            try:
                status, note = fix_one(row)
            except Exception as e:
                status, note = "error", f"{type(e).__name__}: {str(e)[:160]}"
                _log(row, "error", note=note)
            done[status] = done.get(status, 0) + 1
            print(f"   {status}" + (f" — {note}" if note else ""), flush=True)
    except KeyboardInterrupt:
        print("\n■ Stopped. Finished transcripts are saved; run again to carry on.")
    write_report()
    print("\n" + ", ".join(f"{k}: {v}" for k, v in done.items()))
    print(f"Report: {REPORT_PATH}")
