"""Hifz page: the 38 syllabus hadith (Mishkat), with a practice mode and a per-phone memorised/revision tracker.

Writes mishkat1_hifz.html in artifact form (<title>…<style>…</style> then body); build_site.py wraps it.
Progress is kept in this phone's browser only (localStorage), like the tracker's 2 / 7 / 21-day revision rule.
"""
import json, os
from m1_hifz_data import GROUPS, H

HERE = os.path.dirname(os.path.abspath(__file__))
HOME = os.environ.get("CARDS_HOME", "")

data = {
    "groups": [{"k": k, "t": t, "d": d} for k, t, d in GROUPS],
    "h": [{"g": g, "n": n, "s": s, "i": i, "m": m, "t": t, "note": note, "ai": ai}
          for g, n, s, i, m, t, note, ai in H],
}

PAGE = r"""<title>حفظِ احادیث</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&family=Noto+Naskh+Arabic:wght@400;500;600;700&display=swap">
<style>
:root {
  --paper: #FDFCFB; --surface: #FFFFFF; --ink: #1F1A1B; --muted: #6E6566; --rule: #E9E3E2;
  --matn: #A3211A; --matn-tint: #FBEDEB; --teacher: #17624C; --teacher-tint: #E3F2EC;
  --book: #2B4B7E; --book-tint: #E8EEF8; --ai: #8A5A00; --ai-tint: #FBF0DA; --focus: #2B4B7E;
  --shadow: 0 1px 2px rgba(31,26,27,.05), 0 4px 16px rgba(31,26,27,.05);
  --ui: "Noto Naskh Arabic", "Segoe UI", Tahoma, sans-serif;
  --arabic: "Amiri", "Noto Naskh Arabic", "Traditional Arabic", serif;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) { color-scheme: dark;
    --paper: #141112; --surface: #1D191A; --ink: #EFE9E8; --muted: #A99F9F; --rule: #342E2F;
    --matn: #F07B6F; --matn-tint: #3A1F1D; --teacher: #5CC7A2; --teacher-tint: #173229;
    --book: #93B2EA; --book-tint: #1C2638; --ai: #E7B25B; --ai-tint: #34290F; --focus: #93B2EA; --shadow: none; }
}
:root[data-theme="dark"] { color-scheme: dark;
  --paper: #141112; --surface: #1D191A; --ink: #EFE9E8; --muted: #A99F9F; --rule: #342E2F;
  --matn: #F07B6F; --matn-tint: #3A1F1D; --teacher: #5CC7A2; --teacher-tint: #173229;
  --book: #93B2EA; --book-tint: #1C2638; --ai: #E7B25B; --ai-tint: #34290F; --focus: #93B2EA; --shadow: none; }
* { box-sizing: border-box; }
[hidden] { display: none !important; }
html { -webkit-text-size-adjust: 100%; }
body { margin: 0; background: var(--paper); color: var(--ink); font-family: var(--ui); font-size: 15px; padding-inline: 16px; padding-block: 0 60px; }
.wrap { max-width: 760px; margin: 0 auto; }
[lang="ar"] { font-family: var(--arabic); }
button { font: inherit; }
:focus-visible { outline: 2px solid var(--focus); outline-offset: 2px; border-radius: 6px; }
.num { font-variant-numeric: tabular-nums; }

header { padding-block: 14px 6px; display: grid; gap: 4px; }
.homelink { color: var(--book); font-size: 13.5px; font-weight: 600; text-decoration: none; padding-block: 6px; justify-self: start; }
.homelink:hover { text-decoration: underline; }
h1 { margin: 2px 0 0; font-family: var(--arabic); font-weight: 700; color: var(--matn); font-size: clamp(34px, 8vw, 46px); line-height: 1.3; }
.meta { color: var(--muted); font-size: 13.5px; line-height: 2; margin: 0; }
.meta b { color: var(--ink); font-weight: 600; }

/* sticky controls */
.bar { position: sticky; top: 0; z-index: 5; background: var(--paper); margin-inline: -16px; padding: 10px 16px 10px;
  border-bottom: 1px solid var(--rule); display: grid; gap: 8px; }
.prog { display: flex; align-items: center; gap: 10px; font-size: 13.5px; }
.prog .track { flex: 1; height: 6px; border-radius: 999px; background: var(--rule); overflow: hidden; }
.prog .fill { height: 100%; background: var(--teacher); width: 0; transition: width .25s; }
.prog b { font-variant-numeric: tabular-nums; }
.prog .due { color: var(--matn); font-weight: 600; }
.row { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.seg { display: inline-flex; border: 1px solid var(--rule); border-radius: 999px; overflow: hidden; background: var(--surface); }
.seg button, .chip { cursor: pointer; border: 0; background: none; color: var(--ink); padding: 4px 13px; font-size: 13.5px; }
.seg button[aria-pressed="true"] { background: var(--ink); color: var(--paper); }
.chip { border: 1px solid var(--rule); border-radius: 999px; background: var(--surface); }
.chip[aria-pressed="true"] { background: var(--ink); color: var(--paper); border-color: var(--ink); }
.chip .c { font-variant-numeric: tabular-nums; opacity: .75; margin-inline-start: 3px; }
.sp { flex: 1; }

/* groups and cards */
section.grp { padding-block-start: 18px; display: grid; gap: 12px; }
section.grp > h2 { margin: 0; font-family: var(--arabic); color: var(--matn); font-size: 22px; line-height: 1.6; }
section.grp > h2 small { display: block; font-family: var(--ui); color: var(--muted); font-size: 12.5px; font-weight: 400; line-height: 1.7; }
article { background: var(--surface); border: 1px solid var(--rule); border-radius: 12px; box-shadow: var(--shadow); padding: 14px 16px 12px; display: grid; gap: 8px; }
article.done { border-color: color-mix(in srgb, var(--teacher) 35%, var(--rule)); }
.head { display: flex; flex-wrap: wrap; align-items: center; gap: 6px 10px; }
.n { font-weight: 700; font-size: 15px; min-width: 26px; height: 26px; border-radius: 999px; display: inline-grid; place-items: center;
  background: var(--matn-tint); color: var(--matn); font-variant-numeric: tabular-nums; padding-inline: 6px; }
.mno { color: var(--muted); font-size: 12.5px; font-variant-numeric: tabular-nums; }
.sah { font-weight: 600; font-size: 14px; }
.st { margin-inline-start: auto; font-size: 12px; font-weight: 600; border-radius: 999px; padding: 1px 9px; }
.st.ok { color: var(--teacher); background: var(--teacher-tint); }
.st.due { color: var(--matn); background: var(--matn-tint); }
.st.firm { color: var(--book); background: var(--book-tint); }
.txt { font-family: var(--arabic); font-size: 21px; line-height: 2.05; margin: 0; text-align: justify; text-align-last: right; }
.txt .isnad { color: var(--muted); font-size: 18px; }
.txt .tak { color: var(--book); font-size: 17px; white-space: nowrap; }
.hint { font-family: var(--arabic); font-size: 21px; line-height: 2; margin: 0; }
.hint .rest { color: transparent; text-shadow: 0 0 9px color-mix(in srgb, var(--ink) 55%, transparent); user-select: none; }
.notes { display: grid; gap: 4px; }
.note { margin: 0; font-size: 12.5px; line-height: 1.9; color: var(--muted); }
.note.ai { color: var(--ai); background: var(--ai-tint); border-radius: 6px; padding: 1px 8px; justify-self: start; }
.acts { display: flex; flex-wrap: wrap; gap: 6px 8px; align-items: center; border-top: 1px dashed var(--rule); padding-top: 8px; }
.btn { cursor: pointer; border: 1px solid var(--rule); background: var(--surface); color: var(--ink); border-radius: 999px; padding: 4px 13px; font-size: 13.5px; font-weight: 600; }
.btn.main { border-color: var(--teacher); color: var(--teacher); }
.btn.main.due { border-color: var(--matn); color: var(--matn); }
.btn.show { border-color: var(--book); color: var(--book); }
.next { color: var(--muted); font-size: 12.5px; }
.undo { cursor: pointer; border: 0; background: none; color: var(--muted); font-size: 12px; text-decoration: underline; margin-inline-start: auto; padding: 4px 0; }
.empty { color: var(--muted); font-size: 14px; padding-block: 24px; text-align: center; }
footer { margin-top: 28px; border-top: 1px solid var(--rule); padding-top: 12px; color: var(--muted); font-size: 12.5px; line-height: 2; }
</style>

<div class="wrap">
  <header>
    __HOME__
    <h1 lang="ar">حفظ الأحاديث</h1>
    <p class="meta">مشکوٰۃ المصابیح سے نصاب کی <b>38 احادیث</b> · پرچہ 3 (مشکوٰۃ جلد اول) کے ایک سوال کا جز، <b>15 نمبر</b> · پوری سند ضروری نہیں، <b>متن صحابی کے نام کے ساتھ</b> یاد کریں۔</p>
  </header>

  <div class="bar">
    <div class="prog"><span>یاد: <b id="pDone">0</b>/38</span><div class="track"><div class="fill" id="pFill"></div></div><span class="due" id="pDue"></span></div>
    <div class="row">
      <div class="seg" role="group" aria-label="طریقہ">
        <button type="button" data-mode="read" aria-pressed="true">پڑھیں</button>
        <button type="button" data-mode="test" aria-pressed="false">زبانی سنائیں</button>
      </div>
      <span class="sp"></span>
      <button type="button" class="chip" data-f="all" aria-pressed="true">سب<span class="c" id="cAll"></span></button>
      <button type="button" class="chip" data-f="todo" aria-pressed="false">باقی<span class="c" id="cTodo"></span></button>
      <button type="button" class="chip" data-f="due" aria-pressed="false">آج دہرائیں<span class="c" id="cDue"></span></button>
    </div>
  </div>

  <main id="list"></main>
  <p class="empty" id="empty" hidden></p>

  <footer>
    <div>«یاد ہو گئی» دبائیں تو دہرائی خود بتائی جائے گی: 2 دن، پھر 7 دن، پھر 21 دن بعد۔ یہ حساب صرف اسی فون کے براؤزر میں رہتا ہے۔</div>
    <div>متن: مشکوٰۃ المصابیح (تحقیق البانی)، نمبر اسی نسخے کے۔ پہلی تین فصلوں کے اعراب sunnah.com سے؛ باب حفظ اللسان کے اعراب AI نے لگائے ہیں — اپنے نسخے سے ملا لیں۔ جہاں کتاب میں تخریج نہیں لکھی وہاں «بخاری و مسلم» اردو میں لکھا ہے۔</div>
  </footer>
</div>

<script>
const D = __DATA__;
const KEY = "hifz38-v1";
const GAP = [2, 7, 21];
let st = {};
try { st = JSON.parse(localStorage.getItem(KEY) || "{}") || {}; } catch (e) { st = {}; }
let mode = "read", filt = "all";
const shown = new Set();
try { mode = localStorage.getItem(KEY + "-mode") || "read"; } catch (e) {}
const save = () => { try { localStorage.setItem(KEY, JSON.stringify(st)); } catch (e) {} };

const today = () => { const d = new Date(); return new Date(d.getFullYear(), d.getMonth(), d.getDate()); };
const iso = d => d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0");
const parse = s => { const [y, m, d] = s.split("-").map(Number); return new Date(y, m - 1, d); };
const MONTHS = ["جنوری","فروری","مارچ","اپریل","مئی","جون","جولائی","اگست","ستمبر","اکتوبر","نومبر","دسمبر"];
const fmt = d => d.getDate() + " " + MONTHS[d.getMonth()];
function info(n) {
  const s = st[n];
  if (!s) return { k: "todo" };
  if (s.r >= GAP.length) return { k: "firm" };
  const due = new Date(parse(s.m).getTime() + GAP[s.r] * 864e5);
  return { k: due <= today() ? "due" : "ok", due };
}
const esc = s => s.replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const NO_TAK = "بخاری و مسلم";

function hintHtml(h) {
  const words = h.m.split(" ");
  const k = Math.min(3, words.length);
  return '<p class="hint" lang="ar">' + esc(words.slice(0, k).join(" ")) + ' <span class="rest" aria-hidden="true">' +
    esc(words.slice(k, k + 14).join(" ")) + '…</span></p>';
}
function cardHtml(h, idx) {
  const I = info(h.n), open = mode === "read" || shown.has(h.n);
  const stTxt = { ok: "یاد ✓", due: "آج دہرائیں", firm: "پختہ ✓" }[I.k];
  let body;
  if (open) {
    const tak = h.t === "~" ? "" : (h.t ? ' <span class="tak">' + esc(h.t) + '</span>' : "");
    body = '<p class="txt" lang="ar"><span class="isnad">' + esc(h.i) + '</span> ' + esc(h.m) + tak + '</p>';
  } else body = hintHtml(h);
  const notes = [];
  if (open && h.t === "~") notes.push('<p class="note">تخریج: ' + NO_TAK + ' (کتاب میں لکھی نہیں)</p>');
  if (open && h.note) notes.push('<p class="note">' + esc(h.note) + '</p>');
  if (open && h.ai) notes.push('<p class="note ai">اعراب AI کے — اپنے نسخے سے ملا لیں</p>');
  let acts = "";
  if (!open) acts += '<button type="button" class="btn show" data-show="' + h.n + '">متن دکھائیں</button>';
  if (I.k === "todo") acts += '<button type="button" class="btn main" data-mark="' + h.n + '">یاد ہو گئی</button>';
  else if (I.k === "due") acts += '<button type="button" class="btn main due" data-rev="' + h.n + '">دہرائی کر لی</button>';
  else if (I.k === "ok") acts += '<span class="next">اگلی دہرائی: ' + fmt(I.due) + '</span>';
  else acts += '<span class="next">تینوں دہرائیاں مکمل</span>';
  if (I.k !== "todo") acts += '<button type="button" class="undo" data-undo="' + h.n + '">دوبارہ شروع</button>';
  return '<article id="h' + h.n + '" class="' + (I.k === "todo" ? "" : "done") + '">' +
    '<div class="head"><span class="n">' + idx + '</span><span class="sah">' + esc(h.s) + '</span><span class="mno">مشکوٰۃ ' + h.n + '</span>' +
    (stTxt ? '<span class="st ' + I.k + '">' + stTxt + '</span>' : "") + '</div>' +
    body + (notes.length ? '<div class="notes">' + notes.join("") + '</div>' : "") + '<div class="acts">' + acts + '</div></article>';
}
function render() {
  let done = 0, due = 0;
  D.h.forEach(h => { const k = info(h.n).k; if (k !== "todo") done++; if (k === "due") due++; });
  document.getElementById("pDone").textContent = done;
  document.getElementById("pFill").style.width = (done / D.h.length * 100) + "%";
  document.getElementById("pDue").textContent = due ? "آج " + due + " کی دہرائی" : "";
  document.getElementById("cAll").textContent = D.h.length;
  document.getElementById("cTodo").textContent = D.h.length - done;
  document.getElementById("cDue").textContent = due;
  const keep = h => filt === "all" || (filt === "todo" ? info(h.n).k === "todo" : info(h.n).k === "due");
  let out = "", idx = 0, any = 0;
  D.groups.forEach(g => {
    const items = [];
    D.h.forEach(h => { if (h.g !== g.k) return; idx++; if (keep(h)) items.push(cardHtml(h, idx)); });
    if (items.length) { any++; out += '<section class="grp"><h2 lang="ar">' + esc(g.t) + '<small>' + esc(g.d) + '</small></h2>' + items.join("") + '</section>'; }
  });
  document.getElementById("list").innerHTML = out;
  const em = document.getElementById("empty");
  em.hidden = !!any;
  em.textContent = filt === "due" ? "آج کوئی دہرائی باقی نہیں۔" : "سب احادیث یاد ہو گئیں، ما شاء اللہ۔";
  document.querySelectorAll(".seg button").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.mode === mode)));
  document.querySelectorAll(".chip").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.f === filt)));
}
document.addEventListener("click", e => {
  const b = e.target.closest("button"); if (!b) return;
  const d = b.dataset;
  if (d.mode) { mode = d.mode; shown.clear(); try { localStorage.setItem(KEY + "-mode", mode); } catch (x) {} render(); return; }
  if (d.f) { filt = d.f; render(); return; }
  if (d.show) { shown.add(+d.show); render(); return; }
  if (d.mark) { st[d.mark] = { m: iso(today()), r: 0 }; }
  else if (d.rev) { const s = st[d.rev]; s.r += 1; s.m = iso(today()); }
  else if (d.undo) { if (!confirm("اس حدیث کا حساب صاف کر دیں؟")) return; delete st[d.undo]; }
  else return;
  save(); render();
});
render();
</script>
"""

home = f'<a class="homelink" href="{HOME}">→ تمام پرچے</a>' if HOME else ""
page = PAGE.replace("__HOME__", home).replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
open(os.path.join(HERE, "mishkat1_hifz.html"), "w", encoding="utf-8").write(page)
print("built", len(page), "bytes")
