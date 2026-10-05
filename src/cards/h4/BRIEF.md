# Brief: drafting تمہیدی کارڈ for one Hidaya vol 4 lesson

You are drafting study cards (تمہیدی کارڈ) from ONE recorded class of al-Hidaya vol 4, for madrasa students preparing for the Wifaq ul Madaris exam in Pakistan. Students read these cards instead of re-listening to the 45-minute recording, so the cards must carry what the teacher actually said, tied to the book.

## The students' method (why the cards look like this)
The teacher splits the text into sub-topics. For each, he first explains in Urdu with an example using made-up people and numbers ("یاسر نے وقاص سے گاڑی خریدی…", "زمین کی قیمت بیس لاکھ…"), then reads the Arabic and gives the meanings of hard words. Students keep: the teacher's تمہید, the ruling, the proofs/disagreement, and word meanings. Not a translation.

## Sources (all in Google Drive; use the mcp__Google_Drive__* tools — load them with ToolSearch query "select:mcp__Google_Drive__search_files,mcp__Google_Drive__read_file_content" if they are not loaded)
1. **Transcript** of your lesson: folder id `1Rum3xElGM6_aUm5ssuEfOfSssI0T9v3Y`. Search `parentId = '1Rum3xElGM6_aUm5ssuEfOfSssI0T9v3Y' and title contains '<DATE>'` and take the file for your lesson (title begins with the date; ignore titles with "(mp4)" unless told). Lines look like `[0:12:34] text`; `ع:` marks the teacher reading the book's Arabic. Timestamps have been corrected against the audio; use them as they are. Header lines `- خلا:` mark stretches where the transcript is missing text.
   The file is large: `read_file_content` will save it to disk and tell you the path; load it in python (`json.load(...)["fileContent"]`) and unescape markdown (`\[`→`[`, `\]`→`]`, `\-`→`-`, `\#`→`#`, `\*`→`*`). Read ALL of it before writing.
2. **Book text**: 8-volume Maktaba al-Bushra edition, vol 7 OCR, folder id `15KT9EQxSPcCWGKwCvJ73ElIVCL8rSl2U`. File names are by PDF page: see `/home/claude/wifaq/cards/h4/v7_files.txt` (printed page = PDF page − 1). Search `parentId = '15KT9EQxSPcCWGKwCvJ73ElIVCL8rSl2U' and title = 'p0029-0030.md'`. Each page section has `[متن]` (main text), `[بین السطور]` (interlinear glosses) and `[حاشیہ]` (footnotes quoting شروح with volume/page, e.g. `[العناية ٨/٣١٨]`, `(البناية)`). Read every page your lesson covers. Pages 0–106 are already on disk, unescaped, in `/home/claude/wifaq/v7ocr/` (same file names) — read those locally; fetch later pages from Drive (names continue `p0108-0108.md`… — list the folder to find them).
   Vol-7 page landmarks: كتاب الشفعة 3 · باب طلب الشفعة 14 · فصل في الاختلاف 24 · فصل فيما يؤخذ به المشفوع 28 · فصل (وإذا بنى المشتري) 32 · باب ما تجب فيه الشفعة 38 · باب ما تبطل به الشفعة 48 · فصل (حیلے) 53 · مسائل متفرقة 56 · كتاب القسمة 60 · فصل فيما يقسم وما لا يقسم 70 · فصل في كيفية القسمة ≈75 · باب دعوى الغلط في القسمة 86 · فصل [في الاستحقاق] 88 · فصل في المهايأة ≈92 · كتاب المزارعة 99 · كتاب المساقاة ≈117 · كتاب الذبائح ≈128.
3. **Style model**: read `/home/claude/wifaq/cards/h4_cards.py` fully (5 finished cards). Copy its tone, length and tagging. In YOUR file use `K7(vol-7 page)` where that file uses `K(page)`.
4. **Output template**: `/home/claude/wifaq/cards/h4/TEMPLATE_card_file.py`.

## How to make the cards
- One card per sub-topic as the teacher divides it (usually one masala cluster, ~3–10 minutes of class, ~1–3 vol-7 pages). Don't make tiny cards; don't merge unrelated masa'il.
- For each card find where its passage starts and ends in the vol-7 matn (page + rough fraction down the page). `start` = the first 5–12 words of that passage exactly as printed.
- **تمہید** (1–4 lines): the teacher's own setup and example, tightly paraphrased in Urdu, each line tagged `U("h:mm:ss")` with the timestamp of the transcript line where he says it. Keep his characters, numbers and analogies. Don't add examples of your own. If he gives no setup, write one short line tagged `A` and say so in `norec` only if the whole passage is unexplained.
- **مسئلہ**: the ruling(s) as the teacher states them, checked against the matn: tag `U(...)` and `K7(page)` when both support it.
- **دلیل / اختلاف**: from the teacher and the matn (who holds what, and why); footnote points tagged `S("<sharh> <vol/page as printed>")`, e.g. `S("الكفاية ٨/٣١٩")`, `S("البناية ١٠/٣٩٥")`, `S("العناية ٨/٣١٨")`.
- **فائدہ**: exam-useful points from the teacher or the footnotes. If the teacher says something like "یہ امتحان میں آتا ہے", quote it.
- **مشکل الفاظ** (4–8): Arabic words/phrases from the matn with Urdu meaning — the teacher's meaning (`U`) first, else the interlinear gloss (`S(GLOSS)`), else `A`.
- Every line carries at least one source tag. Never invent or estimate a timestamp — copy it from the line where the teacher says it. `A` only for your own wording that nothing supports; keep it rare.
- Teacher contradicts the matn/footnotes, or seems to misspeak → put it in `NOTES`; don't present it as fact.
- Book text inside your lesson's range that the recording doesn't explain (skipped, class cut, recording starts late, `- خلا:` stretch) → `GAPS` with vol-7 pages.
- Ignore English text or model chatter in the transcript, and the teacher's off-topic or sectarian asides.
- Urdu: plain, short sentences (one or two per line). Arabic quotes in Arabic script. Ruling words as in the samples (شفیع، مشتری، بائع…).

## Output
Write `/home/claude/wifaq/cards/h4/<FILE>.py` in exactly the template's form (UTF-8). Check it loads:
`python3 -c "import runpy; d=runpy.run_path('/home/claude/wifaq/cards/h4/<FILE>.py'); print(len(d['CARDS']), 'cards')"`.
Don't create or change any other file.

Final message (short, for Claude, not the student): one line per card (ts · vol-7 pages · title), then GAPS and NOTES.
