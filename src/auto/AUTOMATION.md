# Automated card runs: protocol (read this first in every scheduled run)

Written 8 Oct 2026. The user (Syed) asked for the remaining cards to be made automatically over the coming days, with as little manual work as possible, and to be asked only about important design decisions. **Hidaya 3 is skipped for now (user, 8 Oct).**

You are one scheduled run. You start cold: nothing from earlier runs is in your context except what is written in this repo, in the control panel, and in Drive. Work carefully and push often, because a run can be cut off by usage limits at any moment.

## 0. Files you rely on

| File | What it is |
|---|---|
| `src/HANDOVER.md` | Project facts, pipeline, limits, decisions. Section 5 is how a lesson becomes cards. |
| `src/auto/AUTOMATION.md` | This protocol. |
| `src/auto/queue.json` | Every remaining work item with its state, plus `settings`. The single to-do list. |
| `src/auto/INBOX.md` | The user's answers and notes, copied from the control panel. Durable record. |
| `src/auto/runs.md` | One short line per run (newest first). |
| Control panel "Wifaq Cards Control" | Private artifact https://claude.ai/artifact/GqWNYfh4ZBwfozCFqAwbSN (also in `queue.json → settings.panel_url`). Database: collections `questions`, `notes`; documents `status/now` (you write) and `control/settings` (the user writes: `paused`, `max_lessons_per_run`). Read and write it with the `ArtifactData` tool (load it with ToolSearch `select:ArtifactData`); every write to an existing document needs `if_version` from your read. Page source: `src/auto/panel/panel.html`. |
| Drive `Wifaq 1448/automation/` (folder `19mMOc1kOSN5W-OId2Wtp0uuuhfmkkVd-`) | `daily_config.json` (`14cUGi-JrijwUDqhm-xJUGwHXlvJNvg8e`): what the user's daily Colab notebook does (transcripts to redo, books to repair, books to make Opus copies for); you keep it current with `update_file`. `daily_done.md`: what the last daily run did. `from-me/` (`19CUJI0EcDuV6OLmneplrXgOdfkTVnU4C`): photos and PDFs the user drops for you (editions, contents pages, past papers). |
| Daily notebook | `src/colab/daily/Wifaq_1448_Daily.ipynb` (built by `build_daily_nb.py` from `retx_core.py`, the tsfix code and cell 7). The user opens it from GitHub: https://colab.research.google.com/github/safiullahhusaini/wifaq-cards/blob/main/src/colab/daily/Wifaq_1448_Daily.ipynb, so a pushed rebuild reaches him without uploads. |

## 1. Start

1. Load tools in one ToolSearch call: `select:ArtifactData,SendUserMessage,mcp__Google_Drive__search_files,mcp__Google_Drive__read_file_content,mcp__Google_Drive__download_file_content,mcp__Google_Drive__create_file,mcp__Google_Drive__update_file`.
2. Attach and clone the repo (HANDOVER section 3, steps 1–2), make the two symlinks the brief expects (`/home/claude/wifaq/cards` → `<repo>/src/cards`, `/home/claude/wifaq/v7ocr` → `<repo>/.cache/v7ocr`).
3. Read `src/HANDOVER.md`, this file, `src/auto/queue.json`, `src/auto/INBOX.md`, and the top of `src/auto/runs.md`.
4. Read the panel's `control/settings` (it overrides `queue.json → settings` for `paused` and `max_lessons_per_run`). If paused, or a `claim` in the queue is younger than 5 hours (another run is working), write one line in `runs.md`, push, and stop.

## 2. Inbox first

1. `ArtifactData list` on `questions` and `notes` of the panel. Also look in Drive `automation/from-me/` for files added since the last run (list them in `INBOX.md`).
2. For each question with an `answer` and `state: "answered"`: copy question + answer to `INBOX.md` under "Decisions", apply it (queue settings, HANDOVER section 9, code), then `update` it to `state: "applied"` with a one-line `reply` saying what you did.
3. For each note with `state: "new"`: copy it to `INBOX.md` under "Notes", act on it if it is clear and small (a wrong card line, a typo, a request you can do this run), otherwise turn it into a queue item. `update` it to `state: "done"` or `"queued"` with a short Urdu or English `reply` (match the user's language).
4. A note or answer never overrides HANDOVER section 9 silently: if it conflicts with a recorded decision, ask (section 7) instead of guessing.
5. If ArtifactData is not available in this session, say so in the run summary and carry on with the queue.

## 3. Refresh readiness

1. Download `timestamp_fix.csv` (Drive id `16X4zSGH-9Cxt5xl1HP5bwB3Jo-tUT04y`) and `transcribe_status.md` (`1ayakHwWBQneff0YEKHv_rQX5v7PvSvfB`) and decode them in python (base64 or saved-to-disk JSON; never retype).
2. An item in state `redo` becomes `ready` when its transcript's latest row in `timestamp_fix.csv` is `fixed` (not "text missing") with `matched_pct` ≥ 75 **and** is newer than the time the item was set to `redo`. Record the new repair status in the item.
3. Items in `wait_transcript` become `redo`-checked the same way once a transcript exists.
4. Rewrite Drive `Wifaq 1448/automation/daily_config.json` so its `redo` list holds exactly the transcript files of items still in `redo` (format in section 9).

## 4. Choose and claim work

- Order: `settings.book_order`, and inside a book the queue order (book order of kitabs, then date). Prefer finishing a kitab before starting the next, but don't wait: if a lesson is blocked on re-transcription, card the next ready one and note the hole (`GAPS` already shows unrecorded/unexplained parts on the site).
- At most `settings.max_lessons_per_run` lessons per run, plus at most one `eng` item whose `needs` are met. Do an `eng` item first when ready lessons depend on it (for example the vol-8 page map before الوصايا).
- `retime` items (re-time an already carded lesson after its transcript was redone) are cheap: do them when ready, they don't count against the lesson limit.
- Claim: set `claim: {"run": "<ISO time>", "by": "<session link if known>"}` on the chosen items, commit `queue: claim …`, `git fetch origin main && git rebase origin/main`, push. If the push conflicts on the queue, re-read it and choose again.

## 5. Make a lesson's cards

Follow HANDOVER section 5 exactly (it is the tested pipeline), with these rules for unattended runs:

1. **Prepare** (yourself, not an agent): find the lesson's transcript in Drive, check it has a `- وقت:` line, find its start and end passages in the OCR with rapidfuzz, and note the previous lesson's last card and where the next lesson starts. If the kitab is new: download its OCR pages (sub-agent), add its headings to `HEADINGS` and `RUNNING` in `h4_pagemap.py`, and compare existing card pages before and after (HANDOVER section 6).
2. **Draft**: one sub-agent with `src/cards/h4/BRIEF.md`, model `settings.draft_model` (`inherit` = same as you). Give it the date, file name, start/end passages, previous card, the teacher's slips you noticed.
3. **QA**: a separate sub-agent that has not seen the draft being made (`settings.qa`: `full` = every line, the current standard; `focused` = every ruling, attribution and ikhtilaf line plus the mechanical timestamp check). Fix what it finds. Check S tags against the OCR yourself.
4. **Audio**: add the Opus part(s) (HANDOVER section 7). Same-date lessons: key them by the queue id's suffix (`2025-09-27-ashriba` → `hidaya4/audio/2025-09-27-ashriba.ogg`); extend `h4_data.py` the first time this happens, keeping old keys working.
5. **Build, check, push**: `python3 build_site.py`, Playwright screenshots at 390×844 of the changed kitab page (contents view, one fasl, the recordings sheet), then commit and push. One commit per lesson, message `cards: <kitab> <date> (<n> cards)`.
6. Set the item to `done` with `cards: <n>` and a one-line `qa` summary, clear its claim, push the queue. Then the next lesson.

Hard rules (from the user, unchanged): every line traceable to the teacher or the book; never invent a timestamp; the teacher's own examples; quality over speed; colleagues' page numbers; Hidaya 3 not now; don't card a lesson whose transcript is not repaired.

## 6. Engineering items

`eng` items in the queue say what they need (`needs`) and what done means (`done_when`). Work on one only when its needs are met. Test like the earlier sessions did (local build, Playwright, byte-compare of pages that should not change). Record the result in HANDOVER and close the item.

## 7. Asking the user

Ask only when the answer changes what gets built and a wrong guess would be costly to undo: design of a new kind of page, which edition or numbering to follow, what to drop or simplify, anything that contradicts a recorded decision. Do not ask about things you can test or decide from HANDOVER (code structure, file names, ids, retries).

To ask: `ArtifactData set` a document in `questions` with
`{"q": "<question, in Urdu if the user wrote in Urdu, else plain English>", "why": "<one line: what depends on it>", "options": ["<recommended> (recommended)", "<other>", ...], "asked": "<ISO time>", "by_run": "<date time>", "state": "open", "answer": ""}`.
Then carry on with other work; never wait inside a run. Mention the question in the run summary so the notification shows it. The run that later sees the answer applies it (section 2).

## 8. End of every run (also when stopping early)

1. Clear your remaining claims; push `queue.json`.
2. Prepend one line to `runs.md`: `- 8 Oct, 1:52 pm · 2 lessons (الأضحية 08-09, 08-10) · 14 cards · QA: 0 wrong rulings, 5 nits fixed · asked: 0 · next: الكراهية 08-30`.
3. Update HANDOVER section 4 (what is live) and section 8 (backlog) if they changed. Copy HANDOVER to the project doc `claude/HANDOVER.md` when the Projects tool is available.
4. `ArtifactData set` `status/now` (format in section 9).
5. Final message (it becomes the notification): 2–4 short lines — what went live, open questions for the user, anything the user must do (for example "Run the Wifaq Daily notebook today"). Times in 12-hour format.

## 9. Formats

`status/now`:
```json
{"updated": "8 Oct 2026, 1:52 pm", "last_run": "<one line as in runs.md>",
 "books": [{"name": "ہدایہ جلد رابع", "done": 19, "ready": 45, "redo": 20, "total": 84}],
 "user_todo": ["<short Urdu/English line>"], "next": "<what the next run will do>"}
```

`daily_config.json` (Drive, `Wifaq 1448/automation/`):
```json
{"updated": "...", "redo": [{"book": "ہدایہ جلد رابع", "file": "2025-08-16 الهدايه الرابع كتاب الكراهية.md"}],
 "repair_books": ["ہدایہ جلد رابع", "مشکوٰۃ المصابیح جلد اول"], "opus_books": ["ہدایہ جلد رابع"],
 "skip_books": ["ہدایہ جلد ثالث"]}
```

## 10. Never

- Never force-push, rewrite history, or delete anything in Drive. Drive writes only inside `Wifaq 1448/automation/`.
- Never publish transcripts or OCR text in the public repo (the repo is public; `.cache/` is gitignored for that reason).
- Never add back what HANDOVER section 9 says was removed (original-file downloads, file picker, Drive time links).
- Never change the scheduled tasks themselves; ask the user through the panel if the schedule should change.
- Never run more than 4 sub-agents at once.
