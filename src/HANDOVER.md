# Wifaq 1448 card site: handover (start here in a new chat)

Updated 8 Oct 2026, 3:30 pm (chat: teacher's exam/importance marks added, section 4; earlier: scheduled run carded الأضحية; automation added, section 0). This is the single source of truth for continuing the work. `claude/wifaq-1448-plan.md` (project doc) is background: exam facts, study method, timeline. Its "Open next steps" and its audio notes are out of date; follow this file. A copy lives in the repo at `src/HANDOVER.md`; the project doc `claude/HANDOVER.md` is the primary one.

## 0. Automation (since 8 Oct 2026)

The remaining cards are now made by **scheduled runs** ("Wifaq cards run", 1:52 am and 1:52 pm PKT, cloud, automatic approval). A run starts cold and follows `src/auto/AUTOMATION.md`; the to-do list is `src/auto/queue.json` (every remaining lesson with its state, plus engineering items); the user's answers and notes come from the private control panel https://claude.ai/artifact/GqWNYfh4ZBwfozCFqAwbSN (copied to `src/auto/INBOX.md`); each run adds a line to `src/auto/runs.md`. The user's daily Colab work is one notebook, `src/colab/daily/Wifaq_1448_Daily.ipynb` (opened from GitHub), driven by Drive `Wifaq 1448/automation/daily_config.json`, which the runs keep current. Plan for the user: the Claude doc "Wifaq Cards Automation Plan" (https://claude.ai/code/artifact/24f9f1eb-01ac-431e-bbbf-b8d897759121). **Hidaya 3 is skipped for now (user, 8 Oct).** A chat session that is not a scheduled run should not card lessons from the queue without claiming them there first.

## 1. What this is

Syed (Khanpur, Haripur) is preparing for the Wifaq ul Madaris Alamiya year-1 exam (Mauquf Alaih), Sat 9 – Thu 14 Jan 2027, six papers. The app is a public website of **تمہیدی کارڈ**: study cards built from last year's class recordings, shared with classmates who need no sign-in.

**Card principles (from the user)**
- Authenticity: every line is traceable to the teacher (recording timestamp) or to the book, footnote or sharh.
- The teacher's method, not a translation: his تمہید with made-up characters and numbers → the ruling → proofs and disagreement → hard words.
- Quality over speed.
- Page numbers follow the **colleagues' edition** of Hidaya (continuous pages; Hidaya 4 = pp. 1595–2040). That is neither the user's Bushra 8-volume edition nor the teacher's edition.

## 2. Where everything is

| What | Where |
|---|---|
| Live site | https://safiullahhusaini.github.io/wifaq-cards/ (GitHub Pages, branch `main`, repo root; `robots.txt` disallows indexing) |
| Repo | `safiullahhusaini/wifaq-cards` (public). Generated pages at the root; **all sources in `src/`** |
| Card sources | `src/cards/h4/h4_<date>.py` (one file per lesson), `src/cards/h4_cards.py` (5 pilot cards, 18 May) |
| Builders | `src/cards/build_site.py` → `h4_site.py` → `h4_data.py` (+ `h4_pagemap.py`, `h4_toc.py`), `m1_build.py` (Mishkat); page template `kitab_template.html` |
| Agent brief for drafting cards | `src/cards/h4/BRIEF.md` + `src/cards/h4/TEMPLATE_card_file.py`. The brief expects `/home/claude/wifaq/cards` → `<repo>/src/cards` and `/home/claude/wifaq/v7ocr` → `<repo>/.cache/v7ocr` (make these symlinks) |
| Recordings list (trimmed) | `src/data/recordings.csv` (Hidaya 4 + both Mishkat volumes: file, date, minutes, size, Drive ID). Full list of all 511 recordings: `recording_ids.csv` in Drive folder *Wifaq 1448* |
| Colab code | `src/colab/` (Recordings Pipeline, Drive IDs, Timestamp Repair v2 + `tsfix_*.py`, cell 7 Opus) |
| Transcripts | Drive folder `1Rum3xElGM6_aUm5ssuEfOfSssI0T9v3Y` (`Wifaq 1448/transcripts/ہدایہ جلد رابع`; other books have sibling folders). Originals before timestamp repair: `transcripts/_original` |
| Bushra vol 7 OCR (Hidaya 4) | Drive folder `15KT9EQxSPcCWGKwCvJ73ElIVCL8rSl2U`, files `pAAAA-BBBB.md` = PDF pages AAAA–BBBB, printed page = PDF page − 1; each page has `[متن]`, `[بین السطور]`, `[حاشیہ]`. **Ignore the "PDF n" numbers inside multi-page files (some are wrong, some are 1, 2, 3…); number pages by position in the file.** The folder runs to at least PDF 300, so vol 7 covers much more than الذبائح: الأضحية starts on printed 154. Where vol 7 ends is not checked yet. File list with printed pages: `src/cards/h4/v7_files.txt` |
| Drive folder *Wifaq 1448* | `1pmHpS9MU1wabfYU7AJtPmmwM0xvuJcsk` (transcripts, inventory, `recording_ids.csv`, `web_audio`, `web_audio_opus`) |
| Light AAC copies (old) | `web_audio` `14mMfY9cqP7eNUwHQYSHIy9F-1PUGsJo0`; Hidaya 4 subfolder `1weO8JSyTF9V39_TLJWWmWqmAuuNe-QBH`. Superseded by Opus |
| Opus copies | `Wifaq 1448/web_audio_opus` `1xo6VUnMds6-b_kAENCdK2SUkEpmGBhX8`; Hidaya 4 subfolder `1nC5cNr3GW1tI35ImzciZPTkUFJYUayeZ` (all 85 lessons); `index.csv` `10jAddiTocZjxU3YGywldbK1x8ej5sGRK` (book, file, part, start_sec, lesson_seconds, size_mb, web_file). Made by Colab cell 7, finished 8:08 pm, 5 Oct; parts 0.7–4.9 MB |
| Recordings vault | `سابعہ`, owner imrandn@gmail.com, `1wuN7GpeuAjGSHAwzZzK87DPzC1nQggwf` (shared with the user; linked into My Drive as a shortcut) |
| Project docs | `claude/hidaya4-contents.md` (colleagues' contents page), `claude/cards/*` (old pilot markdown) |
| Old claude.ai artifacts | "ہدایہ رابع کارڈ" and "مشکوٰۃ حدیث کارڈ": superseded by the GitHub site, don't update them |

## 3. Starting work in a new chat

1. **Attach the repo** with push access (add_repo: `safiullahhusaini/wifaq-cards`), clone it, and work in it. Sessions can only reach repos the Claude GitHub App is installed on, and **cannot create repos**. If a new repo is ever needed, the user creates it and adds it to the app.
2. `pip install --break-system-packages rapidfuzz numpy scipy` (ffmpeg and Playwright/Chromium are usually there already).
3. Build: `cd src/cards && python3 build_site.py`. It writes the pages into the repo root. It works **without the OCR**: `h4_pagemap_cache.json` reproduces the page numbers of every existing card. Tested again 5 Oct: a build with the OCR hidden gives byte-identical pages.
4. New cards need the OCR **only for their own pages**: since 5 Oct, pages missing from the OCR on disk fall back to the cache one by one. Download just the new kitab's files into `<repo>/.cache/v7ocr/` (gitignored), or set env `V7OCR`. A sub-agent fetches 30 files in about 11 minutes. Then extend `HEADINGS` (section 6).
5. Check the pages: run `python3 -m http.server` in the repo, then take Playwright screenshots at 390×844. Google Fonts don't load in the sandbox, which is expected. Range text is RTL with LRI/PDI isolates, so read numbers from zoomed screenshots (device_scale_factor 3); low-res screenshots mislead.
6. Commit and push to `main` with the session's attribution lines. Pages deploys in about a minute. `curl` to github.io is blocked by the sandbox proxy; WebFetch to github.io needs the user's approval in the chat (it timed out unanswered on 5 Oct), so ask the user to open the page if needed.

## 4. What is live (8 Oct 2026, 2:40 pm)

- **Home** → paper list. Hidaya 4 links to `hidaya4/` and Mishkat 1 to its sample. The other four papers say "coming".
- **`hidaya4/`** = the colleagues' contents page: every kitab of the volume in book order, with page range, card count, and "ابھی کارڈ نہیں" where there are none. A page-number box jumps to the right kitab.
- **Kitab pages** `shufa.html`, `qisma.html`, `muzaraa.html`, `musaqat.html`, `dhabaih.html`, `udhiya.html`:
  - They open on a **فہرست** styled like the book's contents: bab and fasl rows with dotted leaders, a page range, and page chips under each.
  - Tapping a fasl shows its cards. A sticky bar has page chips and a page box; previous/next fasl links sit at the bottom.
  - Hash routes: `#u3` (unit), `#u3-1613` (unit + page), `#p1613` (page jump, resolves to a unit).
  - **«سب» view (8 Oct, user's request):** when the «سب» page chip is selected, each card opens folded: head row, title, Arabic start and the grey note under it. «تمہید اور تفصیل» opens one card; «سب تفصیل کھولیں» opens all cards but **does not** open the دلیل/اختلاف/فائدہ `details` (those stay manual). A single-page view shows cards fully open and hides «سب تفصیل». Units with one page have no «سب» chip, so their cards are open.
- **Recordings** sit behind the header button in a bottom sheet:
  - Per lesson: «شروع سے سنیں» and one light Opus «ڈاؤن لوڈ» button that downloads all its parts. Nothing else.
  - At the top: «سب ڈاؤن لوڈ کریں» (8 Oct, user's request) downloads every part of every lesson on that kitab page, one after another (1.2 s apart), named `<date> ہدایہ جلد رابع - حصہ N.ogg`. Chrome asks once to allow several downloads; the sheet says so.
  - **Removed 7 Oct (commit 2e474ed), at the user's request:** the original-file download from Drive, «اپنی فائل چنیں» / «کئی فائلیں ایک ساتھ چنیں», and remember-on-this-phone (IndexedDB). Reason: colleagues don't have the original files. The page now deletes the old `<store>-audio` IndexedDB and the `-remember` key on load, freeing space on phones. Don't add these back.
  - A lesson with no Opus file shows «ابھی نہیں لگی»; tapping its times opens a small sheet saying the recording isn't on the page yet. This is currently the case for the Mishkat sample (2025-03-16).
  - The player bar only shows while playing. The Drive "open at time" links were removed: they never worked on phones.
- **Cards: 144 from 19 lessons.**
  - Shuf'a 47 (05-11 → 06-15), Qisma 36 (06-21 → 07-07), Muzara'a 17 complete (07-07, 07-12, 07-13), Musaqat 10 complete (07-19).
  - Dhabaih 22 complete (1657–1671): 07-20 (8, date estimated, shown «(اندازاً)»), 07-26 (6), 07-27 (8).
  - Udhiya 12 (1677–1684): 08-09 second recording (3, key `2025-08-09-udhiya-2`, label «9 اگست 2025، دوسری ریکارڈنگ»), 08-10 (9, to the end of the kitab). Its start (v7 154–165, the first 9 Aug recording) waits for re-transcription; a GAPS line on the page says so.
  - Each card shows its colleague page(s), its Bushra vol-7 page, the lesson, and a play button at the card's timestamp.
- **In-page audio: all 19 carded lessons** (Opus, 29 files in `hidaya4/audio/`, about 83 MB).
- **QA (independent agents):** 3 Oct: all 2,794 timestamps match real transcript lines; 52 random lines all supported; no imam-attribution errors. 5 Oct, 07-27 batch: 186 timestamps all real; all 177 lines checked, no wrong rulings or attributions; 8 minor wording/tag issues fixed. 7 Oct, 07-20 + 07-26: 592 timestamps all real; all 308 lines checked; no wrong rulings or attributions; 1 unsupported tag + 11 nits fixed. Scripts in `src/qa/`.

- **Exam marks (8 Oct):** `src/data/h4_exam.json`. All 84 Hidaya 4 transcripts were searched: the teacher never says a passage comes in the exam (only «امتحان کے لیے وقت کم ہے», 10 Jan). He does flag masāʾil as «اہم», «مشہور», «بہت ضروری», «اچھی طرح ذہن میں رکھیں»: 17 flags, each with lesson, ts, his exact words and the Arabic opening. `h4_data.attach_exam` puts a flag on the card of that lesson whose start ts is the last at or before it; the card shows a red «★ استاد: اہم/مشہور» badge that plays the remark, and the fasl row in the kitab contents shows «★ n». Flags in lessons without cards (12: الجنايات 5, الديات 3, الرهن 2, الكراهية 1, الأشربة 1) are listed under their kitab on `hidaya4/index.html` until carded (AUTOMATION step 5 checks them).

## 5. How a lesson becomes cards (the pipeline)

1. **Recording → transcript**: the user's own Colab notebook *v2.5* (built in the "Transcription optimization" chat, not in this repo).
   - Gemini via AI Studio + Vertex express lanes. Use only `MODELS = VERTEX_MODELS = 3.8, 3.7, 3.6 Flash`: 3.5 and 2.5 produced bad timestamps.
   - Free tier: 20 requests per day per model. Quota resets at 12:00 pm Pakistan time, 1:00 pm after 1 Nov.
   - Lines look like `[h:mm:ss] text`; `ع:` marks the teacher reading Arabic.
   - **Re-transcribing chosen lessons:** `src/colab/cell_retranscribe.py` (one Colab cell, CPU). Put transcript file names in `TARGETS`; it tries 3.8 → 3.7 → 3.6 Flash on AI Studio then Vertex express (secret `VERTEX_API_KEY`, editable), rejects parts with sparse or out-of-range timestamps, moves the old file to `transcripts/_replaced/`, and writes the new one without a `- وقت:` line so Repair v2 picks it up. Given to the user 5 Oct, 10:45 pm, for the two الذبائح lessons.
2. **Timestamp repair**: `src/colab/tsfix/Wifaq_1448_Timestamp_Repair_v3.ipynb` (T4 GPU; built by `build_tsfix_nb.py`). v3 (6 Oct) = v2 with `ONLY_BOOKS = ["ہدایہ جلد رابع"]` and the Opus copier as cell 6; rebuilt after the user's Drive copy got corrupted.
   - faster-whisper large-v3 word times, with audio decoded by ffmpeg to numpy (PyAV breaks on Colab). rapidfuzz alignment, then weighted LIS, then interpolation.
   - Rewrites timestamps, adds `- وقت:` / `- خلا:` header lines, keeps originals, logs `timestamp_fix.csv`.
   - A repaired transcript has a `- وقت:` header line; one without it was not repaired.
3. **Cards**: one sub-agent per lesson with `src/cards/h4/BRIEF.md`.
   - Brief it with the date, the previous lesson's last card, and where the next lesson starts. Listing the teacher's slips you noticed in the transcript helps.
   - It writes `src/cards/h4/h4_<date>.py`: CARDS with `v7`/`v7_frac`/`v7_end`/`v7_end_frac`, `start` (first words as printed), tamheed/masala/dalil/ikhtilaf/faida/lughat lines.
   - Tags: `U(ts)` teacher, `K7(page)` vol-7 matn, `S("الكفاية ٨/٣١٩")` footnote or sharh, `A` = AI wording.
   - It also writes `GAPS` (book text the recording doesn't explain) and `NOTES` (teacher-vs-book slips, OCR fixes; QA only, not shown on the site).
   - Rules: copy timestamps only from real lines; keep the teacher's own examples; don't invent.
   - Telling the agent the exact start/end passages (find them in the OCR with rapidfuzz first) prevents overlap between neighbouring lessons.
   - Check its S tags against the OCR afterwards (the OCR also misspells names, e.g. «إلاء السنن» for إعلاء السنن): the OCR often prints references page-first («البناية ٧١٢/١٠» = ١٠/٧١٢), which is fine, but an agent once "corrected" a printed volume number on a guess. Cite as printed, or the sharh name alone when unsure.
4. **Integration** (`h4_data.py`):
   - Locates each card's `start` in the OCR.
   - Maps to colleague pages (`h4_pagemap.py`).
   - Assigns kitab/bab/fasl from `h4_toc.py` by heading offsets.
   - Converts `K7` tags to colleague-page `K` tags (keeping `v7` for a tooltip).
   - Turns GAPS into per-fasl "not explained" or "not recorded" lists.
   - Special cases: 05-17 card 1 is the teacher's recap of 05-11 and carries the badge «17 مئی کی دہرائی»; 07-06 has no cards.
5. **QA**: a separate agent re-checks timestamps mechanically and checks lines against the transcript and matn (`src/qa/check_a.py`, `sample_b.py`; for one new lesson, copy check_a.py to the scratchpad and narrow its glob). For a single lesson, checking all lines is affordable (about 190k tokens). Do this for every new batch.
6. **Audio**: add the lesson's Opus part(s) (section 7). Since 7 Oct this is the only way a lesson plays on the site, so every carded lesson needs it.
7. **Build and push** (section 3).

## 6. Page numbers (important limitation)

- **Only 1609–1611 are verified** (from photos). The rest are estimated.
  - Inputs: letters of matn per vol-7 page (OCR; pages where the OCR dropped lines or poured footnotes into the matn get the median), the colleagues' contents-page headings, and two exact anchors (start of 1610 «أخذها بمثله», start of 1611 «إنما يثبت بالبيع»).
  - Each heading's position inside its page is fitted (least squares) so that letters per page is even. Expect ±1 page at card edges.
  - The fit is global, so adding headings or OCR pages can move existing card edges by one page. On 5 Oct, adding v7 125–174 moved four card edges in Qisma and a few K-tag ranges near المساقاة/الذبائح by one page; no card changed fasl. Compare card pages before and after when extending.
  - The page footer says so; every card also shows its exact Bushra page.
- **To pin exactly:** the colleagues' edition as a PDF (best) or photos of its pages. Then add EXACT anchors in `h4_pagemap.py` (or replace the model with real per-page text matching).
- **Extending to new kitabs:**
  - Add each heading as (vol-7 page, heading text, colleague page[, fraction if the OCR lost the heading]) to `HEADINGS` in `h4_pagemap.py`; already there up to الأضحية (v7 154 ↔ 1672). Add the kitab's running header to `RUNNING` too.
  - `LAST_PAGE = 184` (8 Oct: OCR to printed 184 measured; كتاب الكراهية heading at v7 179 = 1684 added; existing card pages unchanged).
  - Vol 7 reaches well past الأضحية (OCR folder to PDF ≥ 300). Find where it ends before generalising the map to (volume, page) for vol 8.
- **Teacher's edition** (pages he announces in class) differs from both and can't be used directly: Shuf'a 1637, Qisma 1669, فصل المهايأة 1684, Muzara'a shurut 1692, Musaqat 1700, الذبائح 1705, his page 1711 (mid الذبائح, four veins), فصل فيما يحل أكله 1720, فصل في الجنين 1992. The offset to the colleagues' pages drifts from about +40 to about +130.

## 7. Audio

- **Format: Ogg Opus 16 kbps mono** (user agreed; most classmates use Android). About 5 MB per 45 min, against about 48 MB for the original.
  - Plays on Android and on iOS 18.4+. Older iPhones are told to update to iOS 18.4 or use Chrome on Android; there is no original-file fallback any more (removed 7 Oct).
  - The player streams, and if the server can't seek it fetches the whole file once (blob fallback).
- **The Drive connector only downloads files up to about 5.7 MB.** Base64 results are saved to disk, so let a sub-agent do downloads.
  - Cell 7 (`src/colab/cell7_opus_audio.py`) therefore cuts lessons into parts of at most 5 MB, named `<stem>.ogg` or `<stem> - N.ogg`.
- **Status:** cell 7 finished for all 85 Hidaya 4 lessons (index.csv written 8:08 pm, 5 Oct). All carded Hidaya 4 lessons are on the site.
- **To add audio for a lesson (new kitabs):**
  1. Download its part(s) from the Hidaya 4 subfolder of `web_audio_opus` (a sub-agent: search with `parentId` + `title contains '<date>'`).
  2. Save as `hidaya4/audio/<date>.ogg`, or `<date>-1.ogg`, `<date>-2.ogg`.
  3. Add each later part's `start_sec` from `index.csv` to `hidaya4/audio/parts.json`.
  4. Rebuild.
  - Dates with two lessons (e.g. 2025-04-20, 2025-08-09, 2025-09-27, 2025-10-18, 2025-11-29, 2026-01-10): since 8 Oct the lesson key is the queue id without `h4-` (e.g. `2025-08-09-udhiya-2`). The card file sets `LESSON` to it, audio is `hidaya4/audio/<key>.ogg`, and `LESSON_FILES` / `LESSON_SUFFIX` in `h4_data.py` map it to its recording (by Drive id) and its label. Undated files: give them an estimated date in `recordings.csv` and add it to `ESTIMATED_DATES` in `h4_data.py` (done for 2025-07-20).
- **Storage:** a GitHub Pages site should stay under 1 GB. All 85 Hidaya 4 lessons ≈ 400 MB (77 MB live now). Other books' audio will need a second repo that the user creates and adds to the Claude app. Don't commit the AAC copies. Mishkat needs cell 7 with `WEB_BOOKS` extended; until then the Mishkat sample's times can't play.

## 8. Missing items and backlog (in priority order)

1. **Next Hidaya 4 kitabs** (same pipeline). Check the transcript first: the repair run skipped some because they had too few timestamped lines (other formats or broken transcripts).

   | Kitab | Colleague pages | Lessons | Problems to fix first |
   |---|---|---|---|
   | الذبائح | 1657 (v7 126–153) | **Done** (7 Oct): 07-20 (estimated date, set in `recordings.csv` + `ESTIMATED_DATES`), 07-26, 07-27 | — |
   | الأضحية | 1672 (v7 154–178) | **Mostly done** (8 Oct): «الأضحية 2» (7 min) and 08-10 carded. Left: the first 08-09 recording (v7 154–165) | Its file is named «المشكاة المصابيح اكتاب الأضحية» but it is the Hidaya lesson (the transcript is Roman Urdu and doesn't match the audio, 1%): re-transcribe |
   | الكراهية | 1684 (v7 179–) | 08-16, 08-24, 08-30, 08-31, 09-07 | 08-16 skipped by repair; 08-24 text missing. Heading already in the map |
   | إحياء الموات | 1724 | 09-13, 09-21, 09-27 | |
   | الأشربة | 1742 | 09-27, 09-28, 10-04 | 09-28 skipped by repair |
   | الصيد | 1756 | 10-05, 10-11, 10-12, 10-18 | 10-05 skipped |
   | الرهن | 1773 | 12-29, 01-03 … 01-11 (2026) | 2026-01-08 skipped |
   | الجنايات | 1823 | 2025-02-22 … 04-20 (earlier series) | 04-19 skipped; two 04-20 files (m4a 16 min and mp4 34 min) |
   | الديات + المعاقل | 1856 + 1930 | 2025-04-20 … 05-04 and 10-18 … 12-02 | 04-20 الديات (0 lines), 10-18, 10-28 skipped; 04-27 (64%) and 05-04 (62%) low match. المعاقل is inside files named الديات (late Nov – early Dec) |
   | الوصايا | 1939 | 12-06 … 12-27 | 12-14 skipped |
   | الخنثى | 1997 | 12-28 | |

   **Next: الكراهية** (OCR on disk only in the run that downloads it: fetch v7 179 onward from p0180; `LAST_PAGE = 184`, raise it as new pages are added and compare card pages before/after).
2. **Re-transcribe** with 3.8/3.7/3.6 Flash, then repair:
   - 06-15 and 07-07: only 45–49 timestamps, so green times can be 1–3 min early. 06-15 is also short of text after 0:31.
   - 06-22: text missing 0:35:31–0:37:39.
   - The skipped files in the table.
   - Afterwards, rebuild the affected cards' timestamps; a small agent re-checks them.
3. **Exact colleague pages**: ask the user for the colleagues' Hidaya 4 PDF or page photos (section 6).
4. **Unrecorded part**: فصل في الاختلاف (1607–1608) and the start of فصل فيما يؤخذ. The 18 May recording starts mid-way. A classmate may have the full class.
5. **2025-07-06** is a Hidaya 3 lesson filed under Hidaya 4. Sub-topics start at 0:00:24, 0:04:33, 0:13:58 and 0:16:47. Use it when Hidaya 3 starts; maybe rename it in Drive.
6. **Mishkat (papers 3 and 4)**:
   - The user's convention: follow the book's divisions كتاب → باب → الفصل الأول/الثاني/الثالث, and show each hadith's absolute (running) number on its card.
   - Card focus: what the teacher adds beyond the hadith text, plus difficult words; background only when he gives one.
   - The sample (`m1_cards.py`, 2 hadiths, 2025-03-16) has no hadith numbers yet; verify numbers against the user's or colleagues' Mishkat edition before adding them.
   - Mishkat audio needs cell 7 with `WEB_BOOKS` extended (the sample has no playable audio since 7 Oct). Hifz list: 38 hadith (matn + sahabi).
7. **Hidaya 3**: deliberately last. Earlier pilot: Kitab al-Sarf pp. 254–258 (`src/cards/legacy/sarf_cards.py`, project doc `claude/cards/hidaya3-kitab-al-sarf-253-258.md`).
8. **Other papers**: Tibyan, Taysir → Nukhba, Aina-e-Qadiyaniyat, Baydawi. No cards yet. Aina is an Urdu book and needs a transcription prompt tweak.
9. **Past-paper badges** from «الجواب للموقوف علیہ» (10 years of solved papers, 454 pages; the user has it as an app/PDF). Waiting for the PDF (queue `eng-past-papers`). 8 Oct search: Wifaq's site has no past papers; the only free copies online are old editions (Yasin Shakir 2021 on besturdubooks/archive.org; Maktaba tul Ishaat «7-sabia Baneen.pdf», 40 MB, on archive.org) whose OCR is garbled and which the sandbox cannot download; no 1443–1447 papers anywhere online. The plan's tiers: A = asked 3+ times, B = 1–2, C = never. The data slot is `src/data/h4_exam.json → papers` and the template already renders paper badges (`k` ≠ `t`).
10. **Ideas, not requested yet** (ask before building):
    - Search across cards.
    - An offline/PWA mode (would also replace the offline use the removed file picker gave).
    - A "report a mistake" link for classmates.

    - A short reason under «ابھی کارڈ نہیں» when a lesson exists but awaits re-transcription.

Done (8 Oct, 6:45 am): download-all in the recordings sheet (per lesson and whole kitab); cards folded in the «سب» view, «سب تفصیل» opens cards but not their دلیل sections (commit 559f111).

Done (7 Oct, 4:45 pm): recordings sheet trimmed to listen + light download; original download and own-file picker removed (commit 2e474ed).

Done (7 Oct): re-transcribed + repaired 07-20/07-26 (Repair v3, 88–89% matched) and carded them; الذبائح complete (commit 6870caa).

Done (5 Oct): the 9 missing Opus files were pulled and pushed; every carded lesson plays in-page. 10:20 pm: الذبائح page with فصل فيما يحل أكله (8 cards, 07-27, commit 0f134af); page map extended to الأضحية with per-page cache fallback.

## 9. Decisions and preferences to keep

- **Times in 12-hour format** (e.g. 6:22 pm).
- **Site and access:** public site, no Claude sign-in for classmates. Hosting stays on GitHub Pages.
- **Navigation:** home → paper → kitab list → kitab page by fasl, with page chips under each fasl. Keep the page-number jump.
- **Recordings:** keep them hidden behind a button, so first-time users aren't confused. Offer only listen-here and the light (Opus) download, with one-tap download of all parts and of the whole kitab. No original-file download, no "pick your own file" (user, 7 Oct: colleagues don't have the originals).
- **Card folding:** in the «سب» view cards start folded (title, Arabic start, note); دلیل/اختلاف/فائدہ always open by hand, never by «سب تفصیل» (user, 8 Oct).
- **Drive links:** don't add Drive "open at timestamp" links again; they don't jump on phones.
- **Order of work:** quality over speed. Hidaya 3 goes last in transcription and cards, and is skipped for now (user, 8 Oct). Don't card lessons whose transcripts have bad timestamps; wait for re-transcription.
- **Visual identity:** matn red rubric (#A3211A), teacher green, book blue, AI amber; Amiri for Arabic, Noto Nastaliq for Urdu, Noto Naskh for UI; contents styled like a printed فہرست. Light and dark themes.

## 10. Known technical limits

- **Sandbox:** sessions run in ephemeral cloud containers; anything not pushed to the repo is lost.
- **Network:** shell network goes through an allowlist. github.io and drive.google.com downloads are blocked from curl.
- **Drive connector:** downloads up to about 5.7 MB; `read_file_content` saves big text files to disk.
- **GitHub API (`gh api`):** repository-scoped only; can't create repos.
- **claude.ai artifacts:** CSP blocks media from Drive; "anyone with link" still needs a Claude login (rejected by the user).
- **iOS Safari:** Ogg Opus only from 18.4; it may ask about each download separately.
- **Card agents:** each uses about 170–250k tokens. Running about 10 at once hit the session limit twice; 3–4 at a time is safer.
