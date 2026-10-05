import csv, json, os
import m1_cards as mc

HERE = os.path.dirname(os.path.abspath(__file__))
IDS_CSV = os.path.join(HERE, "..", "data", "recordings.csv")
if os.path.exists(IDS_CSV):
    with open(IDS_CSV, encoding="utf-8-sig") as f:
        ids = {}
        for r in csv.DictReader(f):
            r = {k.replace("\\", "").strip(): (v or "").replace("\\", "").strip() for k, v in r.items()}
            ids[r["file"]] = r
    for L in mc.LESSONS.values():
        r = ids.get(L["file"])
        if r:
            L["id"] = L["id"] or r.get("drive_id", "")
            L["size_mb"] = L["size_mb"] or (float(r["size_mb"]) if r.get("size_mb") else None)


def card_json(c):
    d = {k: c.get(k) for k in ("lesson", "ts", "label", "title", "start", "ref", "badges")}
    d["unit"] = "u1"
    d["pages"] = []
    for key, _ in mc.SECTIONS:
        d[key] = [{"x": t, "s": s} for t, s in (c.get(key) or [])]
    d["lughat"] = [{"ar": a, "ur": u, "s": s} for a, u, s in c["lughat"]]
    return d


data = {"book": mc.BOOK, "lessons": mc.LESSONS, "cards": [card_json(c) for c in mc.CARDS], "gaps": [],
        "units": [{"key": "u1", "level": 3, "title": "الفصل الأول"}], "store": "m1",
        "sections": mc.SECTIONS, "quick": mc.QUICK, "footer": mc.FOOTER}
if os.environ.get("CARDS_HOME"):
    data["home"] = os.environ["CARDS_HOME"]
    data["homeLabel"] = "تمام پرچے"
tpl = open(os.path.join(HERE, "kitab_template.html"), encoding="utf-8").read()
page = tpl.replace("__TITLE__", "مشکوٰۃ حدیث کارڈ").replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
open(os.path.join(HERE, "mishkat1_cards.html"), "w", encoding="utf-8").write(page)

# markdown copy for the project
md = [f"# {mc.BOOK['book']} · {mc.BOOK['kitab']} — حدیث کارڈ (نمونہ)", "", mc.BOOK["edition"], ""]
for i, c in enumerate(mc.CARDS, 1):
    L = mc.LESSONS[c["lesson"]]
    md += [f"## {i}. {c['title']}", "", f"{c['group']} · «{c['start']}» · {c['ref']} · {L['file']} @ {c['ts']}", ""]
    for key, label in mc.SECTIONS:
        items = c.get(key) or []
        if items:
            md.append(f"**{label}:**")
            md += [f"- {t} [{'؛ '.join(('استاد ' + s['v']) if s['t'] == 'u' else 'AI — تصدیق طلب' for s in ss)}]" for t, ss in items]
            md.append("")
    md.append("**مشکل الفاظ:**")
    md += [f"- {a} = {u} [{'؛ '.join(('استاد ' + s['v']) if s['t'] == 'u' else 'AI' for s in ss)}]" for a, u, ss in c["lughat"]]
    md.append("")
open(os.path.join(HERE, "mishkat1_iman_sample.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
print("built", len(page), "bytes; ids:", [L["id"] for L in mc.LESSONS.values()])
