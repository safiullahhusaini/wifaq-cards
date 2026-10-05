"""Hidaya 4 pages for the site: one page per kitab (kitab_template.html) + the paper's contents page.

pages() -> ({"hidaya4/index.html": html, "hidaya4/shufa.html": html, ...}, {"hidaya4/audio/x.ogg": source path})
HTML is in the artifact form (starts with <title>); build_site.full_document() wraps it.
"""
import html, json, os
import h4_data

HERE = os.path.dirname(os.path.abspath(__file__))
SECTIONS = [("tamheed", "تمہید"), ("masala", "مسئلہ"), ("dalil", "دلیل"), ("ikhtilaf", "اختلاف"), ("faida", "فائدہ")]
FOOTER = [
    "صفحہ نمبر ساتھیوں والے نسخے (مسلسل صفحات) کے ہیں۔ ص 1609–1611 کتاب سے ملا کر لکھے گئے ہیں؛ باقی بشریٰ کے آٹھ جلدی نسخے (جلد ٧) سے حساب لگا کر، "
    "اس لیے کہیں ایک صفحہ آگے پیچھے ہو سکتا ہے۔ اصل جگہ کارڈ کی پہلی عربی سطر سے پہچانیں؛ بشریٰ کا صفحہ ہر کارڈ پر ساتھ لکھا ہے۔",
    "ٹرانسکرپٹ ریکارڈنگ سے Gemini نے بنایا اور اس کے وقت آواز سے ملا کر درست کیے گئے۔ کارڈ اسی ٹرانسکرپٹ، کتاب کے متن اور حاشیے سے بنے ہیں؛ ہر سطر کے آخر میں اس کا ماخذ ہے۔",
    "پیلی (AI) علامت والی سطریں خود جانچیں۔ امتحان میں مسئلہ، اختلاف اور دلیل سبز، نیلی یا سرمئی علامت والی سطروں سے لکھیں۔",
    "استاد کلاس میں اپنے نسخے کے صفحے بولتے ہیں (مثلاً كتاب المساقاة 1700)؛ وہ اس نسخے سے مختلف ہیں۔",
]


def card_json(c):
    d = {k: c.get(k) for k in ("unit", "pages", "lesson", "ts", "label", "title", "start", "start_note", "norec", "badges")}
    if c.get("v7a"):
        d["v7"] = h4_data.v7_label(c["v7a"], c.get("v7b") or c["v7a"])
    for key, _ in SECTIONS:
        d[key] = [{"x": t, "s": s} for t, s in (c.get(key) or [])]
    d["lughat"] = [{"ar": a, "ur": u, "s": s} for a, u, s in (c.get("lughat") or [])]
    return d


def pages():
    D = h4_data.build()
    tpl = open(os.path.join(HERE, "kitab_template.html"), encoding="utf-8").read()
    kit_index = [{"title": k["title"], "from": k["page_from"], "to": k["page_to"],
                  "href": f"{k['slug']}.html" if k["cards"] else None} for k in D["kitabs"]]
    out, audio = {}, {}
    for k in D["kitabs"]:
        if not k["cards"]:
            continue
        used = sorted({c["lesson"] for c in k["cards"] if c.get("lesson")})
        lessons = {}
        for d in used:
            L = {x: y for x, y in D["lessons"][d].items() if not x.startswith("_")}
            lessons[d] = L
            for rel, src in D["lessons"][d].get("_files", {}).items():
                audio[f"hidaya4/{rel}"] = src
        data = {
            "book": {"book": "ہدایہ جلد رابع", "kitab": k["title"], "from": k["page_from"], "to": k["page_to"], "unit": "کارڈ", "unitOne": "کارڈ"},
            "home": "./", "homeLabel": "ہدایہ جلد رابع", "store": "h4",
            "lessons": lessons, "units": k["units"], "cards": [card_json(c) for c in k["cards"]],
            "gaps": [{x: g[x] for x in ("unit", "pages", "page_list", "v7", "text")} for g in k["gaps"]],
            "kitabs": kit_index, "sections": SECTIONS, "quick": ["tamheed", "masala"], "footer": FOOTER,
        }
        page = tpl.replace("__TITLE__", html.escape(f"{k['title']} · ہدایہ جلد رابع")).replace(
            "__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
        out[f"hidaya4/{k['slug']}.html"] = page
    out["hidaya4/index.html"] = paper_page(D)
    return out, audio, D


PAPER_CSS = """
:root {
  --paper: #FDFCFB; --surface: #FFFFFF; --ink: #1F1A1B; --muted: #6E6566; --rule: #E9E3E2;
  --matn: #A3211A; --teacher: #17624C; --teacher-tint: #E3F2EC; --book: #2B4B7E; --ai: #8A5A00; --ai-tint: #FBF0DA; --focus: #2B4B7E;
  --ui: "Noto Naskh Arabic", "Segoe UI", Tahoma, sans-serif; --arabic: "Amiri", "Noto Naskh Arabic", serif;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) { color-scheme: dark; --paper: #141112; --surface: #1D191A; --ink: #EFE9E8; --muted: #A99F9F; --rule: #342E2F;
    --matn: #F07B6F; --teacher: #5CC7A2; --teacher-tint: #173229; --book: #93B2EA; --ai: #E7B25B; --ai-tint: #34290F; --focus: #93B2EA; }
}
:root[data-theme="dark"] { color-scheme: dark; --paper: #141112; --surface: #1D191A; --ink: #EFE9E8; --muted: #A99F9F; --rule: #342E2F;
  --matn: #F07B6F; --teacher: #5CC7A2; --teacher-tint: #173229; --book: #93B2EA; --ai: #E7B25B; --ai-tint: #34290F; --focus: #93B2EA; }
* { box-sizing: border-box; }
[hidden] { display: none !important; }
body { margin: 0; background: var(--paper); color: var(--ink); font-family: var(--ui); font-size: 15px; padding-inline: 16px; padding-block: 0 48px; }
.wrap { max-width: 720px; margin: 0 auto; }
[lang="ar"] { font-family: var(--arabic); }
:focus-visible { outline: 2px solid var(--focus); outline-offset: 2px; border-radius: 6px; }
header { padding-block: 14px 6px; display: grid; gap: 4px; }
.homelink { justify-self: start; color: var(--book); font-size: 13.5px; font-weight: 600; text-decoration: none; padding-block: 6px; }
h1 { margin: 6px 0 0; font-family: var(--arabic); color: var(--matn); font-size: clamp(34px, 8vw, 46px); line-height: 1.3; }
.lead { margin: 0; color: var(--muted); font-size: 14px; line-height: 2; max-width: 62ch; }
.tochead { display: flex; flex-wrap: wrap; align-items: center; gap: 8px 14px; margin-block: 16px 4px; }
.tochead h2 { margin: 0; font-size: 15px; color: var(--muted); }
form.jump { display: flex; gap: 4px; margin-inline-start: auto; }
form.jump input { inline-size: 92px; border: 1px solid var(--rule); background: var(--surface); color: var(--ink); border-radius: 999px; padding: 5px 12px; font: inherit; font-size: 14px; direction: ltr; text-align: center; }
form.jump button { cursor: pointer; border: 1px solid var(--ink); background: var(--ink); color: var(--paper); border-radius: 999px; padding: 5px 13px; font: inherit; font-size: 13.5px; }
.msg { margin: 8px 0 0; background: var(--ai-tint); border-radius: 8px; padding: 7px 12px; font-size: 13.5px; line-height: 1.9; }
ol.toc { list-style: none; margin: 6px 0 0; padding: 0; border-top: 1px solid var(--rule); }
.toc li { border-bottom: 1px solid var(--rule); padding-block: 11px 10px; display: grid; gap: 3px; }
.toc .row { display: flex; align-items: baseline; gap: 8px; text-decoration: none; color: inherit; }
.toc .tt { font-family: var(--arabic); font-size: 22px; line-height: 1.6; color: var(--muted); }
.toc a.row .tt { color: var(--matn); font-weight: 700; }
.toc a.row:hover .tt, .toc a.row:focus-visible .tt { text-decoration: underline; text-decoration-thickness: 1px; text-underline-offset: 6px; }
.toc .dots { flex: 1 1 24px; min-inline-size: 24px; border-bottom: 2px dotted var(--rule); transform: translateY(-5px); }
.toc .pp { color: var(--muted); font-size: 14px; font-variant-numeric: tabular-nums; white-space: nowrap; }
.toc .sub { font-size: 12.5px; color: var(--muted); }
.toc .sub b { color: var(--teacher); font-weight: 600; }
section.how { margin-block-start: 26px; border-top: 1px solid var(--rule); padding-block-start: 14px; display: grid; gap: 6px; }
section.how h2 { margin: 0; font-size: 15px; }
section.how ul { margin: 0; padding-inline-start: 18px; color: var(--muted); font-size: 13.5px; line-height: 2.1; }
"""


def paper_page(D):
    rows = []
    total = 0
    for k in D["kitabs"]:
        n = len(k["cards"])
        total += n
        rng = f'<span class="pp">\u2066{k["page_from"]}–{k["page_to"]}\u2069</span>'
        tt = f'<span class="tt" lang="ar">{html.escape(k["title"])}</span><span class="dots"></span>{rng}'
        if n:
            units = sum(1 for u in k["units"] if u["level"] > 1)
            lessons = len({c["lesson"] for c in k["cards"] if c.get("lesson")})
            sub = f"<b>{n} کارڈ</b>، {lessons} اسباق" + (f"، {units + 1} حصے" if units else "")
            rows.append(f'<li><a class="row" href="{k["slug"]}.html">{tt}</a><div class="sub">{sub}</div></li>')
        else:
            rows.append(f'<li><div class="row">{tt}</div><div class="sub">ابھی کارڈ نہیں</div></li>')
    kit = json.dumps([{"t": k["title"], "f": k["page_from"], "to": k["page_to"], "h": f'{k["slug"]}.html' if k["cards"] else ""}
                      for k in D["kitabs"]], ensure_ascii=False)
    return f"""<title>ہدایہ جلد رابع · تمہیدی کارڈ</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&family=Noto+Naskh+Arabic:wght@400;600;700&display=swap">
<style>{PAPER_CSS}</style>
<div class="wrap" dir="rtl" lang="ur">
  <header>
    <a class="homelink" href="../">→ تمام پرچے</a>
    <h1>ہدایہ جلد رابع</h1>
    <p class="lead">کتابیں اسی ترتیب سے جیسے کتاب کی فہرست میں ہیں۔ کسی کتاب کو کھولیں تو اس کے باب اور فصلیں آتی ہیں، ہر فصل کے نیچے اس کے صفحات۔ اب تک {total} کارڈ۔</p>
  </header>
  <div class="tochead">
    <h2>فہرست</h2>
    <form class="jump" id="jump" role="search"><input inputmode="numeric" placeholder="صفحہ نمبر" aria-label="صفحہ نمبر"><button type="submit">کھولیں</button></form>
  </div>
  <p class="msg" id="msg" hidden></p>
  <ol class="toc">
{chr(10).join("    " + r for r in rows)}
  </ol>
  <section class="how">
    <h2>استعمال</h2>
    <ul>
      <li>صفحہ نمبر ساتھیوں والے نسخے کے ہیں (مسلسل صفحات، جلد رابع ص 1595 سے)؛ ہر کارڈ پر بشریٰ (آٹھ جلدی) کا صفحہ بھی لکھا ہے۔</li>
      <li>سبز وقت پر ٹیپ کریں تو استاد کی آواز اسی صفحے پر وہیں سے چلتی ہے۔ ہلکی فائلیں اور اصل ریکارڈنگ «ریکارڈنگز» کے بٹن میں ہیں۔</li>
      <li>سبز = استاد کی ریکارڈنگ، نیلا = کتاب کا متن، سرمئی = حاشیہ یا شرح، پیلا = AI کی لکھی ہوئی سطر، خود جانچیں۔</li>
    </ul>
  </section>
</div>
<script>
const KITABS = {kit};
const toLatin = (v) => String(v).replace(/[۰-۹]/g, (d) => "۰۱۲۳۴۵۶۷۸۹".indexOf(d)).replace(/[٠-٩]/g, (d) => "٠١٢٣٤٥٦٧٨٩".indexOf(d)).trim();
document.getElementById("jump").addEventListener("submit", (e) => {{
  e.preventDefault();
  const v = toLatin(e.target.querySelector("input").value || ""), msg = document.getElementById("msg");
  if (!/^\\d+$/.test(v)) return;
  const p = +v, k = KITABS.find((x) => x.f <= p && p <= x.to);
  if (k && k.h) {{ location.href = `${{k.h}}#p${{p}}`; return; }}
  msg.hidden = false;
  msg.textContent = k ? `صفحہ ${{p}} «${{k.t}}» میں ہے؛ اس کے کارڈ ابھی نہیں بنے۔` : `صفحہ ${{p}} جلد رابع میں نہیں (ص 1595–2004)۔`;
}});
</script>
"""


if __name__ == "__main__":
    out, audio, D = pages()
    for k, v in out.items():
        print(k, len(v))
    print(len(audio), "audio files")
