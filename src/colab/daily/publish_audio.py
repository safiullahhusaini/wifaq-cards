#!/usr/bin/env python3
"""Copy the Opus audio of every carded Hidaya 4 lesson that has none yet from the private data repo
(wifaq-data, filled by the Daily workflow) into the site (hidaya4/audio/), and register split parts in parts.json.

Usage: publish_audio.py <wifaq-data checkout> <wifaq-cards checkout> [--need]
Prints one line per lesson. Writes `changed=true|false` to $GITHUB_OUTPUT when set.
Only plain-date keys (h4_2025-12-06.py -> 2025-12-06) are handled: a date that has one recording in
audio/index.csv. Keys with a suffix (two recordings on one date) need LESSON_FILES and stay manual; they are listed as SKIPPED.
"""
import csv, glob, json, os, re, shutil, sys

data, repo = sys.argv[1], sys.argv[2]
NEED = len(sys.argv) > 3 and sys.argv[3] == "--need"   # only print the data-repo paths that would be copied
AUD = os.path.join(repo, "hidaya4", "audio")
rows = list(csv.DictReader(open(os.path.join(data, "audio", "index.csv"), encoding="utf-8-sig")))
by_date = {}
for r in rows:
    m = re.match(r"(\d{4}-\d\d-\d\d)", r["file"])
    if m:
        by_date.setdefault(m[1], {}).setdefault(r["file"], []).append(r)

pj_path = os.path.join(AUD, "parts.json")
parts_json = json.load(open(pj_path, encoding="utf-8")) if os.path.exists(pj_path) else {}
added, skipped = [], []
for f in sorted(glob.glob(os.path.join(repo, "src", "cards", "h4", "h4_20*.py"))):
    key = os.path.basename(f)[3:-3]
    if '"start":' not in open(f, encoding="utf-8").read():
        continue   # a lesson file without cards (07-06)
    if any(re.fullmatch(re.escape(key) + r"(-p?\d+)?\.ogg", os.path.basename(a)) for a in glob.glob(os.path.join(AUD, key + "*.ogg"))):
        continue
    if not re.fullmatch(r"\d{4}-\d\d-\d\d", key):
        skipped.append((key, "suffixed key: add it by hand (LESSON_FILES)")); continue
    recs = by_date.get(key, {})
    if len(recs) != 1:
        skipped.append((key, f"{len(recs)} recordings for this date in index.csv")); continue
    parts = sorted(next(iter(recs.values())), key=lambda r: int(r["part"]))
    srcs = [os.path.join(data, "audio", p["web_file"]) for p in parts]
    if NEED:
        for p in parts:
            print(os.path.join("audio", p["web_file"]))
        continue
    miss = [s for s in srcs if not os.path.exists(s)]
    if miss:
        skipped.append((key, "audio file not in wifaq-data yet (Opus copy not made)")); continue
    for n, (p, s) in enumerate(zip(parts, srcs), 1):
        name = key + ".ogg" if len(parts) == 1 else f"{key}-{n}.ogg"
        shutil.copyfile(s, os.path.join(AUD, name))
        if n >= 2:
            parts_json[name] = float(p["start_sec"])
    added.append((key, len(parts)))
if NEED:
    sys.exit(0)
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
