"""Build the public site (GitHub Pages) from the card builders.

Card pages are written by h4_build.py / m1_build.py in the artifact form (no <html>/<head>); here they get a full
document, a noindex tag, and a home page that links them. Output: the wifaq-cards repo working tree.
"""
import os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = sys.argv[1] if len(sys.argv) > 1 else os.path.abspath(os.path.join(HERE, "..", ".."))   # the repo root

HEAD = ('<!doctype html>\n<html lang="ur" dir="rtl">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        '<meta name="robots" content="noindex, nofollow">\n')


def full_document(body_html):
    """Artifact-form page (starts with <title>…<style>…</style>) -> full HTML document."""
    cut = body_html.index("</style>") + len("</style>")
    return HEAD + body_html[:cut] + "\n</head>\n<body>\n" + body_html[cut:] + "\n</body>\n</html>\n"


def build(script, out_name, env_home="../"):
    env = dict(os.environ, CARDS_HOME=env_home)
    subprocess.run([sys.executable, script], cwd=HERE, env=env, check=True, capture_output=True)
    with open(os.path.join(HERE, out_name), encoding="utf-8") as f:
        return f.read()


PAGES = [
    # (folder, file, builder, built html, audio files {site path: source})
    ("mishkat1", "iman.html", "m1_build.py", "mishkat1_cards.html", {}),
]
REMOVE = ["hidaya4/audio/2025-05-18.mp4"]   # superseded files

HOME = """<title>وفاق 1448 کارڈ</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&family=Noto+Naskh+Arabic:wght@400;600;700&family=Noto+Nastaliq+Urdu:wght@400;600&display=swap">
<style>
/* layout: one narrow column — papers in exam order, each with its card pages */
:root {
  --paper: #FDFCFB; --surface: #FFFFFF; --ink: #1F1A1B; --muted: #6E6566; --rule: #E9E3E2;
  --matn: #A3211A; --matn-tint: #FBEDEB; --teacher: #17624C; --teacher-tint: #E3F2EC;
  --book: #2B4B7E; --ai: #8A5A00; --ai-tint: #FBF0DA;
  --ui: "Noto Naskh Arabic", "Segoe UI", Tahoma, sans-serif;
  --arabic: "Amiri", "Noto Naskh Arabic", serif;
  --urdu: "Noto Nastaliq Urdu", "Jameel Noori Nastaleeq", "Noto Naskh Arabic", serif;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) { color-scheme: dark;
    --paper: #141112; --surface: #1D191A; --ink: #EFE9E8; --muted: #A99F9F; --rule: #342E2F;
    --matn: #F07B6F; --matn-tint: #3A1F1D; --teacher: #5CC7A2; --teacher-tint: #173229; --book: #93B2EA;
    --ai: #E7B25B; --ai-tint: #34290F; }
}
:root[data-theme="dark"] { color-scheme: dark;
  --paper: #141112; --surface: #1D191A; --ink: #EFE9E8; --muted: #A99F9F; --rule: #342E2F;
  --matn: #F07B6F; --matn-tint: #3A1F1D; --teacher: #5CC7A2; --teacher-tint: #173229; --book: #93B2EA;
  --ai: #E7B25B; --ai-tint: #34290F; }
* { box-sizing: border-box; }
[hidden] { display: none !important; }
body { margin: 0; background: var(--paper); color: var(--ink); font-family: var(--ui); font-size: 15px; padding-inline: 16px; padding-block: 0 48px; }
.wrap { max-width: 720px; margin: 0 auto; }
header { padding-block: 32px 8px; display: grid; gap: 6px; }
.eyebrow { color: var(--muted); font-size: 13px; }
h1 { margin: 0; font-family: var(--arabic); color: var(--matn); font-size: clamp(32px, 7vw, 44px); line-height: 1.3; }
.lead { margin: 0; color: var(--muted); line-height: 2; font-size: 14px; max-width: 62ch; }
ol.papers { list-style: none; margin: 18px 0 0; padding: 0; display: grid; gap: 12px; }
.paper { background: var(--surface); border: 1px solid var(--rule); border-radius: 12px; padding: 14px 16px; display: grid; gap: 8px; }
.paper-head { display: flex; flex-wrap: wrap; align-items: baseline; gap: 4px 10px; }
.paper-head .n { color: var(--muted); font-size: 12.5px; font-variant-numeric: tabular-nums; }
.paper-head h2 { margin: 0; font-size: 17px; font-weight: 700; }
.paper-head .date { margin-inline-start: auto; color: var(--muted); font-size: 12.5px; }
ul.links { list-style: none; margin: 0; padding: 0; display: grid; gap: 6px; }
ul.links a { display: flex; flex-wrap: wrap; align-items: baseline; gap: 4px 10px; text-decoration: none; color: inherit;
  border: 1px solid var(--rule); border-radius: 10px; padding: 8px 12px; }
ul.links a:hover, ul.links a:focus-visible { border-color: var(--teacher); }
ul.links .t { font-family: var(--arabic); font-size: 18px; color: var(--matn); }
ul.links .d { color: var(--muted); font-size: 13px; }
ul.links .tag { font-size: 12px; font-weight: 600; border-radius: 999px; padding: 0 8px; }
.tag.sample { color: var(--ai); background: var(--ai-tint); }
.tag.audio { color: var(--teacher); background: var(--teacher-tint); }
.soon { margin: 0; color: var(--muted); font-size: 13px; }
section.how { margin-block-start: 26px; border-top: 1px solid var(--rule); padding-block-start: 14px; display: grid; gap: 6px; }
section.how h2 { margin: 0; font-size: 15px; }
section.how ul { margin: 0; padding-inline-start: 18px; color: var(--muted); font-size: 13.5px; line-height: 2.1; }
:focus-visible { outline: 2px solid var(--book); outline-offset: 2px; border-radius: 6px; }
</style>

<div class="wrap">
  <header>
    <div class="eyebrow">عالمیہ سال اول (موقوف علیہ) · وفاق المدارس 1448 · امتحان 9–14 جنوری 2027</div>
    <h1 lang="ar">تمہیدی کارڈ</h1>
    <p class="lead">ہر کارڈ میں استاد کی تمہید، مسئلہ اور مشکل الفاظ ہیں، صفحہ نمبر اور ریکارڈنگ کے وقت کے ساتھ۔ سبز وقت پر ٹیپ کریں تو استاد کی آواز وہیں سے چلتی ہے۔</p>
  </header>
  <ol class="papers">
__PAPERS__
  </ol>
  <section class="how">
    <h2>استعمال</h2>
    <ul>
      <li>سبز وقت = استاد کی ریکارڈنگ؛ نیلی علامت = کتاب کا متن؛ سرمئی = حاشیے میں منقول شرح؛ پیلی = AI کی لکھی ہوئی، خود جانچیں۔</li>
      <li>ہدایہ کے صفحہ نمبر ساتھیوں والے نسخے کے ہیں (مسلسل صفحات، جلد رابع ص 1595 سے)۔</li>
      <li>ہر صفحے کے اوپر «ریکارڈنگز» کے بٹن میں ہلکی فائلیں (3–9 MB) اور اصل ریکارڈنگ کا ڈاؤن لوڈ ہے۔</li>
    </ul>
  </section>
</div>
"""

PAPERS = [
    ("1", "التبیان، تیسیر مصطلح الحدیث، شرح نخبۃ الفکر، آئینہ قادیانیت", "", []),
    ("2", "بیضاوی (ربع پارہ اول)", "", []),
    ("3", "مشکوٰۃ المصابیح جلد اول", "پیر 11 جنوری",
     [("mishkat1/iman.html", "كتاب الإيمان", "الفصل الأول · 2 حدیثیں", ["sample"])]),
    ("4", "مشکوٰۃ المصابیح جلد دوم", "", []),
    ("5", "ہدایہ جلد ثالث", "", []),
    ("6", "ہدایہ جلد رابع", "", "__H4__"),
]
TAGS = {"sample": "نمونہ", "audio": "آواز یہیں"}


def home_html(h4_links):
    items = []
    for n, name, date, links in PAPERS:
        if links == "__H4__":
            links = h4_links
        if links:
            lis = "".join(
                f'<li><a href="{href}"><span class="t" lang="ar">{t}</span><span class="d">{d}</span>'
                + "".join(f'<span class="tag {tg}">{TAGS[tg]}</span>' for tg in tags) + "</a></li>"
                for href, t, d, tags in links)
            body = f'<ul class="links">{lis}</ul>'
        else:
            body = '<p class="soon">کارڈ جلد آ رہے ہیں۔</p>'
        items.append(f'    <li class="paper"><div class="paper-head"><span class="n">پرچہ {n}</span><h2>{name}</h2>'
                     f'</div>{body}</li>')
    return HOME.replace("__PAPERS__", "\n".join(items))


def main():
    os.makedirs(SITE, exist_ok=True)
    sys.path.insert(0, HERE)
    os.chdir(HERE)
    import h4_site
    h4_pages, h4_audio, D = h4_site.pages()
    for rel, body in h4_pages.items():
        dst = os.path.join(SITE, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "w", encoding="utf-8") as f:
            f.write(full_document(body))
    for rel, src in h4_audio.items():
        dst = os.path.join(SITE, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.abspath(src) != os.path.abspath(dst) and (not os.path.exists(dst) or os.path.getsize(dst) != os.path.getsize(src)):
            shutil.copyfile(src, dst)
    for rel in REMOVE:
        if os.path.exists(os.path.join(SITE, rel)):
            os.remove(os.path.join(SITE, rel))
    done = [k for k in D["kitabs"] if k["cards"]]
    n = sum(len(k["cards"]) for k in done)
    h4_links = [("hidaya4/", "فہرست", f"{len(done)} کتابیں ({'، '.join(k['title'].replace('كتاب ', '') for k in done)}) · {n} کارڈ", ["audio"])]
    for folder, fname, script, built, audio in PAGES:
        page = full_document(build(script, built))
        os.makedirs(os.path.join(SITE, folder), exist_ok=True)
        with open(os.path.join(SITE, folder, fname), "w", encoding="utf-8") as f:
            f.write(page)
        for rel, src in audio.items():
            dst = os.path.join(SITE, folder, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if not os.path.exists(dst) or os.path.getsize(dst) != os.path.getsize(src):
                shutil.copyfile(src, dst)
    with open(os.path.join(SITE, "index.html"), "w", encoding="utf-8") as f:
        f.write(full_document(home_html(h4_links)))
    with open(os.path.join(SITE, "robots.txt"), "w") as f:
        f.write("User-agent: *\nDisallow: /\n")
    open(os.path.join(SITE, ".nojekyll"), "w").close()
    with open(os.path.join(SITE, "README.md"), "w", encoding="utf-8") as f:
        f.write("# Wifaq 1448 — تمہیدی کارڈ\n\nStudy cards for the Wifaq ul Madaris Alamiya year-1 papers, built from class "
                "recordings. The pages at the top level are generated: edit the sources in `src/` and run "
                "`cd src/cards && python3 build_site.py`.\n\nStart with [`src/HANDOVER.md`](src/HANDOVER.md).\n")
    print("site built in", SITE)


if __name__ == "__main__":
    main()
