# Inbox: the user's decisions and notes

Copied here from the control panel by each run (newest first). The panel is where the user answers; this file is the durable record.

## Decisions

- 13 Oct 2026, 6:42 am (chat): **go faster within the Pro limits without lowering quality.** Applied in that chat: `max_lessons_per_run` 2 (queue + panel), no new lesson after 4:30 am on nightly runs; scheduled task switched to Sonnet as manager, with drafting, QA and fixes always on Opus; full QA on the nights of 14 and 15 Oct; four token-saving eng items queued; Daily notebook cell 9 (sync to the private repo wifaq-data). The user raises the limit to 3 on the panel if a night uses under ~10% of his weekly allowance. (This replaces "runs stay small, 1 per run" from 9 Oct.)
- 10 Oct 2026 (panel, answered 8 Oct, 3:37–3:41 pm; applied by the 10 Oct 9:05 am run):
  - **Book order after Hidaya 4:** Baydawi → Mishkat 1 → Mishkat 2 → Taysir → Nukhba → Tibyan → Aina. Already `settings.book_order`.
  - **Claude plan:** Pro. Runs stay small (the user also set `max_lessons_per_run` = 1 on the panel, 9 Oct).
  - **Lighter draft model:** yes, test Sonnet for drafting on one lesson, Opus checks it fully; keep it only if as accurate as the Opus drafts. Test lesson: h4-2025-08-09-udhiya (10 Oct run).
  - **GitHub machines for the daily Colab work:** yes, send the steps. Steps are in queue item `eng-github-pipeline` and in the panel reply; it stays blocked until the user adds the three secrets.
  - **Checking level:** focused check after a book's first 3 lessons pass clean. Hidaya 4 has had 3 clean full checks (3, 5, 7 Oct), so Hidaya 4 uses `focused`, except the Sonnet test lesson (full). Each new book starts on `full`.
  - **Run hours:** nights only, 12:52 am and 4:52 am. Runs may not edit their own schedule (AUTOMATION §10); the user was told to change it himself (or say so in a chat). As of 10 Oct 9 am the task still says 1:52 am / 1:52 pm.
- 8 Oct 2026 (chat): skip Hidaya 3 for now. Make all other cards automatically over the coming days with minimal manual work; ask only about important design decisions.

## Notes

- 15 Oct 2026 run: the "wifaq-data ready" note below is resolved: the run had the repo in its scope, cloned it and read transcripts, OCR and audio from it (marked done on the panel).
- 13 Oct 2026, 9:21 pm (panel note): "wifaq-data ready". → 14 Oct run: tried to read `safiullahhusaini/wifaq-data`; this scheduled session has GitHub access only to `wifaq-cards` and no `add_repo` tool, so the data repo could not be attached; Drive used as before. Queued: the run needs `add_repo` (or the repo added to the task's repository list) before `eng-data-repo` can finish.
- 13 Oct 2026 (chat, after the 1:10 am run): photo of Bushra vol 7 pp. 223–224 (asked on the panel). Applied: card 3 of 08-31 now follows the printed «ولا بأس ببيع السرقين، ويكره بيع العذرة» (مکروہ; teacher said جائز نہیں) with K7(224) tags; فصل في البيع heading frac 0.3; also confirms «المكاعمة» on 223.
- 11 Oct 2026, 7:00 am (panel note): "i already placed Mishkat (title page, a page with hadith numbers, contents of both volumes); title + contents pages of their Baydawi, Nukhba, Tibyan and Aina in the Wifaq folder. Please check and tell me if you need anything else." → 12 Oct run: the 27 photos in `automation/from-me/` (IMG_20261009_150554 … 151219) are catalogued in `src/auto/from-me.md`. Present: Taysir title + full contents; Tibyan title + contents; Nuzhat al-Nazar title + contents (sheet for book pp. 260–261 missing); Baydawi title + 3 text pages (no contents); Mishkat vols 1–2 titles + contents (vol 2 only its last contents page); Aina title (151219 reads as blank). Not found: a Mishkat text page with hadith numbers. Asked him in the reply for: one Mishkat text page, Baydawi and Aina contents, Mishkat vol 2 first contents pages.
- 9 Oct 2026, 3:13 pm: five photos dropped in Drive `automation/from-me/` (IMG_20261009_150631 … 151138). The first is the contents (فہرست, book pp. 220–221) of **تیسیر مصطلح الحدیث** (Tahhan): input for `eng-other-books`. Not yet transcribed.
