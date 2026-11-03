"""Hidaya 3 pages for the site: one page per kitab (kitab_template.html) + the paper's contents page.

pages() -> ({"hidaya3/index.html": html, "hidaya3/sarf.html": html, ...}, {"hidaya3/audio/x.ogg": source path}, D)
With no Hidaya 3 cards at all, pages() returns ({}, {}, D): build_site then writes no hidaya3/ page and no home link.
Page numbers are Bushra vol-5 printed pages (the colleagues' edition of Hidaya 3 is not known yet); the pages say so.
"""
import html, json, os
import h3_data
from h4_site import SECTIONS, PAPER_CSS

HERE = os.path.dirname(os.path.abspath(__file__))
BOOK = "ہدایہ جلد ثالث"
PAGES_NOTE = ("صفحہ نمبر مکتبۃ البشریٰ کے آٹھ جلدی نسخے کی جلد ٥ کے چھپے ہوئے صفحات ہیں، ساتھیوں والے نسخے کے نہیں "
              "(ہدایہ جلد ثالث کے لیے اس نسخے کی فہرست ابھی نہیں ملی؛ ملنے پر نمبر بدل دیے جائیں گے)۔")
FOOTER = [
    PAGES_NOTE + " اصل جگہ کارڈ کی پہلی عربی سطر سے پہچانیں۔",
    "«اس سال کی کلاس» = اس سال (1448) کی کلاس کی ریکارڈنگ۔ «پچھلے سال کی کلاس» = پچھلے سال کی ریکارڈنگ، صرف اس حصے کے لیے جس کی اس سال کی ریکارڈنگ نہیں ملی۔",
    "ٹرانسکرپٹ ریکارڈنگ سے Gemini نے بنایا اور اس کے وقت آواز سے ملا کر درست کیے گئے۔ کارڈ اسی ٹرانسکرپٹ، کتاب کے متن اور حاشیے سے بنے ہیں؛ ہر سطر کے آخر میں اس کا ماخذ ہے۔",
    "پیلی (AI) علامت والی سطریں خود جانچیں۔ امتحان میں مسئلہ، اختلاف اور دلیل سبز، نیلی یا سرمئی علامت والی سطروں سے لکھیں۔",
]


def card_json(c):
    d = {k: c.get(k) for k in ("unit", "pages", "lesson", "ts", "label", "title", "start", "start_note", "norec", "badges", "exam")}
    d["v7"] = h3_data.v5_label(c["v5a"], c.get("v5b") or c["v5a"])     # the template's Bushra-page field
    for key, _ in SECTIONS:
        d[key] = [{"x": t, "s": s} for t, s in (c.get(key) or [])]
    d["lughat"] = [{"ar": a, "ur": u, "s": s} for a, u, s in (c.get("lughat") or [])]
    return d


def pages():
    D = h3_data.build()
    if not any(k["cards"] for k in D["kitabs"]):
        return {}, {}, D
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
            lessons[d] = {x: y for x, y in D["lessons"][d].items() if not x.startswith("_")}
            for rel, src in D["lessons"][d].get("_files", {}).items():
                audio[f"hidaya3/{rel}"] = src
        data = {
            "book": {"book": BOOK, "kitab": k["title"], "from": k["page_from"], "to": k["page_to"], "unit": "کارڈ", "unitOne": "کارڈ"},
            "home": "./", "homeLabel": BOOK, "store": "h3",
            "lessons": lessons, "units": k["units"], "cards": [card_json(c) for c in k["cards"]],
            "gaps": [{x: g[x] for x in ("unit", "pages", "page_list", "v7", "text")} for g in k["gaps"]],
            "kitabs": kit_index, "sections": SECTIONS, "quick": ["tamheed", "masala"], "footer": FOOTER,
        }
        page = tpl.replace("__TITLE__", html.escape(f"{k['title']} · {BOOK}")).replace(
            "__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
        out[f"hidaya3/{k['slug']}.html"] = page
    out["hidaya3/index.html"] = paper_page(D)
    return out, audio, D


def summary(D):
    """For the home page: (kitabs with cards, total cards, any audio)."""
    done = [k for k in D["kitabs"] if k["cards"]]
    return done, sum(len(k["cards"]) for k in done), any(L.get("web") for L in D["lessons"].values())


def paper_page(D):
    rows, total = [], 0
    for k in D["kitabs"]:
        n = len(k["cards"])
        total += n
        rng = f'<span class="pp">⁦{k["page_from"]}–{k["page_to"]}⁩</span>'
        tt = f'<span class="tt" lang="ar">{html.escape(k["title"])}</span><span class="dots"></span>{rng}'
        if n:
            units = sum(1 for u in k["units"] if u["level"] > 1)
            les = sorted({c["lesson"] for c in k["cards"] if c.get("lesson")})
            ty = sum(1 for l in les if D["lessons"][l]["source"] == "this-year")
            ly = len(les) - ty
            yrs = "، ".join(x for x in (f"اس سال کی کلاس {ty}" if ty else "", f"پچھلے سال کی کلاس {ly}" if ly else "") if x)
            sub = f"<b>{n} کارڈ</b>، {len(les)} اسباق ({yrs})" + (f"، {units + 1} حصے" if units else "")
            rows.append(f'<li><a class="row" href="{k["slug"]}.html">{tt}</a><div class="sub">{sub}</div></li>')
        else:
            rows.append(f'<li><div class="row">{tt}</div><div class="sub">ابھی کارڈ نہیں</div></li>')
    kit = json.dumps([{"t": k["title"], "f": k["page_from"], "to": k["page_to"], "h": f'{k["slug"]}.html' if k["cards"] else ""}
                      for k in D["kitabs"]], ensure_ascii=False)
    first, last = D["kitabs"][0]["page_from"], D["kitabs"][-1]["page_to"]
    return f"""<title>{BOOK} · تمہیدی کارڈ</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&family=Noto+Naskh+Arabic:wght@400;600;700&display=swap">
<style>{PAPER_CSS}
.note {{ margin: 6px 0 0; background: var(--ai-tint); border-radius: 8px; padding: 7px 12px; font-size: 13.5px; line-height: 1.9; }}</style>
<div class="wrap" dir="rtl" lang="ur">
  <header>
    <a class="homelink" href="../">→ تمام پرچے</a>
    <h1>{BOOK}</h1>
    <p class="lead">کتابیں اسی ترتیب سے جیسے کتاب کی فہرست میں ہیں۔ کسی کتاب کو کھولیں تو اس کے باب اور فصلیں آتی ہیں، ہر فصل کے نیچے اس کے صفحات۔ اب تک {total} کارڈ۔</p>
    <p class="note">{PAGES_NOTE}</p>
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
      <li>صفحہ نمبر بشریٰ (آٹھ جلدی) کی جلد ٥ کے ہیں، ساتھیوں والے نسخے کے نہیں۔</li>
      <li>ہر سبق کے ساتھ لکھا ہے کہ وہ «اس سال کی کلاس» کا ہے یا «پچھلے سال کی کلاس» کا۔ پچھلے سال کی ریکارڈنگ صرف وہاں لی گئی ہے جہاں اس سال کی نہیں ملی۔</li>
      <li>سبز وقت پر ٹیپ کریں تو استاد کی آواز اسی صفحے پر وہیں سے چلتی ہے۔ ہلکی فائلیں «ریکارڈنگز» کے بٹن میں ہیں۔</li>
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
  msg.textContent = k ? `صفحہ ${{p}} «${{k.t}}» میں ہے؛ اس کے کارڈ ابھی نہیں بنے۔` : `صفحہ ${{p}} یہاں نہیں (بشریٰ جلد ٥، ص {first}–{last})۔`;
}});
</script>
"""


if __name__ == "__main__":
    out, audio, D = pages()
    for k, v in out.items():
        print(k, len(v))
    print(len(audio), "audio files")
