"""Check A: every U timestamp in the h4 card files must equal a transcript line timestamp of that lesson."""
import runpy, glob, re, os, json, bisect
CARDS = '/home/claude/wifaq/cards/h4'
TX = '/home/claude/wifaq/qa/transcripts'
TS = re.compile(r'\[(\d+:\d\d:\d\d)\]')
def secs(t):
    h, m, s = map(int, t.split(':')); return h*3600+m*60+s
def tx_stamps(date):
    txt = open(f'{TX}/{date}.md').read()
    body = txt.split('\n---', 1)[1] if '\n---' in txt else txt
    strict, loose = set(), set()
    for line in body.splitlines():
        m = re.match(r'\s*\[(\d+:\d\d:\d\d)\]', line)
        if m: strict.add(m.group(1))
        for t in TS.findall(line): loose.add(t)
    return strict, loose
def walk(x, path, out):
    if isinstance(x, dict):
        if x.get('t') == 'u': out.append((path, x))
        else:
            for k, v in x.items(): walk(v, path + [k], out)
    elif isinstance(x, (list, tuple)):
        for i, v in enumerate(x): walk(v, path + [i], out)
results = {}
for f in sorted(glob.glob(f'{CARDS}/h4_2025-*.py')):
    d = runpy.run_path(f)
    lesson = d['LESSON']
    if not d['CARDS']: continue
    strict, loose = tx_stamps(lesson)
    ssorted = sorted(strict, key=secs)
    tags = []
    for ci, card in enumerate(d['CARDS']):
        # card-level ts
        tags.append(([ci, 'ts'], {'t': 'u', 'v': card.get('ts')}))
        walk({k: v for k, v in card.items() if k in ('tamheed','masala','dalil','ikhtilaf','faida','lughat')}, [ci], tags)
    misses = []; n = 0
    for path, tag in tags:
        v = tag['v']; L = tag.get('l', lesson)
        if v is None: continue
        n += 1
        if L != lesson:
            s2, l2 = tx_stamps(L)
        else:
            s2, l2 = strict, loose
        if not re.fullmatch(r'\d+:\d\d:\d\d', str(v)):
            misses.append({'path': path, 'v': v, 'why': 'bad format'}); continue
        if v in s2: continue
        why = 'only mid-line in transcript' if v in l2 else 'not in transcript'
        sv = secs(v); i = bisect.bisect_left([secs(t) for t in ssorted], sv)
        near = [ssorted[j] for j in (i-1, i) if 0 <= j < len(ssorted)]
        misses.append({'path': path, 'v': v, 'why': why, 'nearest': near})
    results[os.path.basename(f)] = {'lesson': lesson, 'checked': n, 'misses': misses, 'tx_lines': len(strict)}
json.dump(results, open('/home/claude/wifaq/qa/check_a.json', 'w'), ensure_ascii=False, indent=1)
tot = sum(r['checked'] for r in results.values()); totm = sum(len(r['misses']) for r in results.values())
for k, r in results.items():
    print(k, r['checked'], 'checked,', len(r['misses']), 'misses')
    for m in r['misses']: print('   ', m)
print('TOTAL', tot, 'checked,', totm, 'misses')
