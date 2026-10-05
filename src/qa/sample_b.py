"""Check B: random sample (random.seed(7)) of 4 tamheed/masala lines per lesson, with transcript context and matn pages."""
import runpy, glob, re, os, random, json
CARDS = '/home/claude/wifaq/cards/h4'; TX = '/home/claude/wifaq/qa/transcripts'; OCR = '/home/claude/wifaq/v7ocr'
def secs(t):
    h, m, s = map(int, t.split(':')); return h*3600+m*60+s
def tx_lines(date):
    txt = open(f'{TX}/{date}.md').read()
    body = txt.split('\n---', 1)[1]
    out = []; cur = None
    for line in body.splitlines():
        line = line.rstrip()
        m = re.match(r'\s*\[(\d+:\d\d:\d\d)\]\s*(.*)', line)
        if m:
            cur = [secs(m.group(1)), m.group(1), m.group(2)]; out.append(cur)
        elif cur is not None and line.strip():
            cur[2] += ' / ' + line.strip()      # continuation lines (2025-06-15 block format)
    return out
PAGES = {}
for f in sorted(glob.glob(f'{OCR}/p*.md')):          # page = position in file (some headers carry wrong PDF numbers)
    a, b = map(int, re.match(r'p(\d+)-(\d+)', os.path.basename(f)).groups())
    chunks = re.split(r'^=== PDF [^\n]*===\n', open(f).read(), flags=re.M)[1:]
    assert len(chunks) == b - a + 1, f
    for k, c in enumerate(chunks): PAGES[a + k - 1] = c   # printed page = PDF page - 1
def matn(p):
    t = PAGES.get(p)
    if t is None: return None
    m = re.search(r'\[متن\]\n(.*?)(?=\n\[بین السطور\]|\n\[حاشیہ\]|\Z)', t, re.S)
    return m.group(1) if m else t
random.seed(7)
sample = []
for f in sorted(glob.glob(f'{CARDS}/h4_2025-*.py')):
    d = runpy.run_path(f)
    if not d['CARDS']: continue
    pool = []
    for ci, card in enumerate(d['CARDS']):
        for sec in ('tamheed', 'masala'):
            for li, (text, tags) in enumerate(card[sec]):
                pool.append((ci, sec, li, text, tags))
    picks = random.sample(pool, 4)
    for ci, sec, li, text, tags in picks:
        sample.append({'file': os.path.basename(f), 'lesson': d['LESSON'], 'card': ci + 1, 'title': d['CARDS'][ci]['title'],
                       'sec': sec, 'line': li + 1, 'text': text, 'tags': tags, 'pool': len(pool)})
json.dump(sample, open('/home/claude/wifaq/qa/sample_b.json', 'w'), ensure_ascii=False, indent=1)
with open('/home/claude/wifaq/qa/sample_b_context.txt', 'w') as out:
    for i, s in enumerate(sample):
        out.write(f"\n######## S{i+1} {s['file']} card {s['card']} ({s['title']}) {s['sec']}[{s['line']}]  pool={s['pool']}\n")
        out.write(f"TEXT: {s['text']}\nTAGS: {s['tags']}\n")
        lines = tx_lines(s['lesson'])
        us = [t['v'] for t in s['tags'] if t['t'] == 'u']
        for u in us:
            su = secs(u)
            out.write(f"-- transcript from {u}:\n")
            for sec_, ts, tx in lines:
                if su <= sec_ <= su + 90: out.write(f"   [{ts}] {tx}\n")
        for k in [t['v'] for t in s['tags'] if t['t'] == 'k7']:
            if k <= 106:
                for p in (k,):
                    mt = matn(p)
                    out.write(f"-- matn p.{p}:\n{mt}\n")
print(len(sample))
