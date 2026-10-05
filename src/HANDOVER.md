# Wifaq 1448 card site: handover (start here in a new chat)

Updated 5 Oct 2026. This is the single source of truth for continuing the work. `claude/wifaq-1448-plan.md` (project doc) is background: exam facts, study method, timeline. Its "Open next steps" and its audio notes are out of date; follow this file.

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
| Agent brief for drafting cards | `src/cards/h4/BRIEF.md` + `src/cards/h4/TEMPLATE_card_file.py` |
| Recordings list (trimmed) | `src/data/recordings.csv` (Hidaya 4 + both Mishkat volumes: file, date, minutes, size, Drive ID). Full list of all 511 recordings: `recording_ids.csv` in Drive folder *Wifaq 1448* |
| Colab code | `src/colab/` (Recordings Pipeline, Drive IDs, Timestamp Repair v2 + `tsfix_*.py`, cell 7 Opus) |
| Transcripts | Drive folder `1Rum3xElGM6_aUm5ssuEfOfSssI0T9v3Y` (`Wifaq 1448/transcripts/ہدایہ جلد رابع`; other books have sibling folders). Originals before timestamp repair: `transcripts/_original` |
| Bushra vol 7 OCR (Hidaya 4, first half) | Drive folder `15KT9EQxSPcCWGKwCvJ73ElIVCL8rSl2U`, files `pAAAA-BBBB.md` = PDF pages AAAA–BBBB, printed page = PDF page − 1; each page has `[متن]`, `[بین السطور]`, `[حاشیہ]`. **Ignore the "PDF n" numbers inside multi-page files (some are wrong); number pages by position in the file.** Vol 8 (second half of Hidaya 4): not located yet, search Drive for "Al Hidayah Vol-8" |
| Drive folder *Wifaq 1448* | `1pmHpS9MU1wabfYU7AJtPmmwM0xvuJcsk` (transcripts, inventory, `recording_ids.csv`, `web_audio`, `web_audio_opus`) |
| Light AAC copies (old) | `web_audio` `14mMfY9cqP7eNUwHQYSHIy9F-1PUGsJo0`; Hidaya 4 subfolder `1weO8JSyTF9V39_TLJWWmWqmAuuNe-QBH`. Superseded by Opus |
| Opus copies (new) | `Wifaq 1448/web_audio_opus` `1xo6VUnMds6-b_kAENCdK2SUkEpmGBhX8`; Hidaya 4 subfolder `1nC5cNr3GW1tI35ImzciZPTkUFJYUayeZ`; `index.csv` (book, file, part, start_sec, lesson_seconds, size_mb, web_file) is written when the run ends. Made by Colab cell 7 (running since 6:48 pm, 5 Oct; about 35 s per lesson, parts 2.5–4.4 MB) |
| Recordings vault | `سابعہ`, owner imrandn@gmail.com, `1wuN7GpeuAjGSHAwzZzK87DPzC1nQggwf` (shared with the user; linked into My Drive as a shortcut) |
| Project docs | `claude/hidaya4-contents.md` (colleagues' contents page), `claude/cards/*` (old pilot markdown) |
| Old claude.ai artifacts | "ہدایہ رابع کارڈ" and "مشکوٰۃ حدیث کارڈ": superseded by the GitHub site, don't update them |

## 3. Starting work in a new chat

1. **Attach the repo** with push access (add_repo: `safiullahhusaini/wifaq-cards`), clone it, and work in it. Sessions can only reach repos the Claude GitHub App is installed on, and **cannot create repos**. If a new repo is ever needed, the user creates it and adds it to the app.
2. `pip install --break-system-packages rapidfuzz numpy scipy` (ffmpeg and Playwright/Chromium are usually there already).
3. Build: `cd src/cards && python3 build_site.py`. It writes the pages into the repo root. It works **without the OCR**: `h4_pagemap_cache.json` reproduces the page numbers of every existing card. Tested: a build with the OCR hidden gives byte-identical pages.
4. New cards on vol-7 pages need the OCR: download it into `<repo>/.cache/v7ocr/` (gitignored), or set env `V7OCR`. A sub-agent can fetch about 50 files in 7 minutes.
5. Check the pages: run `python3 -m http.server` in the repo, then take Playwright screenshots at 390×844. Google Fonts don't load in the sandbox, which is expected. Range text is RTL with LRI/PDI isolates, so read numbers from zoomed screenshots (device_scale_factor 3); low-res screenshots mislead.
6. Commit and push to `main` with the session's attribution lines. Pages deploys in about a minute. `curl` to github.io is blocked by the sandbox proxy; check the live site with WebFetch instead.

## 4. What is live (5 Oct 2026)

- **Home** → paper list. Hidaya 4 links to `hidaya4/` and Mishkat 1 to its sample. The other four papers say "coming".
- **`hidaya4/`** = the colleagues' contents page: every kitab of the volume in book order, with page range, card count, and "ابھی کارڈ نہیں" where there are none. A page-number box jumps to the right kitab.
- **Kitab pages** `shufa.html`, `qisma.html`, `muzaraa.html`, `musaqat.html`:
  - They open on a **فہرست** styled like the book's contents: bab and fasl rows with dotted leaders, a page range, and page chips under each.
  - Tapping a fasl shows its cards. A sticky bar has page chips and a page box; previous/next fasl links sit at the bottom.
  - Hash routes: `#u3` (unit), `#u3-1613` (unit + page), `#p1613` (page jump, resolves to a unit).
- **Recordings** sit behind the header button in a bottom sheet:
  - Per lesson: listen here, light Opus download, original download from Drive, pick own file, remember on this phone (IndexedDB).
  - The player bar only shows while playing. The Drive "open at time" links were removed: they never worked on phones.
- **Cards: 110 from 14 lessons.**
  - Shuf'a 47 (05-11 → 06-15), Qisma 36 (06-21 → 07-07), Muzara'a 17 complete (07-07, 07-12, 07-13), Musaqat 10 complete (07-19).
  - Each card shows its colleague page(s), its Bushra vol-7 page, the lesson, and a play button at the card's timestamp.
- **In-page audio:** only 05-18, 06-14 (2 parts), 06-28, 07-05 and 07-13 (Opus, in `hidaya4/audio/`, about 18 MB). The other 9 lessons show "download the original".
- **QA (independent agent, 3 Oct):** all 2,794 timestamps match real transcript lines; 52 random lines all supported; no imam-attribution errors. Scripts in `src/qa/`.

## 5. How a lesson becomes cards (the pipeline)

1. **Recording → transcript**: the user's own Colab notebook *v2.5* (built in the "Transcription optimization" chat, not in this repo).
   - Gemini via AI Studio + Vertex express lanes. Use only `MODELS = VERTEX_MODELS = 3.8, 3.7, 3.6 Flash`: 3.5 and 2.5 produced bad timestamps.
   - Free tier: 20 requests per day per model. Quota resets at 12:00 pm Pakistan time, 1:00 pm after 1 Nov.
   - Lines look like `[h:mm:ss] text`; `ع:` marks the teacher reading Arabic.
2. **Timestamp repair**: `Wifaq_1448_Timestamp_Repair_v2.ipynb` (T4 GPU).
   - faster-whisper large-v3 word times, with audio decoded by ffmpeg to numpy (PyAV breaks on Colab). rapidfuzz alignment, then weighted LIS, then interpolation.
   - Rewrites timestamps, adds `- وقت:` / `- خلا:` header lines, keeps originals, logs `timestamp_fix.csv`.
3. **Cards**: one sub-agent per lesson with `src/cards/h4/BRIEF.md`.
   - Brief it with the date, the previous lesson's last card, and where the next lesson starts.
   - It writes `src/cards/h4/h4_<date>.py`: CARDS with `v7`/`v7_frac`/`v7_end`/`v7_end_frac`, `start` (first words as printed), tamheed/masala/dalil/ikhtilaf/faida/lughat lines.
   - Tags: `U(ts)` teacher, `K7(page)` vol-7 matn, `S("الكفاية ٨/٣١٩")` footnote or sharh, `A` = AI wording.
   - It also writes `GAPS` (book text the recording doesn't explain) and `NOTES` (teacher-vs-book slips, OCR fixes; QA only, not shown on the site).
   - Rules: copy timestamps only from real lines; keep the teacher's own examples; don't invent.
4. **Integration** (`h4_data.py`):
   - Locates each card's `start` in the OCR.
   - Maps to colleague pages (`h4_pagemap.py`).
   - Assigns kitab/bab/fasl from `h4_toc.py` by heading offsets.
   - Converts `K7` tags to colleague-page `K` tags (keeping `v7` for a tooltip).
   - Turns GAPS into per-fasl "not explained" or "not recorded" lists.
   - Special cases: 05-17 card 1 is the teacher's recap of 05-11 and carries the badge «17 مئی کی دہرائی»; 07-06 has no cards.
5. **QA**: a separate agent re-checks timestamps mechanically and samples lines against the transcript and matn (`src/qa/check_a.py`, `sample_b.py`). Do this for every new batch.
6. **Build and push** (section 3).

## 6. Page numbers (important limitation)

- **Only 1609–1611 are verified** (from photos). The rest are estimated.
  - Inputs: letters of matn per vol-7 page (OCR; pages where the OCR dropped lines or poured footnotes into the matn get the median), the colleagues' contents-page headings, and two exact anchors (start of 1610 «أخذها بمثله», start of 1611 «إنما يثبت بالبيع»).
  - Each heading's position inside its page is fitted (least squares) so that letters per page is even. Expect ±1 page at card edges.
  - The page footer says so; every card also shows its exact Bushra page.
- **To pin exactly:** the colleagues' edition as a PDF (best) or photos of its pages. Then add EXACT anchors in `h4_pagemap.py` (or replace the model with real per-page text matching).
- **Extending to new kitabs:**
  - Add each heading as (vol-7 page, heading text, colleague page[, fraction if the OCR lost the heading]) to `HEADINGS` in `h4_pagemap.py`; already there up to الذبائح (v7 126 ↔ 1657).
  - `LAST_PAGE = 135` caps vol 7.
  - **Vol 8 needs generalising** the map to (volume, page), plus that volume's OCR.
- **Teacher's edition** (pages he announces in class) differs from both and can't be used directly: Shuf'a 1637, Qisma 1669, فصل المهايأة 1684, Muzara'a shurut 1692, Musaqat 1700, فصل في الجنين 1992. The offset to the colleagues' pages drifts from about +40 to about +130.

## 7. Audio

- **Format: Ogg Opus 16 kbps mono** (user agreed; most classmates use Android). About 5 MB per 45 min, against about 48 MB for the original.
  - Plays on Android and on iOS 18.4+. Older iPhones are told to download the original and use «اپنی فائل چنیں».
  - The player streams, and if the server can't seek it fetches the whole file once (blob fallback).
- **The Drive connector only downloads files up to about 5.7 MB.** Base64 results are saved to disk, so let a sub-agent do downloads.
  - Cell 7 (`src/colab/cell7_opus_audio.py`) therefore cuts lessons into parts of at most 5 MB, named `<stem>.ogg` or `<stem> - N.ogg`.
- **To add audio for a lesson:**
  1. Download its part(s) from `web_audio_opus`.
  2. Save as `hidaya4/audio/<date>.ogg`, or `<date>-1.ogg`, `<date>-2.ogg`.
  3. Add each part's `start_sec` from `index.csv` to `hidaya4/audio/parts.json`.
  4. Rebuild.
- **Waiting for cell 7** (running since 6:48 pm, 5 Oct, in date order; the first Jinayat files were in Drive by 6:53 pm, so all 85 should be done in about an hour). Needed for the live cards: 05-11, 05-17, 06-01, 06-15, 06-21, 06-22, 07-07, 07-12, 07-19. If `index.csv` is missing, the run stopped early: check the cell output and run it again (it skips finished lessons).
- **Storage:** a GitHub Pages site should stay under 1 GB. All 85 Hidaya 4 lessons ≈ 400 MB. Other books' audio will need a second repo that the user creates and adds to the Claude app. Don't commit the AAC copies.

## 8. Missing items and backlog (in priority order)

1. **Pull the 9 missing Opus files** once cell 7 has written them (section 7), then rebuild and push.
2. **Next Hidaya 4 kitabs** (same pipeline). Check the transcript first: the repair run skipped some because they had too few timestamped lines (other formats or broken transcripts).

   | Kitab | Colleague pages | Lessons | Problems to fix first |
   |---|---|---|---|
   | الذبائح | 1657 | 07-26, 07-27, plus "2025-07- … الذبائح" (undated, 33 min; find its place) | 07-26 transcript has 1 timestamp: re-transcribe |
   | الأضحية | 1672 | 08-09 (+ "الأضحية 2", 7 min), 08-10 | "2025-08-09 المشكاة المصابيح اكتاب الأضحية.m4a" sits in the Hidaya 4 list: check whether it is Hidaya or Mishkat |
   | الكراهية | 1684 | 08-16, 08-24, 08-30, 08-31, 09-07 | 08-16 skipped by repair |
   | إحياء الموات | 1724 | 09-13, 09-21, 09-27 | |
   | الأشربة | 1742 | 09-27, 09-28, 10-04 | 09-28 skipped by repair |
   | الصيد | 1756 | 10-05, 10-11, 10-12, 10-18 | 10-05 skipped |
   | الرهن | 1773 | 12-29, 01-03 … 01-11 (2026) | 2026-01-08 skipped |
   | الجنايات | 1823 | 2025-02-22 … 04-20 (earlier series) | 04-19 skipped; two 04-20 files (m4a 16 min and mp4 34 min) |
   | الديات + المعاقل | 1856 + 1930 | 2025-04-20 … 05-04 and 10-18 … 12-02 | 04-20 الديات (0 lines), 10-18, 10-28 skipped; 04-27 (64%) and 05-04 (62%) low match. المعاقل is inside files named الديات (late Nov – early Dec) |
   | الوصايا | 1939 | 12-06 … 12-27 | 12-14 skipped |
   | الخنثى | 1997 | 12-28 | |

   Most of these are in Bushra **vol 8**: find its OCR folder and generalise the page map. Vol 7 covers Shuf'a to about الذبائح and beyond; check where it ends.
3. **Re-transcribe** with 3.8/3.7/3.6 Flash, then repair:
   - 06-15 and 07-07: only 45–49 timestamps, so green times can be 1–3 min early. 06-15 is also short of text after 0:31.
   - 06-22: text missing 0:35:31–0:37:39.
   - The skipped files in the table.
   - Afterwards, rebuild the affected cards' timestamps; a small agent re-checks them.
4. **Exact colleague pages**: ask the user for the colleagues' Hidaya 4 PDF or page photos (section 6).
5. **Unrecorded part**: فصل في الاختلاف (1607–1608) and the start of فصل فيما يؤخذ. The 18 May recording starts mid-way. A classmate may have the full class.
6. **2025-07-06** is a Hidaya 3 lesson filed under Hidaya 4. Sub-topics start at 0:00:24, 0:04:33, 0:13:58 and 0:16:47. Use it when Hidaya 3 starts; maybe rename it in Drive.
7. **Mishkat (papers 3 and 4)**:
   - The user's convention: follow the book's divisions كتاب → باب → الفصل الأول/الثاني/الثالث, and show each hadith's absolute (running) number on its card.
   - Card focus: what the teacher adds beyond the hadith text, plus difficult words; background only when he gives one.
   - The sample (`m1_cards.py`, 2 hadiths, 2025-03-16) has no hadith numbers yet; verify numbers against the user's or colleagues' Mishkat edition before adding them.
   - Mishkat audio needs cell 7 with `WEB_BOOKS` extended. Hifz list: 38 hadith (matn + sahabi).
8. **Hidaya 3**: deliberately last. Earlier pilot: Kitab al-Sarf pp. 254–258 (`src/cards/legacy/sarf_cards.py`, project doc `claude/cards/hidaya3-kitab-al-sarf-253-258.md`).
9. **Other papers**: Tibyan, Taysir → Nukhba, Aina-e-Qadiyaniyat, Baydawi. No cards yet. Aina is an Urdu book and needs a transcription prompt tweak.
10. **Past-paper heat map** from «الجواب للموقوف علیہ» (10 years of solved papers, 454 pages; the user has it as an app/PDF). Waiting for the PDF. The plan's tiers: A = asked 3+ times, B = 1–2, C = never.
11. **Ideas, not requested yet** (ask before building):
    - Search across cards.
    - An offline/PWA mode.
    - A "report a mistake" link for classmates.
    - Exam-hint badges where the teacher says «امتحان میں آتا ہے» (none found in the 14 lessons so far).

## 9. Decisions and preferences to keep

- **Times in 12-hour format** (e.g. 6:22 pm).
- **Site and access:** public site, no Claude sign-in for classmates. Hosting stays on GitHub Pages.
- **Navigation:** home → paper → kitab list → kitab page by fasl, with page chips under each fasl. Keep the page-number jump.
- **Recordings:** keep them hidden behind a button, so first-time users aren't confused. Keep a download option for weak-internet users, but light (Opus).
- **Drive links:** don't add Drive "open at timestamp" links again; they don't jump on phones.
- **Order of work:** quality over speed. Hidaya 3 goes last in transcription and cards.
- **Visual identity:** matn red rubric (#A3211A), teacher green, book blue, AI amber; Amiri for Arabic, Noto Nastaliq for Urdu, Noto Naskh for UI; contents styled like a printed فہرست. Light and dark themes.

## 10. Known technical limits

- **Sandbox:** sessions run in ephemeral cloud containers; anything not pushed to the repo is lost.
- **Network:** shell network goes through an allowlist. github.io and drive.google.com downloads are blocked from curl.
- **Drive connector:** downloads up to about 5.7 MB; `read_file_content` saves big text files to disk.
- **GitHub API (`gh api`):** repository-scoped only; can't create repos.
- **claude.ai artifacts:** CSP blocks media from Drive; "anyone with link" still needs a Claude login (rejected by the user).
- **iOS Safari:** Ogg Opus only from 18.4.
- **Card agents:** each uses about 200–250k tokens. Running about 10 at once hit the session limit twice; 3–4 at a time is safer.
