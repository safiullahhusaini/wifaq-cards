# Sources of the card site

Read `HANDOVER.md` first: it covers the project, the data sources, the pipeline, the open work and the limits.

```
src/
  HANDOVER.md            start here
  cards/
    build_site.py        builds every page into the repo root (python3 build_site.py)
    h4_site.py           Hidaya 4: one page per kitab + the paper's contents page
    h4_data.py           gathers lesson cards, maps pages, splits by kitab → bab/fasl, lesson + audio info
    h4_pagemap.py        Bushra vol-7 position → colleagues' page (uses OCR if present, else h4_pagemap_cache.json)
    h4_toc.py            colleagues' contents of Hidaya 4 (level, title, page)
    h4_cards.py          5 pilot cards (18 May, pp. 1609–1611, verified pages)
    h4/                  one card file per lesson (h4_<date>.py) + BRIEF.md for card-drafting agents
    kitab_template.html  the kitab page (contents view, fasl view, recordings sheet, player)
    m1_build.py, m1_cards.py   Mishkat vol 1 sample
    legacy/              earlier pilots (Hidaya 3 Kitab al-Sarf viewer, first Hidaya 4 page)
  colab/                 Colab notebooks and their sources (pipeline, Drive IDs, timestamp repair, cell 7 Opus)
  data/recordings.csv    Hidaya 4 + Mishkat recordings with Drive IDs (trimmed from Drive's recording_ids.csv)
  qa/                    independent checks of card timestamps and content
  tracker/               builder of the study tracker spreadsheet
```

Requirements: `pip install --break-system-packages rapidfuzz numpy scipy`; `ffprobe` (for split audio without parts.json).
