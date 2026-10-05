# Hidaya 4 · cards drafted from the 2025-07-06 lesson (transcript "2025-07-06 الهدايه الرابع كتاب الشفعة.md")
# NO CARDS: this recording is not a Hidaya 4 lesson. See NOTES.
LESSON = "2025-07-06"


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

CARDS = []
GAPS = []    # none: the vol-7 كتاب القسمة sequence runs unbroken from 2025-07-05 to 2025-07-07 (see NOTES)
NOTES = [
    "Misfiled recording: despite the title and the 'ہدایہ جلد رابع · سبق 25' header, the 2025-07-06 transcript contains no كتاب القسمة or any vol-7 text. "
    "It is a Hidaya 3 (كتاب البيوع) class: باب البيع الفاسد · فصل في أحكامه, from «وإذا قبض المشتري المبيع في البيع الفاسد بأمر البائع» (0:00:24) "
    "to «وهذا لأن المثل صورة ومعنى أعدل من المثل معنى» (0:17:26). The teacher gives the page as 1109 in the colleagues' edition (0:00:14).",
    "Book location: Bushra 8-vol edition vol 5, فصل في أحكامه starts at printed p.128 (vol-5 contents page, OCR file p0543-0543.md in Drive folder 1Jtc5xpikshh_3eB5m3dJ2Osy_AulVVze). "
    "The lesson covers roughly the first 2–3 pages of that فصل.",
    "Different teacher/class: he says he has a sore eye and stops early, and that 'آج جو میری دو کلاسیں تھیں پوری نہیں ہوئیں' (0:18:48–0:18:58). "
    "The Hidaya 4 teacher's 5 July class ends at «ولو تهايا في دار واحدة» ('یہاں سے آگے انشاءاللہ کل پڑھیں گے', 0:24:58), and the 7 July class resumes exactly there (ص 1684, فصل في المهايأة, 0:00:01) "
    "saying 'مہایاہ کے بارے میں کل بتایا تھا'. So nothing in vol 7 falls between them.",
    "If wanted, this transcript can feed Hidaya 3 cards (vol-5 pagination, like claude/cards/hidaya3-kitab-al-sarf-253-258.md). Sub-topics by timestamp: "
    "0:00:24 main ruling (ملک بالقبض، قیمت لازم) + امام شافعی کا اختلاف and his proofs (محظور، النهي نسخ للمشروعية، لا يفيده قبل القبض، كالبيع بالميتة/الخمر); "
    "0:04:33 احناف کی دلیل and answers (ركن البيع صدر من أهله، النهي يقرر المشروعية، البيع وقت النداء، قبل القبض ملک کیوں نہیں، بمنزلة الهبة، الميتة ليست بمال، الخمر مثمنًا); "
    "0:13:58 قیود: قبضہ بإذن البائع (صراحۃً یا دلالۃً، مجلسِ عقد میں استحساناً، ہبہ پر قیاس), عوضان كل منهما مال (میتہ، دم، حر، ریح، نفیِ ثمن خارج); "
    "0:16:47 ذوات القيم میں قیمت، ذوات الأمثال میں مثل (غصب کی طرح؛ استاد کی مثال: دس من گندم بمقابلہ گائے، 0:17:44).",
]
