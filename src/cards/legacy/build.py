import json, html
import sarf_cards as sc

SECTIONS = [("tamheed", "تمہید"), ("masala", "مسئلہ"), ("dalil", "دلیل"),
            ("ikhtilaf", "اختلاف"), ("faida", "فائدہ")]


def src_md(s):
    t, v = s["t"], s["v"]
    return {"u": f"استاد {v}", "k": f"کتاب ص {v}", "h": f"حاشیہ ص {v}", "a": "AI — تصدیق طلب"}[t]


def pages_label(ps):
    return f"{ps[0]}" if len(ps) == 1 else f"{ps[0]}–{ps[-1]}"


# ---------------------------------------------------------------- markdown (for Drive)
md = [f"# {sc.LESSON['kitab']} — تمہیدی کارڈ",
      "",
      f"{sc.LESSON['book']} ({sc.LESSON['edition']}) · صفحات {sc.LESSON['pages'][0]}–{sc.LESSON['pages'][-1]} · "
      f"ریکارڈنگ: {sc.LESSON['file']} ({sc.LESSON['minutes']} منٹ) · ٹرانسکرپٹ: {sc.LESSON['model']}",
      "",
      "ماخذ: [استاد وقت] = ریکارڈنگ · [کتاب ص] = متن · [حاشیہ ص] = کتاب کا حاشیہ · [AI — تصدیق طلب] = خود جانچیں",
      ""]
for i, c in enumerate(sc.CARDS, 1):
    md += [f"## {i}. {c['title']}", "",
           f"ص {pages_label(c['pages'])} · {sc.LESSON['file']} @ {c['ts']} · شروع: «{c['start']}»", ""]
    for key, label in SECTIONS:
        items = c.get(key) or []
        if not items:
            continue
        md.append(f"**{label}:**")
        for text, srcs in items:
            md.append(f"- {text} [{'؛ '.join(src_md(s) for s in srcs)}]")
        md.append("")
    md.append("**مشکل الفاظ:**")
    for ar, ur, srcs in c["lughat"]:
        md.append(f"- {ar} = {ur} [{'؛ '.join(src_md(s) for s in srcs)}]")
    md.append("")
md += ["## اسی سبق کے اگلے حصے (صفحات کی تصاویر ابھی نہیں آئیں)", ""]
for ts, ar, ur in sc.NEXT:
    md.append(f"- {ts} · «{ar}» — {ur}")
open("kitab_al_sarf_253-258.md", "w", encoding="utf-8").write("\n".join(md) + "\n")


# ---------------------------------------------------------------- html viewer
def jsonable():
    out = []
    for c in sc.CARDS:
        d = {"pages": c["pages"], "ts": c["ts"], "title": c["title"], "start": c["start"]}
        for key, _ in SECTIONS:
            d[key] = [{"x": t, "s": s} for t, s in (c.get(key) or [])]
        d["lughat"] = [{"ar": a, "ur": u, "s": s} for a, u, s in c["lughat"]]
        out.append(d)
    return out


data = {"lesson": sc.LESSON, "cards": jsonable(),
        "next": [{"ts": t, "ar": a, "ur": u} for t, a, u in sc.NEXT],
        "sections": SECTIONS}
tpl = open("viewer_template.html", encoding="utf-8").read()
page = tpl.replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
open("hidaya_cards.html", "w", encoding="utf-8").write(page)
print("built", len(page), "bytes")
