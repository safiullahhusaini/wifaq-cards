# Hidaya 3 · cards drafted from the <KEY> lesson (transcript "<file>.md")
# Book = Bushra 8-vol edition, VOLUME 5; pages are its printed pages (PDF page − 1). Range: <start passage> → <end passage>.
LESSON = "<KEY>"                 # this year's class: "<DATE>-1448"; last year's class: "<DATE>"
SOURCE = "this-year"             # "this-year" (اس سال کی کلاس) or "last-year" (پچھلے سال کی کلاس)
RECORDING = "<recording file name, e.g. Hidaya Saalis 11 July 2026.m4a>"
MINUTES = None                   # length of the recording in minutes, e.g. 42.1


def U(ts, lesson=None):          # teacher, at this transcript timestamp
    d = {"t": "u", "v": ts}
    if lesson:
        d["l"] = lesson
    return d


def K5(p):                       # the matn says this: vol-5 printed page in the 8-volume Bushra edition
    return {"t": "k5", "v": int(p)}


def S(x):                        # a sharh quoted in the footnotes (name + vol/page as printed), or the interlinear gloss
    return {"t": "s", "v": x}


A = {"t": "a", "v": ""}          # your own wording, no source: use rarely
GLOSS = "بشریٰ ٨ جلدی، بین السطور"

CARDS = [
    {
        "v5": 253, "v5_frac": 0.1,          # passage start: vol-5 printed page + fraction down that page's matn (0 = top, 1 = bottom)
        "v5_end": 254, "v5_end_frac": 0.5,  # passage end
        "lesson": LESSON, "ts": "0:00:08",  # where the teacher starts this sub-topic (copy from the transcript)
        "title": "…",
        "start": "…",                       # first words of the passage in the matn, as printed
        "start_note": "",
        "norec": "",                        # only when the recording does not explain this passage
        "tamheed": [("…", [U("0:00:08")])],
        "masala": [("…", [U("0:01:00"), K5(253)])],
        "dalil": [],
        "ikhtilaf": [],
        "faida": [],
        "lughat": [("…", "…", [U("0:01:00")])],
    },
]
GAPS = []    # [("v5 255–256", "what the book has there and why the recording doesn't explain it")]
NOTES = []   # for Claude: teacher-vs-book conflicts, the teacher's exam hints, anything doubtful
