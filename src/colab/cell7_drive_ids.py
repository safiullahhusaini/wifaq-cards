# ── خانہ 7: ریکارڈنگز کی Drive IDs + ہم نام فائلوں کا مسئلہ ─────────────────────
# Cells 1–4 must have run first (Drive mounted, SOURCE_FOLDERS / OUT_DIR set, `rows` built).
# What this cell does:
#   1. Saves My Drive/Wifaq 1448/recording_ids.csv — every recording with its Drive file ID,
#      so the card pages can show "Download" and "Open in Drive" buttons for each lesson.
#   2. Replaces transcript_path() so that two recordings with the same name
#      (e.g. "2025-04-20 … الجنايات.m4a" and "… .mp4") get separate transcripts.
#      After running this cell, run cell 6 again: it will transcribe only the missing one.

import os, csv, glob, subprocess


def transcript_path(out_dir, row):
    """Same file name as before, unless another recording already owns that name.
    Then this one is saved as '<name> (mp4).md' (or (m4a), …)."""
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


def drive_id(path):
    """Drive file ID of a file on the mounted Drive (empty string if Colab doesn't expose it)."""
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


if "rows" not in globals():
    rows = scan(SOURCE_FOLDERS)

out_csv = os.path.join(OUT_DIR, "recording_ids.csv")
missing_id, same_name = [], {}
with open(out_csv, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["file", "book", "date", "minutes", "size_mb", "drive_id", "transcript", "path"])
    for r in rows:
        fid = drive_id(r["path"])
        if not fid:
            missing_id.append(r["file"])
        tp = transcript_path(OUT_DIR, r)
        w.writerow([r["file"], r["book"], r["date"], r["minutes"], r["size_mb"], fid,
                    os.path.basename(tp) if os.path.exists(tp) else "", r["path"]])
        key = (r["book"], os.path.splitext(r["file"])[0])
        same_name.setdefault(key, []).append(r)

print(f"✓ {out_csv}  ({len(rows)} recordings, {len(rows) - len(missing_id)} with Drive ID)")
if missing_id:
    print(f"⚠ No Drive ID for {len(missing_id)} files, e.g.: {missing_id[:3]}")

dups = {k: v for k, v in same_name.items() if len(v) > 1}
if dups:
    print("\nRecordings that share a name (each now gets its own transcript):")
    for (book, stem), rs in dups.items():
        for r in rs:
            tp = transcript_path(OUT_DIR, r)
            state = "done" if os.path.exists(tp) else "NOT YET — run cell 6 again"
            print(f"  {r['file']}  →  {os.path.basename(tp)}  [{state}]")
