import csv, json, os
import h4_cards as hc

# Drive IDs and sizes come from the Colab inventory (recording_ids.csv), matched by file name.
IDS_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "recording_ids.csv")
if os.path.exists(IDS_CSV):
    with open(IDS_CSV, encoding="utf-8-sig") as f:
        ids = {}
        for r in csv.DictReader(f):
            r = {k.replace("\\", "").strip(): (v or "").replace("\\", "").strip() for k, v in r.items()}
            ids[r["file"]] = r
    for k, L in hc.LESSONS.items():
        r = ids.get(L["file"])
        if r:
            L["id"] = L["id"] or r.get("drive_id", "")
            L["size_mb"] = L["size_mb"] or (float(r["size_mb"]) if r.get("size_mb") else None)
    print("Drive IDs:", sum(1 for L in hc.LESSONS.values() if L["id"]), "of", len(hc.LESSONS))

SECTIONS = [("tamheed", "تمہید"), ("masala", "مسئلہ"), ("dalil", "دلیل"),
            ("ikhtilaf", "اختلاف"), ("faida", "فائدہ")]


def src_md(s, lesson):
    t, v = s["t"], s["v"]
    if t == "u":
        l = s.get("l") or lesson
        return f"استاد {hc.LESSONS[l]['label']} {v}"
    return {"k": f"کتاب ص {v}", "s": f"شرح: {v}", "a": "AI — تصدیق طلب"}[t]


def pages_label(ps):
    return f"{ps[0]}" if len(ps) == 1 else f"{ps[0]}–{ps[-1]}"


# ---- markdown (for Drive / project)
B = hc.BOOK
allp = sorted({p for c in hc.CARDS for p in c["pages"]})
md = [f"# {B['kitab']} — تمہیدی کارڈ (ص {allp[0]}–{allp[-1]})", "",
      f"{B['book']} · {B['bab']} · {B['edition']}", "",
      "ماخذ: [استاد تاریخ وقت] = ریکارڈنگ · [کتاب ص] = متن (ساتھیوں والا نسخہ) · [شرح: …] = حاشیے میں منقول شرح یا بین السطور · [AI — تصدیق طلب] = خود جانچیں", ""]
for i, c in enumerate(hc.CARDS, 1):
    l = c["lesson"]
    rec = f"{hc.LESSONS[l]['file']} @ {c['ts']}" if l else "ریکارڈنگ نہیں"
    md += [f"## {i}. {c['title']}", ""]
    if c.get("label"):
        md += [f"({c['label']})", ""]
    md += [f"ص {pages_label(c['pages'])} · {rec} · شروع: «{c['start']}»", ""]
    if c.get("norec"):
        md += [f"> توجہ: {c['norec']}", ""]
    for key, label in SECTIONS:
        items = c.get(key) or []
        if items:
            md.append(f"**{label}:**")
            md += [f"- {t} [{'؛ '.join(src_md(s, l) for s in ss)}]" for t, ss in items]
            md.append("")
    md.append("**مشکل الفاظ:**")
    md += [f"- {a} = {u} [{'؛ '.join(src_md(s, l) for s in ss)}]" for a, u, ss in c["lughat"]]
    md.append("")
md += ["## جن حصوں کی ریکارڈنگ نہیں", ""] + [f"- ص {p}: {t}" for p, t in hc.GAPS] + [""]
N = hc.NEXT
md += [f"## اگلا سبق: {hc.LESSONS[N['lesson']]['file']} ({N['pages_hint']})", ""]
md += [f"- {ts} · «{ar}» — {ur}" for ts, ar, ur in N["items"]]
open(f"hidaya4_shufa_{allp[0]}-{allp[-1]}.md", "w", encoding="utf-8").write("\n".join(md) + "\n")


# ---- html
def card_json(c):
    d = {k: c.get(k) for k in ("pages", "lesson", "ts", "label", "title", "start", "start_note", "norec")}
    for key, _ in SECTIONS:
        d[key] = [{"x": t, "s": s} for t, s in (c.get(key) or [])]
    d["lughat"] = [{"ar": a, "ur": u, "s": s} for a, u, s in c["lughat"]]
    return d


data = {"book": B, "lessons": hc.LESSONS, "cards": [card_json(c) for c in hc.CARDS],
        "gaps": [{"pages": p, "text": t} for p, t in hc.GAPS],
        "next": {"lesson": N["lesson"], "pages_hint": N["pages_hint"],
                 "items": [{"ts": a, "ar": b, "ur": c} for a, b, c in N["items"]]},
        "sections": SECTIONS, "quick": ["tamheed", "masala"],
        "footer": [
            "ٹرانسکرپٹ ریکارڈنگ سے Gemini نے بنایا؛ کارڈ اسی ٹرانسکرپٹ، کتاب کے متن اور حاشیے سے بنے ہیں۔ ہر سطر کے آخر میں اس کا ماخذ ہے۔",
            "صفحہ نمبر ساتھیوں والے نسخے کے ہیں۔ استاد کلاس میں اپنے نسخے کے صفحے بولتے ہیں (مثلاً باب طلب الشفعة کو 1644)، جو اس نسخے سے مختلف ہیں۔",
            "پیلی علامت والی سطریں اور لغات خود جانچیں؛ امتحان میں مسئلہ، اختلاف اور دلیل سبز، نیلی یا سرمئی علامت والی سطروں سے لکھیں۔"]}
if os.environ.get("CARDS_HOME"):
    data["home"] = os.environ["CARDS_HOME"]
tpl = open("h4_template.html", encoding="utf-8").read()
page = tpl.replace("__TITLE__", "ہدایہ رابع کارڈ").replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
open("hidaya4_cards.html", "w", encoding="utf-8").write(page)
print("built", len(page), "bytes;", len(hc.CARDS), "cards")
