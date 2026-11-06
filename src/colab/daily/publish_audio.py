#!/usr/bin/env python3
"""Copy the Opus audio of every carded Hidaya 4 lesson that has none yet from the private data repo
(wifaq-data, filled by the Daily workflow) into the site (hidaya4/audio/), and register split parts in parts.json.

Usage: publish_audio.py <wifaq-data checkout> <wifaq-cards checkout> [--need]
Prints one line per lesson. Writes `changed=true|false` to $GITHUB_OUTPUT when set.
Plain-date keys (h4_2025-12-06.py -> 2025-12-06): the date must have one recording in audio/index.csv.
Keys with a suffix (two recordings on one date, e.g. 2025-04-20-diyat, since 6 Nov 2026): the recording is found via
LESSON_FILES in src/cards/h4_data.py (key -> Drive id) and status/recording_ids.csv in wifaq-data (Drive id -> file name);
split parts are named <key>-p1.ogg, <key>-p2.ogg (a plain "-2" is another lesson's key).
"""
import csv, glob, json, os, re, shutil, sys

data, repo = sys.argv[1], sys.argv[2]
NEED = len(sys.argv) > 3 and sys.argv[3] == "--need"   # only print the data-repo paths that would be copied
AUD = os.path.join(repo, "hidaya4", "audio")
AUD3 = os.path.join(repo, "hidaya3", "audio")
rows = list(csv.DictReader(open(os.path.join(data, "audio", "index.csv"), encoding="utf-8-sig")))
by_date = {}
for r in rows:
    m = re.match(r"(\d{4}-\d\d-\d\d)", r["file"])
    if m:
        by_date.setdefault(m[1], {}).setdefault(r["file"], []).append(r)

def norm_name(x):
    return re.sub(r"\s+", "", x).translate(str.maketrans("ىيةهأإآ", "ييههااا"))


def lesson_files():
    """LESSON_FILES of h4_data.py (suffixed key -> Drive id of its recording), read as text (no import: it needs the OCR)."""
    txt = open(os.path.join(repo, "src", "cards", "h4_data.py"), encoding="utf-8").read()
    m = re.search(r"^LESSON_FILES\s*=\s*\{(.*?)\}", txt, re.S | re.M)
    return dict(re.findall(r'"([0-9][^"]+)"\s*:\s*"([^"]+)"', m[1])) if m else {}


def drive_names():
    """Drive id -> recording file name, from wifaq-data status/recording_ids.csv (empty if not checked out)."""
    f = os.path.join(data, "status", "recording_ids.csv")
    if not os.path.exists(f):
        return {}
    return {r["drive_id"].strip(): r["file"].strip() for r in csv.DictReader(open(f, encoding="utf-8-sig")) if r.get("drive_id")}


def h3_keys():
    """Hidaya 3 card files src/cards/h3/h3_<key>.py -> (key, recording file name or None)."""
    out = []
    for f in sorted(glob.glob(os.path.join(repo, "src", "cards", "h3", "h3_20*.py"))):
        txt = open(f, encoding="utf-8").read()
        if '"start":' not in txt:
            continue
        m = re.search(r'^RECORDING\s*=\s*"([^"]+)"', txt, re.M)
        out.append((os.path.basename(f)[3:-3], m[1] if m else None))
    return out


pj_path = os.path.join(AUD, "parts.json")
parts_json = json.load(open(pj_path, encoding="utf-8")) if os.path.exists(pj_path) else {}
added, skipped = [], []
LF, DN = lesson_files(), drive_names()
by_norm = {norm_name(r["file"]): r["file"] for r in rows}
by_file = {}
for r in rows:
    by_file.setdefault(r["file"], []).append(r)
for f in sorted(glob.glob(os.path.join(repo, "src", "cards", "h4", "h4_20*.py"))):
    key = os.path.basename(f)[3:-3]
    if '"start":' not in open(f, encoding="utf-8").read():
        continue   # a lesson file without cards (07-06)
    plain = bool(re.fullmatch(r"\d{4}-\d\d-\d\d", key))
    have_re = re.escape(key) + (r"(-p?\d+)?\.ogg" if plain else r"(-p\d+)?\.ogg")
    if any(re.fullmatch(have_re, os.path.basename(a)) for a in glob.glob(os.path.join(AUD, key + "*.ogg"))):
        continue
    if plain:
        recs = by_date.get(key, {})
        if len(recs) != 1:
            skipped.append((key, f"{len(recs)} recordings for this date in index.csv")); continue
        rec_rows = next(iter(recs.values()))
    else:
        fid = LF.get(key)
        name = DN.get(fid) if fid else None
        rec = by_norm.get(norm_name(name)) if name else None
        if not fid:
            skipped.append((key, "suffixed key without a LESSON_FILES entry in h4_data.py")); continue
        if not rec:
            skipped.append((key, f"recording {name or fid} not found in audio/index.csv")); continue
        rec_rows = by_file[rec]
    parts = sorted(rec_rows, key=lambda r: int(r["part"]))
    srcs = [os.path.join(data, "audio", p["web_file"]) for p in parts]
    if NEED:
        for p in parts:
            print(os.path.join("audio", p["web_file"]))
        continue
    miss = [s for s in srcs if not os.path.exists(s)]
    if miss:
        skipped.append((key, "audio file not in wifaq-data yet (Opus copy not made)")); continue
    for n, (p, s) in enumerate(zip(parts, srcs), 1):
        name = key + ".ogg" if len(parts) == 1 else (f"{key}-{n}.ogg" if plain else f"{key}-p{n}.ogg")
        shutil.copyfile(s, os.path.join(AUD, name))
        if n >= 2:
            parts_json[name] = float(p["start_sec"])
    added.append((key, len(parts)))

# ---- Hidaya 3 (hidaya3/audio): key = <date>-1448 (this year, recording named in the card file) or <date> (last year)
pj3_path = os.path.join(AUD3, "parts.json")
parts_json3 = json.load(open(pj3_path, encoding="utf-8")) if os.path.exists(pj3_path) else {}
by_file3 = {}
for r in rows:
    if r["book"].strip() == "\u06c1\u062f\u0627\u06cc\u06c1 \u062c\u0644\u062f \u062b\u0627\u0644\u062b":
        by_file3.setdefault(r["file"], []).append(r)
added3 = []
for key, rec in h3_keys():
    os.makedirs(AUD3, exist_ok=True)
    if glob.glob(os.path.join(AUD3, key + ".ogg")) or glob.glob(os.path.join(AUD3, key + "-[0-9].ogg")) or glob.glob(os.path.join(AUD3, key + "-[0-9][0-9].ogg")):
        continue
    if rec is None:
        d = key[:10]
        cand = [f for f in by_file3 if f.startswith(d)]
        rec = cand[0] if len(cand) == 1 else None
    if rec is None or rec not in by_file3:
        skipped.append((key, "Hidaya 3: recording not found in audio/index.csv")); continue
    parts = sorted(by_file3[rec], key=lambda r: int(r["part"]))
    srcs = [os.path.join(data, "audio", p["web_file"]) for p in parts]
    if NEED:
        for p in parts:
            print(os.path.join("audio", p["web_file"]))
        continue
    miss = [s for s in srcs if not os.path.exists(s)]
    if miss:
        skipped.append((key, "Hidaya 3 audio file not in wifaq-data yet")); continue
    for n, (p, s) in enumerate(zip(parts, srcs), 1):
        name = key + ".ogg" if len(parts) == 1 else f"{key}-{n}.ogg"
        shutil.copyfile(s, os.path.join(AUD3, name))
        if n >= 2:
            parts_json3[name] = float(p["start_sec"])
    added3.append((key, len(parts)))
if NEED:
    sys.exit(0)
if added3:
    json.dump(parts_json3, open(pj3_path, "w", encoding="utf-8"), ensure_ascii=False)
added = added + added3
if added:
    json.dump(parts_json, open(pj_path, "w", encoding="utf-8"), ensure_ascii=False)
for k, n in added:
    print(f"ADDED {k} ({n} part{'s' if n > 1 else ''})")
for k, why in skipped:
    print(f"SKIPPED {k}: {why}")
if not added and not skipped:
    print("nothing to do")
if os.environ.get("GITHUB_OUTPUT"):
    with open(os.environ["GITHUB_OUTPUT"], "a") as o:
        o.write(f"changed={'true' if added else 'false'}\n")
