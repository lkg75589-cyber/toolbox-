"""🧰 صندوق الأدوات: 30 أداة في مشروع Flask واحد (بدون مفاتيح API وبدون ذكاء اصطناعي)
تشغيل:  pip install flask pypdf   ثم   python app.py   ثم افتح  http://127.0.0.1:5000
"""
import ast, operator as op, random, string, json, re, hashlib, base64, shutil, secrets, os
import urllib.request, urllib.parse
from datetime import date, datetime
from collections import Counter
from flask import Flask, request, redirect, jsonify

app = Flask(__name__)
DB = os.path.join(os.environ.get("ANDROID_PRIVATE", "."), "data.json")  # مكان آمن للحفظ داخل الأندرويد


def load():
    try:
        return json.load(open(DB, encoding="utf-8"))
    except Exception:
        return {}


def save(d):
    json.dump(d, open(DB, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def lst(key):
    d = load()
    return d, d.setdefault(key, [])


def get(url):
    r = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(r, timeout=10).read().decode("utf-8", "ignore")


# ───────── 1) الأدوات الـ 17 من الفيديو ─────────
OPS = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul, ast.Div: op.truediv,
       ast.Pow: op.pow, ast.Mod: op.mod, ast.USub: op.neg}


def ev(n):
    if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
        return n.value
    if isinstance(n, ast.BinOp):
        return OPS[type(n.op)](ev(n.left), ev(n.right))
    if isinstance(n, ast.UnaryOp):
        return OPS[type(n.op)](ev(n.operand))
    raise ValueError("عملية غير مسموحة")


def calc(f):
    r = ev(ast.parse(f["expr"], mode="eval").body)
    return int(r) if isinstance(r, float) and r.is_integer() else round(r, 10) if isinstance(r, float) else r


def todo(f):
    d, t = lst("todo")
    a, x = f["act"], f["text"]
    if a == "add" and x:
        t.append({"t": x, "done": False})
    elif a == "done":
        t[int(x) - 1]["done"] = not t[int(x) - 1]["done"]
    elif a == "del":
        t.pop(int(x) - 1)
    save(d)
    return "\n".join(f"{i}. [{'x' if k['done'] else ' '}] {k['t']}" for i, k in enumerate(t, 1)) or "القائمة فارغة"


def guess(f):
    d = load()
    n = int(f["n"])
    if n == 0 or "secret" not in d:
        d["secret"], d["tries"] = random.randint(1, 100), 0
        if n == 0:
            save(d)
            return "لعبة جديدة. خمّن رقم من 1 إلى 100"
    d["tries"] += 1
    s = d["secret"]
    if n == s:
        msg = f"صح! بعد {d['tries']} محاولة 🎉"
        d.pop("secret")
    else:
        msg = "الرقم أكبر ⬆️" if n < s else "الرقم أصغر ⬇️"
    save(d)
    return msg


def pw(f):
    c = string.ascii_letters + string.digits + ("!@#$%^&*" if f.get("sym") else "")
    return "\n".join("".join(secrets.choice(c) for _ in range(int(f["len"]))) for _ in range(5))


def cur(f):  # API مجاني بدون مفتاح
    a, b = f["a"].upper(), f["b"].upper()
    r = json.loads(get(f"https://open.er-api.com/v6/latest/{a}"))["rates"]
    return f"{f['amt']} {a} = {float(f['amt']) * r[b]:,.2f} {b}"


def remind(f):
    d, r = lst("rem")
    now = datetime.now().timestamp()
    if f["text"]:
        r.append({"t": f["text"], "due": now + float(f["min"]) * 60})
        save(d)
    return "\n".join(("🔔 حان الوقت: " if x["due"] <= now else f"⏳ بعد {int((x['due'] - now) / 60) + 1} د: ") + x["t"]
                     for x in r) or "لا توجد تنبيهات"


def notes(f):
    d, n = lst("notes")
    if f["act"] == "add" and f["text"]:
        n.append(f["text"])
    elif f["act"] == "del":
        n.pop(int(f["text"]) - 1)
    save(d)
    return "\n".join(f"{i}. {x}" for i, x in enumerate(n, 1)) or "لا توجد ملاحظات"


def wc(f):
    t = f["text"]
    return f"كلمات: {len(t.split())}\nأحرف: {len(t)}\nأسطر: {len(t.splitlines())}"


def rps(f):
    m = ["حجر", "ورقة", "مقص"]
    u, c = m.index(f["c"]), random.randrange(3)
    k = "tie" if u == c else "win" if (u - c) % 3 == 1 else "lose"
    return {"u": m[u], "c": m[c], "k": k, "r": {"tie": "تعادل", "win": "فزت 🎉", "lose": "خسرت 😅"}[k]}


EXT = {"صور": ".jpg .jpeg .png .gif .webp", "مستندات": ".pdf .doc .docx .txt .xlsx .pptx",
       "فيديو": ".mp4 .mkv .mov .avi", "صوت": ".mp3 .wav .m4a", "ضغط": ".zip .rar .7z"}


def organize(f):
    p, out = f["path"], []
    for n in os.listdir(p):
        fp = os.path.join(p, n)
        if os.path.isfile(fp):
            e = os.path.splitext(n)[1].lower()
            k = next((k for k, v in EXT.items() if e in v.split()), "أخرى")
            out.append(f"{n} → {k}")
            if f.get("go"):
                os.makedirs(os.path.join(p, k), exist_ok=True)
                shutil.move(fp, os.path.join(p, k, n))
    return ("تم النقل:\n" if f.get("go") else "معاينة فقط (فعّل التنفيذ للنقل):\n") + "\n".join(out)


def prices(f):
    m = re.findall(r"(?:\$|USD|IQD)\s?\d[\d,]*\.?\d*|\d[\d,]*\.?\d*\s?(?:\$|USD|IQD|دينار)", get(f["url"]))
    return "\n".join(dict.fromkeys(m[:20])) or "ما لقيت أسعار"


W = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]


def win(b):
    return next((b[a] for a, x, c in W if b[a] != " " and b[a] == b[x] == b[c]), None)


def ttt(f):
    d = load()
    b = d.get("ttt") or [" "] * 9
    n, msg = int(f["cell"]), ""
    if n == 0 or (n > 0 and (win(b) or " " not in b)):
        b = [" "] * 9
    elif n > 0:
        if b[n - 1] != " ":
            msg = "الخانة مشغولة"
        else:
            b[n - 1] = "X"
            if not win(b) and " " in b:
                b[random.choice([i for i, x in enumerate(b) if x == " "])] = "O"
    w = win(b)
    msg = msg or ("فزت 🎉" if w == "X" else "فاز الكمبيوتر 😅" if w == "O" else "تعادل" if " " not in b else "")
    d["ttt"] = b
    save(d)
    return {"b": b, "m": msg}


def weather(f):  # Open-Meteo مجاني بدون مفتاح
    g = json.loads(get("https://geocoding-api.open-meteo.com/v1/search?count=1&name=" + urllib.parse.quote(f["city"])))["results"][0]
    w = json.loads(get(f"https://api.open-meteo.com/v1/forecast?latitude={g['latitude']}&longitude={g['longitude']}"
                       "&current=temperature_2m,wind_speed_10m,relative_humidity_2m"))["current"]
    return f"{g['name']}, {g.get('country', '')}\n🌡 {w['temperature_2m']}°C\n💧 {w['relative_humidity_2m']}%\n💨 {w['wind_speed_10m']} km/h"


def spend(f):
    d, e = lst("exp")
    if f["amt"]:
        e.append({"a": float(f["amt"]), "c": f["cat"] or "عام"})
        save(d)
    t = {}
    for x in e:
        t[x["c"]] = t.get(x["c"], 0) + x["a"]
    return "\n".join(f"{k}: {v:,.2f}" for k, v in t.items()) + f"\n— المجموع: {sum(x['a'] for x in e):,.2f}"


def short(f):
    d = load()
    c = secrets.token_urlsafe(4)
    d.setdefault("links", {})[c] = f["url"]
    save(d)
    return request.host_url + "s/" + c


@app.route("/s/<c>")
def go(c):
    return redirect(load().get("links", {}).get(c, "/"))


Q = [("عاصمة العراق؟", ["بغداد", "البصرة", "أربيل"], "بغداد"), ("كم ناتج 2+2×2؟", ["8", "6", "4"], "6"),
     ("أكبر كوكب بالمجموعة الشمسية؟", ["زحل", "الأرض", "المشتري"], "المشتري"), ("عاصمة اليابان؟", ["طوكيو", "سيول", "بكين"], "طوكيو"),
     ("كم يوم بالأسبوع؟", ["5", "7", "10"], "7"), ("أطول نهر بالعراق؟", ["دجلة", "الفرات", "ديالى"], "الفرات"),
     ("لغة Flask؟", ["جافا", "بايثون", "سي"], "بايثون"), ("كم ثانية بالدقيقة؟", ["60", "100", "30"], "60")]


def quiz(f):
    d, m = load(), ""
    if f.get("ans") and "q" in d:
        ok = f["ans"] == Q[d["q"]][2]
        d["s"] = d.get("s", 0) + ok
        m = "✅ صح" if ok else "❌ الجواب: " + Q[d["q"]][2]
    d["q"] = random.randrange(len(Q))
    save(d)
    q = Q[d["q"]]
    o = q[1][:]
    random.shuffle(o)
    return {"q": q[0], "o": o, "m": m, "s": d.get("s", 0)}


def pdf(f):
    from pypdf import PdfReader
    r = PdfReader(request.files["file"].stream)
    return f"عدد الصفحات: {len(r.pages)}\n\n" + r.pages[int(f["page"]) - 1].extract_text()


# ───────── 2) الأدوات الـ 13 الإضافية ─────────
U = {"km_mi": .621371, "mi_km": 1.609344, "kg_lb": 2.204623, "lb_kg": .453592,
     "m_ft": 3.28084, "ft_m": .3048, "cm_in": .393701, "in_cm": 2.54}


def unit(f):
    v, k = float(f["v"]), f["k"]
    if k == "C_F": return f"{v * 9 / 5 + 32:.2f} °F"
    if k == "F_C": return f"{(v - 32) * 5 / 9:.2f} °C"
    return f"{v * U[k]:.4f}"


def bmi(f):
    b = float(f["kg"]) / (float(f["cm"]) / 100) ** 2
    return f"BMI = {b:.1f}\n" + ("نحافة" if b < 18.5 else "طبيعي" if b < 25 else "وزن زائد" if b < 30 else "سمنة")


def hs(f):
    return "\n".join(f"{a}: {hashlib.new(a, f['text'].encode()).hexdigest()}" for a in ("md5", "sha1", "sha256"))


def b64(f):
    t = f["text"]
    return base64.b64encode(t.encode()).decode() if f["m"] == "enc" else base64.b64decode(t).decode()


def age(f):
    b, t = date.fromisoformat(f["d"]), date.today()
    y = t.year - b.year - ((t.month, t.day) < (b.month, b.day))
    return f"عمرك {y} سنة\nعشت {(t - b).days:,} يوم"


def dice(f):
    m = f["m"]
    return random.randint(1, 6) if m == "dice" else random.choice(["صورة", "كتابة"]) if m == "coin" \
        else random.choice([x.strip() for x in f["text"].split(",")])


def color(f):
    h = f["hex"].lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"RGB({r}, {g}, {b})"


def base(f):
    n = int(f["n"])
    return f"ثنائي: {bin(n)[2:]}\nثماني: {oct(n)[2:]}\nست عشري: {hex(n)[2:]}"


def js(f):
    return json.dumps(json.loads(f["text"]), ensure_ascii=False, indent=2)


def bill(f):
    t = float(f["t"]) * (1 + float(f["tip"] or 0) / 100)
    return f"المجموع: {t:,.2f}\nلكل شخص: {t / int(f['n']):,.2f}"


M = dict(zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
             ".- -... -.-. -.. . ..-. --. .... .. .--- -.- .-.. -- -. --- .--. --.- .-. ... - ..- ...- .-- -..- -.-- --.. "
             "----- .---- ..--- ...-- ....- ..... -.... --... ---.. ----.".split()))


def morse(f):
    return " / ".join(" ".join(M.get(c, "?") for c in w) for w in f["text"].upper().split())


def caesar(f):
    k = int(f["k"])

    def sh(c):
        if not (c.isascii() and c.isalpha()):
            return c
        s = 65 if c.isupper() else 97
        return chr((ord(c) - s + k) % 26 + s)
    return "".join(sh(c) for c in f["text"])


def freq(f):
    return "\n".join(f"{w}: {n}" for w, n in Counter(re.findall(r"\w+", f["text"].lower())).most_common(10))


# ───────── 3) سجل الأدوات + الواجهة (تنبني تلقائياً) ─────────
def F(k, l, t="text", o=None): return (k, l, t, o)


LIST = [("add", "إضافة"), ("del", "حذف (رقم)"), ("list", "عرض")]
UK = list(U) + ["C_F", "F_C"]
T = [
    ("calc", "🧮", "الحاسبة", calc, [F("expr", "مثال: 2+3*4")]),
    ("todo", "✅", "قائمة مهام", todo, [F("act", "", "sel", [("add", "إضافة"), ("done", "إنجاز (رقم)"), ("del", "حذف (رقم)"), ("list", "عرض")]), F("text", "النص أو الرقم")]),
    ("guess", "🎯", "خمّن الرقم", guess, [F("n", "رقمك (0 = لعبة جديدة)", "num")]),
    ("pw", "🔑", "مولد باسوردات", pw, [F("len", "الطول", "range", (6, 32, 14)), F("sym", "إضافة رموز", "chk")]),
    ("cur", "💱", "محول عملات", cur, [F("amt", "المبلغ", "num"), F("a", "من (مثل USD)"), F("b", "إلى (مثل IQD)")]),
    ("rem", "⏰", "منبّه", remind, [F("text", "التذكير (فارغ = عرض)"), F("min", "بعد كم دقيقة", "num")]),
    ("notes", "📝", "دفتر ملاحظات", notes, [F("act", "", "sel", LIST), F("text", "الملاحظة أو الرقم")]),
    ("wc", "🔤", "عدّاد كلمات", wc, [F("text", "النص", "area")]),
    ("rps", "✊", "حجر ورقة مقص", rps, [F("c", "", "sel", [(x, x) for x in ("حجر", "ورقة", "مقص")])]),
    ("org", "📁", "مرتّب ملفات", organize, [F("path", "مسار المجلد"), F("go", "نفّذ فعلياً", "chk")]),
    ("price", "🏷️", "سحب أسعار", prices, [F("url", "رابط الصفحة")]),
    ("ttt", "⭕", "إكس أو", ttt, [F("cell", "الخانة 1-9 (0 = جديدة)", "num")]),
    ("wx", "🌤️", "الطقس", weather, [F("city", "اسم المدينة بالإنجليزي")]),
    ("spend", "💰", "المصاريف", spend, [F("amt", "المبلغ (فارغ = عرض)", "num"), F("cat", "الفئة")]),
    ("short", "🔗", "مختصر روابط", short, [F("url", "الرابط الكامل https://...")]),
    ("quiz", "❓", "أسئلة", quiz, [F("ans", "جوابك (فارغ = سؤال جديد)")]),
    ("pdf", "📄", "قارئ PDF", pdf, [F("file", "", "file"), F("page", "رقم الصفحة", "num")]),
    ("unit", "📏", "محول وحدات", unit, [F("v", "القيمة", "num"), F("k", "", "sel", [(k, k.replace("_", " → ")) for k in UK])]),
    ("bmi", "⚖️", "كتلة الجسم", bmi, [F("kg", "الوزن كغم", "num"), F("cm", "الطول سم", "num")]),
    ("hash", "#️⃣", "تشفير Hash", hs, [F("text", "النص", "area")]),
    ("b64", "🔐", "Base64", b64, [F("m", "", "sel", [("enc", "ترميز"), ("dec", "فك")]), F("text", "النص", "area")]),
    ("age", "🎂", "حاسبة العمر", age, [F("d", "تاريخ الميلاد", "date")]),
    ("dice", "🎲", "نرد / عملة / اختيار", dice, [F("m", "", "sel", [("dice", "نرد"), ("coin", "عملة"), ("pick", "اختيار")]), F("text", "للاختيار: خيار1, خيار2, خيار3")]),
    ("color", "🎨", "ألوان HEX→RGB", color, [F("hex", "مثل #3ddc97")]),
    ("base", "🔟", "تحويل أنظمة عد", base, [F("n", "رقم عشري", "num")]),
    ("json", "🧾", "منسّق JSON", js, [F("text", "JSON", "area")]),
    ("bill", "🍽️", "تقسيم الفاتورة", bill, [F("t", "المجموع", "num"), F("tip", "بقشيش %", "num"), F("n", "عدد الأشخاص", "num")]),
    ("morse", "📡", "مورس", morse, [F("text", "نص إنجليزي/أرقام")]),
    ("caesar", "🕵️", "تشفير قيصر", caesar, [F("k", "الإزاحة (سالب = فك)", "num"), F("text", "النص", "area")]),
    ("freq", "📊", "أكثر الكلمات تكراراً", freq, [F("text", "النص", "area")]),
]

CAT_OF = {i: k for k, ids in {
    "games": "guess rps ttt quiz dice", "daily": "calc todo notes spend rem age bill bmi",
    "info": "cur unit color base wx", "text": "wc freq morse caesar b64 hash json pw",
    "files": "org pdf price short"}.items() for i in ids.split()}
CATS = [("games", "ألعاب", "var(--coral)"), ("daily", "يومي", "var(--lapis)"), ("info", "تحويل ومعلومات", "var(--mint)"),
        ("text", "نصوص وأمان", "var(--saf)"), ("files", "ملفات وويب", "var(--violet)")]

PAGE = r"""<!doctype html><html lang=ar dir=rtl><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name=color-scheme content="light dark">
<title>صندوق الأدوات</title>
<link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;800&display=swap" rel=stylesheet>
<style>
:root{--ink:#14213d;--paper:#f2f4fa;--card:#fff;--line:#dfe4f1;--lapis:#2b4bd8;--saf:#ffb703;--coral:#e4572e;--mint:#16a67a;--violet:#7b4ae2;--mut:#5d6785}
@media(prefers-color-scheme:dark){:root{--ink:#eef1fb;--paper:#0f1424;--card:#192038;--line:#2a3354;--mut:#9aa5c8;--lapis:#5b78f5}}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.5 Tajawal,"Noto Sans Arabic",system-ui,sans-serif;padding:env(safe-area-inset-top) 0 env(safe-area-inset-bottom)}
button,input,select,textarea{font:inherit;color:inherit}button{cursor:pointer}button:disabled{opacity:.5}
.wrap{max-width:560px;margin:auto;padding:20px 16px 40px}
h1{font-size:30px;font-weight:800;margin:8px 0 4px}.sub{color:var(--mut);margin:0 0 16px}
input,select,textarea{width:100%;padding:13px 14px;border:1.5px solid var(--line);border-radius:12px;background:var(--card);outline:none}
input:focus,select:focus,textarea:focus{border-color:var(--lapis)}input[type=range]{padding:0}
.chips{display:flex;gap:8px;overflow-x:auto;padding:12px 0}
.chip{white-space:nowrap;border:1.5px solid var(--line);background:none;border-radius:99px;padding:6px 14px}
.chip.on{background:var(--ink);color:var(--paper);border-color:var(--ink)}
section h2{font-size:17px;margin:22px 0 10px;color:var(--mut);font-weight:500}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.tile{display:flex;align-items:center;gap:10px;padding:12px;border-radius:18px;background:var(--card);border:1.5px solid var(--line);color:inherit;text-decoration:none;font-weight:500}
.ic{width:42px;height:42px;border-radius:13px;display:grid;place-items:center;font-size:22px;background:color-mix(in srgb,var(--k) 18%,var(--card));flex:none}
.bar{display:flex;align-items:center;gap:10px}.bar h1{font-size:24px;margin:0}
.back{width:42px;height:42px;border-radius:13px;display:grid;place-items:center;background:var(--card);border:1.5px solid var(--line);color:inherit;text-decoration:none;font-size:20px}
.body{margin-top:18px;display:grid;gap:12px}
.fld{display:grid;gap:6px}.fld span{color:var(--mut);font-size:14px}.chk{display:flex;align-items:center;gap:10px}.chk input{width:auto}
.primary{background:var(--lapis);color:#fff;border:0;border-radius:14px;padding:14px 18px;font-weight:800}
.ghost{background:none;border:1.5px solid var(--line);border-radius:14px;padding:11px 16px}
.out{background:var(--card);border:1.5px solid var(--line);border-radius:16px;padding:14px}.out.bad{border-color:var(--coral)}
pre{margin:0 0 10px;white-space:pre-wrap;font:inherit;font-size:18px;word-break:break-word}
.addrow{display:flex;gap:8px}.addrow input{flex:1}.stack{flex-direction:column}
.rows{display:grid;gap:8px}.row{display:flex;align-items:center;gap:10px;background:var(--card);border:1.5px solid var(--line);border-radius:14px;padding:10px 12px}
.row span{flex:1}.row.done span{text-decoration:line-through;color:var(--mut)}
.tick{width:26px;height:26px;border-radius:50%;border:2px solid var(--lapis);background:none;color:var(--lapis);font-weight:800;padding:0}.done .tick{background:var(--lapis);color:#fff}
.x{background:none;border:0;color:var(--mut)}.empty{color:var(--mut);text-align:center;margin:20px 0}
.big,.bigres{font-size:44px;font-weight:800;text-align:center;padding:12px 0}.bigres{font-size:26px}
.screen{background:#14213d;color:#eef1fb;border-radius:22px;padding:18px;min-height:130px;display:flex;flex-direction:column;justify-content:flex-end}
.disp{font-size:44px;font-weight:800;text-align:right;overflow-x:auto;white-space:nowrap}.dsub{text-align:right;color:var(--saf);min-height:24px}
.keys{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
.key{height:62px;border-radius:18px;border:0;background:var(--card);font-size:24px;box-shadow:inset 0 0 0 1.5px var(--line)}
.key.op{background:var(--saf);color:#14213d;box-shadow:none}.key.eq{background:var(--lapis);color:#fff;box-shadow:none}.key.clr{color:var(--coral)}
.trio{display:flex;gap:10px}.big-btn{flex:1;font-size:42px;padding:16px 0;border-radius:20px;border:1.5px solid var(--line);background:var(--card);display:grid;gap:2px;justify-items:center}
.big-btn small{font-size:15px;color:var(--mut)}
.vs{display:flex;justify-content:center;align-items:center;gap:18px;font-size:64px}.vs i{font-size:16px;color:var(--mut);font-style:normal}
.verdict{text-align:center;font-weight:800;font-size:20px;white-space:pre-line;min-height:30px}.verdict.win{color:var(--mint)}.verdict.lose{color:var(--coral)}
.board{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
.cell{aspect-ratio:1;border-radius:18px;border:1.5px solid var(--line);background:var(--card);font-size:48px;font-weight:800}.cell.X{color:var(--lapis)}.cell.O{color:var(--coral)}
.qq{font-size:24px;margin:8px 0}.opts{display:grid;gap:10px}.opt{padding:16px;border-radius:16px;border:1.5px solid var(--line);background:var(--card);font-size:18px;text-align:right}
</style>
<div id=app></div>
<script>
const M=__META__,CAT=__CATS__,V={},app=document.getElementById('app');
let q='',cat='';
const h=(t,a={},...c)=>{const e=document.createElement(t);for(const k in a){const v=a[k];if(k=='class')e.className=v;else if(k.startsWith('on'))e.addEventListener(k.slice(2),v);else e.setAttribute(k,v)}c.flat().forEach(x=>{if(x!=null&&x!==false)e.append(x)});return e};
const errMsg=e=>/urlopen|resol|timed out|Errno|HTTP/i.test(e)?'تعذّر الاتصال بالإنترنت. تأكد من الشبكة وحاول مرة ثانية.':'تعذّر التنفيذ: '+e;
async function api(id,o={}){let fd=o;if(!(o instanceof FormData)){fd=new FormData();for(const k in o)fd.append(k,o[k])}
 try{return await(await fetch('/api/'+id,{method:'POST',body:fd})).json()}catch(e){return{err:'urlopen'}}}
const st=async k=>{try{return await(await fetch('/api/state/'+k)).json()}catch(e){return[]}};

function home(){
 const chips=h('div',{class:'chips'}),list=h('div');
 const draw=()=>{
  chips.replaceChildren(...[{k:'',n:'الكل'},...CAT].map(c=>h('button',{class:'chip'+(cat==c.k?' on':''),onclick:()=>{cat=c.k;draw()}},c.n)));
  list.replaceChildren(...CAT.filter(c=>!cat||cat==c.k).map(c=>{const ts=M.filter(t=>t.c==c.k&&t.n.includes(q));
   return ts.length&&h('section',{},h('h2',{},c.n),h('div',{class:'grid'},ts.map(t=>h('a',{class:'tile',href:'#'+t.id,style:'--k:'+c.col},h('span',{class:'ic'},t.e),t.n))))}).filter(Boolean))};
 draw();
 return h('div',{class:'wrap'},h('h1',{},'صندوق الأدوات'),h('p',{class:'sub'},'30 أداة جاهزة. بدون حساب وبدون مفاتيح.'),
  h('input',{placeholder:'ابحث عن أداة',value:q,oninput:e=>{q=e.target.value.trim();draw()}}),chips,list)}

function tool(t){const body=h('div',{class:'body'});(V[t.id]||generic)(t,body);
 return h('div',{class:'wrap'},h('div',{class:'bar'},h('a',{class:'back',href:'#','aria-label':'رجوع'},'→'),h('h1',{},t.e+' '+t.n)),body)}

function generic(t,body){
 const out=h('div',{class:'out',hidden:''}),btn=h('button',{class:'primary'},'نفّذ');
 const fs=t.f.map(([k,l,ty,o])=>{let el;
  if(ty=='sel')el=h('select',{name:k},o.map(([v,n])=>h('option',{value:v},n)));
  else if(ty=='area')el=h('textarea',{name:k,rows:5});
  else if(ty=='chk')return h('label',{class:'chk'},h('input',{type:'checkbox',name:k}),l);
  else if(ty=='range'){const v=h('b',{},o[2]);el=h('input',{type:'range',name:k,min:o[0],max:o[1],value:o[2],oninput:e=>{v.textContent=e.target.value}});return h('label',{class:'fld'},h('span',{},l+': ',v),el)}
  else el=h('input',{name:k,type:{num:'number',date:'date',file:'file'}[ty]||'text',step:'any'});
  return h('label',{class:'fld'},l&&h('span',{},l),el)});
 const form=h('form',{onsubmit:async e=>{e.preventDefault();btn.disabled=true;const r=await api(t.id,new FormData(form));btn.disabled=false;
  out.hidden=false;out.classList.toggle('bad',!!r.err);const txt=r.err?errMsg(r.err):r.out;
  out.replaceChildren(h('pre',{},txt),!r.err&&h('button',{type:'button',class:'ghost',onclick:()=>navigator.clipboard&&navigator.clipboard.writeText(txt)},'انسخ النتيجة'))}},fs,btn);
 body.append(form,out)}

V.calc=(t,b)=>{let ex='';const disp=h('div',{class:'disp',dir:'ltr'},'0'),sub=h('div',{class:'dsub',dir:'ltr'}),upd=()=>{disp.textContent=ex||'0'};
 const OP={'÷':'/','×':'*','−':'-'};
 const eq=async()=>{if(!ex)return;const r=await api('calc',{expr:ex.replace(/[÷×−]/g,c=>OP[c])});if(r.err)sub.textContent='العملية غير صحيحة';else{sub.textContent=ex+' =';ex=String(r.out)}upd()};
 const rows=['C','(',')','÷','7','8','9','×','4','5','6','−','1','2','3','+','⌫','0','.','='];
 b.append(h('div',{class:'screen'},sub,disp),h('div',{class:'keys',dir:'ltr'},rows.map(k=>h('button',{class:'key '+('÷×−+'.includes(k)?'op':k=='='?'eq':k=='C'?'clr':''),
  onclick:k=='C'?()=>{ex='';sub.textContent='';upd()}:k=='⌫'?()=>{ex=ex.slice(0,-1);upd()}:k=='='?eq:()=>{ex+=k;upd()}},k))))};

const L=(ph,empty)=>(t,b)=>{const list=h('div',{class:'rows'}),inp=h('input',{placeholder:ph}),todo=t.id=='todo';
 const load=async()=>{const d=await st(t.id);list.replaceChildren(...(d.length?d.map((x,i)=>{const o=typeof x=='string'?{t:x}:x;
  return h('div',{class:'row'+(o.done?' done':'')},todo&&h('button',{class:'tick','aria-label':'إنجاز',onclick:()=>act('done',i)},o.done?'✓':''),h('span',{},o.t),h('button',{class:'x','aria-label':'حذف',onclick:()=>act('del',i)},'✕'))}):[h('p',{class:'empty'},empty)]))};
 const act=async(a,i)=>{await api(t.id,{act:a,text:i+1});load()};
 const add=async()=>{const v=inp.value.trim();if(!v)return;await api(t.id,{act:'add',text:v});inp.value='';load()};
 inp.addEventListener('keydown',e=>{if(e.key=='Enter')add()});
 b.append(h('div',{class:'addrow'},inp,h('button',{class:'primary',onclick:add},'أضف')),list);load()};
V.todo=L('مهمة جديدة','ما عندك مهام. اكتب أول مهمة بالأعلى.');
V.notes=L('ملاحظة جديدة','الدفتر فاضي. اكتب أول ملاحظة.');

V.spend=(t,b)=>{const amt=h('input',{type:'number',step:'any',placeholder:'المبلغ'}),cat=h('input',{placeholder:'الفئة: أكل، مواصلات...'}),sum=h('div',{class:'rows'});
 const load=async()=>{const d=await st('exp'),tot={};d.forEach(x=>{tot[x.c]=(tot[x.c]||0)+x.a});const all=d.reduce((s,x)=>s+x.a,0);
  sum.replaceChildren(h('div',{class:'big'},all.toLocaleString('en')),...Object.entries(tot).map(([k,v])=>h('div',{class:'row'},h('span',{},k),h('b',{},v.toLocaleString('en')))),!d.length&&h('p',{class:'empty'},'ما سجلت أي مصروف بعد.'))};
 b.append(h('div',{class:'addrow stack'},amt,cat,h('button',{class:'primary',onclick:async()=>{if(!amt.value)return;await api('spend',{amt:amt.value,cat:cat.value});amt.value='';load()}},'سجّل المصروف')),sum);load()};

V.rps=(t,b)=>{const E={'حجر':'✊','ورقة':'✋','مقص':'✌️'},res=h('div',{},h('p',{class:'empty'},'اختر وتحدَّ الكمبيوتر.'));
 b.append(h('div',{class:'trio'},Object.keys(E).map(k=>h('button',{class:'big-btn',onclick:async()=>{const r=(await api('rps',{c:k})).data;
  res.replaceChildren(h('div',{class:'vs'},h('span',{},E[r.u]),h('i',{},'ضد'),h('span',{},E[r.c])),h('div',{class:'verdict '+r.k},r.r))}},E[k],h('small',{},k)))),res)};

V.ttt=(t,b)=>{const msg=h('p',{class:'verdict'}),bd=h('div',{class:'board',dir:'ltr'});
 const draw=d=>{bd.replaceChildren(...d.b.map((c,i)=>h('button',{class:'cell '+c,onclick:()=>play(i+1)},c.trim())));msg.textContent=d.m||'دورك. أنت X.'};
 const play=async n=>draw((await api('ttt',{cell:n})).data);
 b.append(bd,msg,h('button',{class:'ghost',onclick:()=>play(0)},'لعبة جديدة'));play(-1)};

V.dice=(t,b)=>{const r=h('div',{class:'big'},'—'),lst=h('input',{placeholder:'خيار1، خيار2، خيار3'});
 const go=async(m,text='')=>{r.textContent=(await api('dice',{m,text})).out};
 b.append(r,h('div',{class:'trio'},h('button',{class:'big-btn',onclick:()=>go('dice')},'🎲',h('small',{},'نرد')),h('button',{class:'big-btn',onclick:()=>go('coin')},'🪙',h('small',{},'عملة'))),
  h('div',{class:'addrow'},lst,h('button',{class:'primary',onclick:()=>lst.value&&go('pick',lst.value.replace(/،/g,','))},'اختر لي')))};

V.guess=(t,b)=>{const hint=h('div',{class:'bigres'},'خمّن رقم من 1 إلى 100'),n=h('input',{type:'number',placeholder:'رقمك'});
 const go=async v=>{hint.textContent=(await api('guess',{n:v})).out;n.value=''};
 b.append(hint,h('div',{class:'addrow'},n,h('button',{class:'primary',onclick:()=>n.value&&go(n.value)},'خمّن')),h('button',{class:'ghost',onclick:()=>go(0)},'لعبة جديدة'))};

V.quiz=(t,b)=>{const qq=h('h2',{class:'qq'}),opts=h('div',{class:'opts'}),m=h('p',{class:'verdict'});
 const next=async a=>{const d=(await api('quiz',{ans:a||''})).data;m.textContent=d.m?d.m+'\nنقاطك: '+d.s:'';qq.textContent=d.q;opts.replaceChildren(...d.o.map(o=>h('button',{class:'opt',onclick:()=>next(o)},o)))};
 b.append(m,qq,opts);next()};

function route(){const t=M.find(x=>x.id==location.hash.slice(1));scrollTo(0,0);app.replaceChildren(t?tool(t):home())}
addEventListener('hashchange',route);route();
</script>"""

HTML = PAGE.replace("__META__", json.dumps([{"id": i, "e": e, "n": n, "f": f, "c": CAT_OF[i]} for i, e, n, _, f in T], ensure_ascii=False)) \
           .replace("__CATS__", json.dumps([{"k": k, "n": n, "col": c} for k, n, c in CATS], ensure_ascii=False))


@app.route("/")
def home():
    return HTML


@app.route("/api/<i>", methods=["POST"])
def api(i):
    t = next(x for x in T if x[0] == i)
    try:
        o = t[3](request.form.to_dict())
        return jsonify(data=o) if isinstance(o, (dict, list)) else jsonify(out=str(o))
    except Exception as e:
        return jsonify(err=str(e))


@app.route("/api/state/<k>")
def state(k):
    return jsonify(load().get(k, []))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
