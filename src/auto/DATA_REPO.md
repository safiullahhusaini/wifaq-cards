# wifaq-data: private copy of the Drive working files (since 13 Oct 2026)

**Why.** Night runs read transcripts, OCR, status files and audio through the Drive connector. Small files come back inline as base64, which fills the run's context and uses up the Pro allowance. Larger files need sub-agents, the connector stops at about 5.7 MB, and it cannot rewrite a file (so `daily_config.json` could never be updated). A private GitHub repo can be cloned for nothing and written with git.

**Repo:** `safiullahhusaini/wifaq-data`, **private**. The user creates it and gives the Claude GitHub app access. Never copy its contents into the public `wifaq-cards` repo (transcripts and OCR stay private).

## What is in it

Filled by **cell 9 of the Daily notebook** (`src/colab/daily/`) each time the user runs it. It mirrors Drive `My Drive/Wifaq 1448/`:

| In wifaq-data | From Drive `Wifaq 1448/` | Notes |
|---|---|---|
| `transcripts/<book>/*.md` | `transcripts/<book>/` | Every book. Folders starting with `_` (`_original`, `_replaced`, `_redo`) are skipped. A file removed from Drive is removed here. |
| `status/*` | top-level `.csv`, `.md`, `.json`, `.txt` files | `timestamp_fix.csv`, `transcribe_status.md`, `recording_ids.csv`, … |
| `ocr/<volume>/*.md` | `Books/text/<volume>/` | OCR text only, no PDFs. Hidaya 4 = `ocr/Al Hidayah Vol-7/` (and later `Al Hidayah Vol-8/`). |
| `audio/<book>/*.ogg`, `audio/index.csv` | `web_audio_opus/` | Only the books in `daily_config.json → data_audio_books` (default: `opus_books`). A part already here with the same size is not copied again. |
| `automation/…` | `automation/…` | Files over 20 MB skipped. `daily_config.json` is the exception: see below. |
| `SYNCED.md` | — | Time of the last sync and file counts. |

**`daily_config.json`.** The copy here (`automation/daily_config.json`) is the one the Daily notebook reads (cell 2). Runs update it with git. The notebook copies it back to Drive, so the Drive copy stays current as a fallback. If the repo has none yet, the first sync copies Drive's.

## How a run reads it (once `eng-data-repo` is done)

1. `add_repo` `safiullahhusaini/wifaq-data` with push access (push is only needed for `daily_config.json`).
2. Blobless sparse clone, so the audio isn't downloaded:
   ```
   git clone --depth 1 --filter=blob:none --sparse https://github.com/safiullahhusaini/wifaq-data /home/claude/wifaq-data
   git -C /home/claude/wifaq-data sparse-checkout set --no-cone '/transcripts/' '/status/' '/automation/' '/SYNCED.md' '/ocr/Al Hidayah Vol-7/' '/audio/index.csv'
   ```
   For one lesson's audio: `git -C /home/claude/wifaq-data sparse-checkout add '/audio/ہدایہ جلد رابع/2025-09-07*'`.
3. Point the brief's OCR path at it: `<cards repo>/.cache/v7ocr` → `/home/claude/wifaq-data/ocr/Al Hidayah Vol-7`.
4. Read `SYNCED.md`. If it is older than the Daily run in `automation/daily_done.md`, the user stopped before cell 9: use Drive for anything newer.
5. To change the Daily to-do: edit `automation/daily_config.json`, commit `config: …`, `git pull --rebase`, push.

## Setup (the user, once)

1. GitHub → **New repository** → name `wifaq-data` → **Private** → tick **Add a README file** → Create.
2. Give the Claude GitHub app access to it (GitHub → Settings → Applications → the Claude app → Configure → Repository access → add `wifaq-data` → Save). Nothing to do if the app already has access to all repositories.
3. GitHub → Settings → Developer settings → Personal access tokens → **Fine-grained tokens** → Generate new token: name `wifaq-data colab`, expiration 31 Jan 2027, Repository access → Only select repositories → `wifaq-data`, Permissions → Repository permissions → **Contents: Read and write** → Generate, copy the token.
4. Colab → the 🔑 Secrets panel on the left → Add new secret: name `GITHUB_DATA_TOKEN`, value = the token, **Notebook access** on.
5. Run the Daily notebook as usual. The first cell-9 sync copies about 400 MB of Hidaya 4 audio and takes several minutes; later days copy only what changed.
6. Tell Claude (panel note or chat) "wifaq-data ready". The next run checks it and does `eng-data-repo`.
