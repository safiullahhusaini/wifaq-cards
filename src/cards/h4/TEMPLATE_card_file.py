# Hidaya 4 · cards drafted from the <DATE> lesson (transcript "<DATE> الهدايه الرابع كتاب ....md")
LESSON = "<DATE>"


def U(ts, lesson=None):          # teacher, at this transcript timestamp
    d = {"t": "u", "v": ts}
    if lesson:
        d["l"] = lesson
    return d


def K7(p):                       # the matn says this: vol-7 printed page in the 8-volume Bushra edition
    return {"t": "k7", "v": int(p)}


def S(x):                        # a sharh quoted in the footnotes (name + vol/page as printed), or the interlinear gloss
    return {"t": "s", "v": x}


A = {"t": "a", "v": ""}          # your own wording, no source: use rarely
GLOSS = "بشریٰ ٨ جلدی، بین السطور"

CARDS = [
    {
        "v7": 29, "v7_frac": 0.2,           # passage start: vol-7 printed page + fraction down that page's matn (0 = top, 1 = bottom)
        "v7_end": 31, "v7_end_frac": 0.5,   # passage end
        "lesson": LESSON, "ts": "0:00:06",  # where the teacher starts this sub-topic (copy from the transcript)
        "title": "ادھار قیمت پر بکی زمین: کیا شفیع کو بھی مہلت ملے گی؟",
        "start": "وإذا باع بثمن مؤجَّل فللشفيع الخيار",   # first words of the passage in the matn, as printed
        "start_note": "",
        "norec": "",                        # only when the recording does not explain this passage
        "tamheed": [("…", [U("0:00:06")])],
        "masala": [("…", [U("0:05:00"), K7(29)])],
        "dalil": [],
        "ikhtilaf": [],
        "faida": [],
        "lughat": [("مؤجَّل", "ادھار، مدت والا", [U("0:05:00")])],
    },
]
GAPS = []    # [("v7 24–28", "what the book has there and why the recording doesn't explain it")]
NOTES = []   # for Claude: teacher-vs-book conflicts, the teacher's exam hints, anything doubtful
