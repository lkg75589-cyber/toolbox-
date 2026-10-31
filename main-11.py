"""🧰 صندوق الأدوات: 30 أداة في مشروع Flask واحد (بدون مفاتيح API وبدون ذكاء اصطناعي)
تشغيل:  pip install flask pypdf   ثم   python app.py   ثم افتح  http://127.0.0.1:5000
"""
import ast, operator as op, random, string, json, re, hashlib, base64, shutil, secrets, os
import urllib.request, urllib.parse
from datetime import date, datetime
from collections import Counter
from flask import Flask, request, render_template_string, redirect

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
    return ev(ast.parse(f["expr"], mode="eval").body)


def todo(f):
    d, t = lst("todo")
    a, x = f["act"], f["text"]
    if a == "add" and x:
        t.append({"t": x, "done": False})
    elif a == "done":
        t[int(x) - 1]["done"] = True
    elif a == "del":
        t.pop(int(x) - 1)
    save(d)
    return "\n".join(f"{i}. [{'x' if k['done'] else ' '}] {k['t']}" for i, k in enumerate(t, 1)) or "القائمة فارغة"


def guess(f):
    d = load()
    n = int(f["n"])
    if n == 0 or "secret" not in d:
        d["secret"], d["tries"] = random.randint(1, 100), 0
        save(d)
        return "لعبة جديدة! خمّن رقم من 1 إلى 100"
    d["tries"] += 1
    s = d["secret"]
    if n == s:
        msg = f"صح! بعد {d['tries']} محاولة 🎉"
        d.pop("secret")
    else:
        msg = "أكبر ⬆️" if n < s else "أصغر ⬇️"
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
    return f"أنت: {m[u]} | الكمبيوتر: {m[c]}\n" + ("تعادل" if u == c else "فزت 🎉" if (u - c) % 3 == 1 else "خسرت 😅")


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
    if n == 0 or win(b) or " " not in b:
        b = [" "] * 9
    elif b[n - 1] != " ":
        msg = "الخانة مشغولة\n"
    else:
        b[n - 1] = "X"
        if not win(b) and " " in b:
            b[random.choice([i for i, x in enumerate(b) if x == " "])] = "O"
        w = win(b)
        msg = "فزت 🎉\n" if w == "X" else "فاز الكمبيوتر 😅\n" if w == "O" else "تعادل\n" if " " not in b else ""
    d["ttt"] = b
    save(d)
    return msg + "\n---------\n".join(" | ".join(b[i:i + 3]) for i in (0, 3, 6))


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


Q = [("عاصمة العراق؟", "بغداد"), ("2+2×2 = ؟", "6"), ("أكبر كوكب؟", "المشتري"),
     ("لغة برمجة اسمها أفعى بالإنجليزي؟", "بايثون"), ("كم يوم بالأسبوع؟", "7"), ("عاصمة اليابان؟", "طوكيو")]


def quiz(f):
    d, m = load(), ""
    if f["ans"] and "q" in d:
        ok = f["ans"].strip() == Q[d["q"]][1]
        d["s"] = d.get("s", 0) + ok
        m = ("✅ صح" if ok else f"❌ الجواب: {Q[d['q']][1]}") + f"\nنقاطك: {d['s']}\n\n"
    d["q"] = random.randrange(len(Q))
    save(d)
    return m + "السؤال: " + Q[d["q"]][0]


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
    ("pw", "🔑", "مولد باسوردات", pw, [F("len", "الطول", "num"), F("sym", "إضافة رموز", "chk")]),
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

PAGE = """<!doctype html><html lang=ar dir=rtl><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>صندوق الأدوات</title>
<style>
body{font-family:system-ui;margin:0;background:#101418;color:#eee}a{color:inherit;text-decoration:none}
header{padding:16px;background:#1b2229;font-weight:bold}
.g{display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:10px;padding:12px}
.c{background:#1b2229;border-radius:12px;padding:16px;text-align:center}
main{padding:12px;max-width:600px;margin:auto}
input,select,textarea,button{width:100%;padding:12px;margin:6px 0;border-radius:8px;border:0;font:inherit;box-sizing:border-box}
button{background:#3ddc97;color:#000;font-weight:bold}
pre{background:#1b2229;padding:12px;border-radius:8px;white-space:pre-wrap}
</style>
<header><a href="/">🧰 صندوق الأدوات ({{T|length}})</a></header>
{% if t %}<main><h2>{{t[1]}} {{t[2]}}</h2>
<form method=post enctype=multipart/form-data>
{% for k,l,ty,o in t[4] %}
{% if ty=="sel" %}<select name={{k}}>{% for v,n in o %}<option value="{{v}}" {{"selected" if v==vals.get(k)}}>{{n}}</option>{% endfor %}</select>
{% elif ty=="area" %}<textarea name={{k}} rows=5 placeholder="{{l}}">{{vals.get(k,"")}}</textarea>
{% elif ty=="chk" %}<label><input type=checkbox name={{k}} style="width:auto"> {{l}}</label>
{% else %}<input name={{k}} type="{{ {'num':'number','date':'date','file':'file'}.get(ty,'text') }}" placeholder="{{l}}" value="{{vals.get(k,'')}}" {{"step=any" if ty=="num"}}>
{% endif %}{% endfor %}
<button>تنفيذ</button></form>
{% if out is not none %}<pre>{{out}}</pre>{% endif %}</main>
{% else %}<div class=g>{% for x in T %}<a class=c href="/t/{{x[0]}}"><div style="font-size:30px">{{x[1]}}</div>{{x[2]}}</a>{% endfor %}</div>{% endif %}
"""


@app.route("/")
def home():
    return render_template_string(PAGE, T=T, t=None, vals={}, out=None)


@app.route("/t/<i>", methods=["GET", "POST"])
def tool(i):
    t = next(x for x in T if x[0] == i)
    v, out = request.form.to_dict(), None
    if request.method == "POST":
        try:
            out = str(t[3](v))
        except Exception as e:
            out = f"⚠️ خطأ: {e}"
    return render_template_string(PAGE, T=T, t=t, vals=v, out=out)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
