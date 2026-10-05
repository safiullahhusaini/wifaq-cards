# @title 7 · Opus audio for the card site (no GPU needed · safe to stop and run again)
# Run cells 1–3 of the Timestamp Repair notebook first, then this cell.
# Makes a small Opus copy of each recording (16 kbps, about 5 MB for 45 minutes) in My Drive/Wifaq 1448/web_audio_opus/.
# Claude can fetch files of about 5 MB from Drive, so longer lessons are cut into equal parts of at most 5 MB.
# Lessons that already have a copy are skipped, so you can stop and run it again any time.
WEB_BOOKS = ["ہدایہ جلد رابع"]   # books to prepare, in this order (add more later, e.g. "مشکوٰۃ")
OPUS_KBPS = 16
MAX_MB = 5.0
MAKE_OPUS = True  # @param {type:"boolean"}

import csv, glob, json, math, os, shutil, subprocess
OPUS_DIR = os.path.join(OUT_DIR, "web_audio_opus")


def _opus_targets():
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


def _encode_opus(src, start, seconds, dst, kbps):
    tmp = os.path.join(LOCAL, "opus_tmp.ogg")
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", f"{start:.2f}", "-t", f"{seconds:.2f}", "-i", src,
                    "-vn", "-ac", "1", "-ar", "48000", "-c:a", "libopus", "-b:a", f"{kbps}k",
                    "-application", "voip", "-frame_duration", "60", tmp],
                   check=True, capture_output=True, timeout=3600)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(tmp, dst + ".part")
    os.replace(dst + ".part", dst)
    return os.path.getsize(dst)


def make_opus_audio():
    os.makedirs(LOCAL, exist_ok=True)
    targets = _opus_targets()
    print(f"{len(targets)} recordings in {', '.join(WEB_BOOKS)}", flush=True)
    made = 0
    for n, (_, _, file, book, path) in enumerate(targets, 1):
        stem = os.path.splitext(file)[0]
        side = os.path.join(OPUS_DIR, book, stem + ".json")
        if os.path.exists(side):
            continue
        local = None
        try:
            local = local_copy(path)
            dur = probe_seconds(local)
            parts = max(1, math.ceil((dur * OPUS_KBPS * 125 * 1.04 + 30000) / (MAX_MB * 1e6)))
            step = dur / parts
            info = []
            for i in range(parts):
                name = f"{stem}.ogg" if parts == 1 else f"{stem} - {i + 1}.ogg"
                dst = os.path.join(OPUS_DIR, book, name)
                length = step if i < parts - 1 else dur - i * step + 1
                size = _encode_opus(local, i * step, length, dst, OPUS_KBPS)
                if size > MAX_MB * 1e6:      # rare: squeeze a little more
                    size = _encode_opus(local, i * step, length, dst, 12)
                info.append({"web_file": f"{book}/{name}", "start": round(i * step, 2), "size_mb": round(size / 1e6, 2)})
            with open(side, "w", encoding="utf-8") as f:
                json.dump({"file": file, "book": book, "seconds": round(dur, 1), "parts": info}, f, ensure_ascii=False)
            made += 1
            print(f"[{n}/{len(targets)}] {file}: {len(info)} part(s), {sum(p['size_mb'] for p in info):.1f} MB", flush=True)
        except Exception as e:
            print(f"[{n}/{len(targets)}] {file}: ✗ {type(e).__name__}: {str(e)[:150]}", flush=True)
        finally:
            try:
                if local:
                    os.remove(local)
            except Exception:
                pass
    rows = []
    for side in glob.glob(os.path.join(OPUS_DIR, "*", "*.json")):
        with open(side, encoding="utf-8") as f:
            d = json.load(f)
        for i, p in enumerate(d["parts"], 1):
            rows.append([d["book"], d["file"], i, p["start"], d["seconds"], p["size_mb"], p["web_file"]])
    with open(os.path.join(OPUS_DIR, "index.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["book", "file", "part", "start_sec", "lesson_seconds", "size_mb", "web_file"])
        w.writerows(sorted(rows))
    print(f"\n✓ {made} new, {len(rows)} files listed in web_audio_opus/index.csv")


if MAKE_OPUS:
    make_opus_audio()
else:
    print("Skipped. Tick MAKE_OPUS to make the Opus copies.")
