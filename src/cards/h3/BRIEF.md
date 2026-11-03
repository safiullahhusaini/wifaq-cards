# Brief: drafting تمہیدی کارڈ for one Hidaya vol 3 lesson

You are drafting study cards (تمہیدی کارڈ) from ONE recorded class of al-Hidaya vol 3, for madrasa students preparing for the Wifaq ul Madaris exam in Pakistan. Students read these cards instead of re-listening to the 45-minute recording, so the cards must carry what the teacher actually said, tied to the book.

## The students' method (why the cards look like this)
The teacher splits the text into sub-topics. For each, he first explains in Urdu with an example using made-up people and numbers ("یاسر نے وقاص سے گاڑی خریدی…", "دس گرام سونا گیارہ گرام کے بدلے…"), then reads the Arabic and gives the meanings of hard words. Students keep: the teacher's تمہید, the ruling, the proofs/disagreement, and word meanings. Not a translation.

## Your lesson (the manager fills this in)
- Lesson key `<KEY>`: this year's class = `<DATE>-1448` (e.g. `2026-07-11-1448`), last year's class = `<DATE>` (e.g. `2025-02-22`).
- Source: `this-year` (اس سال کی کلاس, 1448) or `last-year` (پچھلے سال کی کلاس; used only for a passage this year's class has passed without a recording).
- Recording file name (e.g. `Hidaya Saalis 11 July 2026.m4a`) and its length in minutes.
- Start and end passages in the vol-5 matn, the previous lesson's last card, the teacher's slips noticed.

## Sources (local files; the data repo `wifaq-data` is checked out at /home/claude/wifaq-data)
1. **Transcript**: `/home/claude/wifaq-data/transcripts/ہدایہ جلد ثالث/<file>.md`. This year's: `<DATE> ہدایہ جلد ثالث 1448.md` (header line `- سال: 1448 (اس سال کی کلاس)`); last year's: `<DATE> الهدايه الثالث كتاب ....md`. Lines look like `[0:12:34] text`; `ع:` marks the teacher reading the book's Arabic. A repaired transcript has a `- وقت:` header line (timestamps corrected against the audio): use them as they are. Header lines `- خلا:` mark stretches where the transcript is missing text. Read ALL of it before writing.
2. **Book text**: 8-volume Maktaba al-Bushra edition, **vol 5** OCR in `/home/claude/wifaq/v5ocr/` (symlink → `<cards repo>/.cache/v5ocr` → `/home/claude/wifaq-data/ocr/Al Hidayah Vol-5/`; make the links if missing). Files `pAAAA-BBBB.md` hold PDF pages AAAA–BBBB; `pages.csv` there says which file holds each PDF page (a few pages were re-done in single-page files: `p0310-0310.md`, `p0356-0356.md`, `p0371-0371.md`, `p0420-0420.md`, `p0438-0438.md`). **Printed page = PDF page − 1.** Ignore the "PDF n" labels inside a file; number its pages by position in the file. Each page section has `[متن]` (main text), `[بین السطور]` (interlinear glosses) and `[حاشیہ]` (footnotes quoting شروح with volume/page, e.g. `[العناية ٧/١٣٣]`, `(البناية)`). Read every page your lesson covers.
   Vol-5 printed-page landmarks: كتاب الصرف 253 · كتاب الكفالة 274 · فصل في الضمان 311 · باب كفالة الرجلين 318 · باب كفالة العبد وعنه 324 · كتاب الحوالة 328 · كتاب أدب القاضي 336 · فصل في الحبس 350 · باب كتاب القاضي إلى القاضي 355 · فصل آخر 362 · باب التحكيم 370 · مسائل شتى 374 · فصل في القضاء بالمواريث 382 · كتاب الشهادة 399 · فصل 410 · باب من تقبل شهادته 419 · باب الاختلاف في الشهادة 437 · فصل في الشهادة على الإرث 446 · باب الشهادة على الشهادة 449 · كتاب الرجوع عن الشهادة 460 · كتاب الوكالة 472 · باب الوكالة بالبيع والشراء 484 · باب الوكالة بالخصومة والقبض 521 · باب عزل الوكيل 535. (Full list: `/home/claude/wifaq/cards/h3_toc.py`.)
3. **Style model**: read `/home/claude/wifaq/cards/h4_cards.py` fully (5 finished Hidaya 4 cards). Copy its tone, length and tagging. In YOUR file use `K5(vol-5 printed page)` where that file uses `K(page)`.
4. **Output template**: `/home/claude/wifaq/cards/h3/TEMPLATE_card_file.py`.

## How to make the cards
- One card per sub-topic as the teacher divides it (usually one masala cluster, ~3–10 minutes of class, ~1–3 vol-5 pages). Don't make tiny cards; don't merge unrelated masa'il.
- For each card find where its passage starts and ends in the vol-5 matn (printed page + rough fraction down the page). `start` = the first 5–12 words of that passage exactly as printed. The site's page numbers are these Bushra vol-5 printed pages, so get them right.
- **تمہید** (1–4 lines): the teacher's own setup and example, tightly paraphrased in Urdu, each line tagged `U("h:mm:ss")` with the timestamp of the transcript line where he says it. Keep his characters, numbers and analogies. Don't add examples of your own. If he gives no setup, write one short line tagged `A` and say so in `norec` only if the whole passage is unexplained.
- **مسئلہ**: the ruling(s) as the teacher states them, checked against the matn: tag `U(...)` and `K5(page)` when both support it.
- **دلیل / اختلاف**: from the teacher and the matn (who holds what, and why); footnote points tagged `S("<sharh> <vol/page as printed>")`, e.g. `S("البناية ٨/٣٨٠")`, `S("العناية ٧/١٣٣")`. Cite as printed, or the sharh name alone when unsure; never "correct" a printed number on a guess.
- **فائدہ**: exam-useful points from the teacher or the footnotes. If the teacher says something like "یہ امتحان میں آتا ہے" or «اہم», quote it.
- **مشکل الفاظ** (4–8): Arabic words/phrases from the matn with Urdu meaning — the teacher's meaning (`U`) first, else the interlinear gloss (`S(GLOSS)`), else `A`.
- Every line carries at least one source tag. Never invent or estimate a timestamp — copy it from the line where the teacher says it. `A` only for your own wording that nothing supports; keep it rare.
- Teacher contradicts the matn/footnotes, or seems to misspeak → put it in `NOTES`; don't present it as fact.
- Book text inside your lesson's range that the recording doesn't explain (skipped, class cut, recording starts late, `- خلا:` stretch) → `GAPS` with vol-5 pages (`"v5 255–256"`).
- Ignore English text or model chatter in the transcript, and the teacher's off-topic or sectarian asides.
- Urdu: plain, short sentences (one or two per line). Arabic quotes in Arabic script.

## Output
Write `/home/claude/wifaq/cards/h3/h3_<KEY>.py` in exactly the template's form (UTF-8), with `LESSON = "<KEY>"`, `SOURCE` (`"this-year"` / `"last-year"`), `RECORDING` (file name) and `MINUTES`. Check it loads:
`python3 -c "import runpy; d=runpy.run_path('/home/claude/wifaq/cards/h3/h3_<KEY>.py'); print(len(d['CARDS']), 'cards')"`.
Don't create or change any other file. Never copy transcript or OCR text beyond the short quotes the cards need (the repo is public).

Final message (short, for Claude, not the student): one line per card (ts · vol-5 pages · title), then GAPS and NOTES.
