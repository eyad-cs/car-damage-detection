from flask import Flask, render_template, request
import requests
import base64

# إنشاء كائن الموقع من كلاس Flask (مثل new Flask في جافا)
# الصفحات في المجلد الحالي (.)، والملفات الثابتة كالتنسيق والصور في مجلد assets
app = Flask(__name__, template_folder=".", static_folder="assets")

# ثوابت بروابط الخدمات ومفتاح البحث (مثل String في جافا)
API_URL = "https://baseerah.duckdns.org/webhook/parts-search"
API_KEY = "X9p#vL2$mPq7!kR4"
CHAT_API_URL = "https://dilute-uncheck-eastward.ngrok-free.dev/extract"
ANALYSIS_API_URL = ""  # فارغ حاليًا حتى يرسل زميلك رابط خدمة تحليل الصور

# قاموس السيارات (يشبه HashMap في جافا): كل شركة بداخلها طرازاتها بالإنجليزية والعربية
cars = {
    "Toyota": {"Camry": "كامري", "Corolla": "كورولا", "Yaris": "يارس"},
    "Hyundai": {"Elantra": "إلنترا", "Sonata": "سوناتا", "Accent": "أكسنت"},
    "Kia": {"Pegas": "بيجاس", "Sportage": "سبورتاج", "K5": "كي 5"},
    "Nissan": {"Sunny": "صني", "Patrol": "باترول", "X-Trail": "إكس تريل"},
    "Ford": {"Taurus": "توروس", "Territory": "تيريتوري", "Explorer": "إكسبلورر"},
    "GMC": {"Yukon": "يوكن", "Sierra": "سييرا", "Acadia": "أكاديا"}
}


# 1. دوال فتح الصفحات الرئيسية الثلاث
@app.route("/")
@app.route("/index.html")
def home():
    # نتحقق هل رابط التحليل موجود أم فارغ لتفعيل أو تعطيل زر التحليل في index.html
    ready = (ANALYSIS_API_URL != "")
    return render_template("index.html", analysis_ready=ready)


@app.route("/parts.html")
def parts():
    return render_template("parts.html")


@app.route("/about.html")
def about():
    return render_template("about.html")


# 2. دالة إرسال طرازات الشركة المختارة إلى قائمة الطرازات في index.html و parts.html
@app.get("/models")
def show_models():
    make = request.args.get("make", "")
    models = cars.get(make, {})
    return render_template("models.html", models=models)


# 3. دالة إضافة خانة قطعة جديدة عند الضغط على «+ إضافة قطعة» في index.html
@app.get("/extra-part")
def extra_part():
    return '<div class="field"><label>اسم القطعة<input name="partName" placeholder="مثل: صدام أمامي" autofocus></label></div>'


# 4. دالة مساعدة لتنظيف الرابط إذا أرسلته الخدمة بصيغة [نص](رابط)
def web_link(link):
    if not link:
        return ""
    link = str(link).strip()
    if link.startswith("[") and "](" in link:
        link = link.split("](")[1].split(" ")[0].rstrip(")")
    if link.startswith("http"):
        return link
    return ""


# 5. دالة البحث عن القطع (تخدم البحث الفردي في parts.html والبحث الجماعي في index.html)
@app.post("/search/products")
@app.post("/search/all")
def search():
    # قراءة بيانات السيارة والقطعة التي أرسلها المستخدم من النموذج
    data = {
        "make": request.form.get("make", ""),
        "model": request.form.get("model", ""),
        "year": request.form.get("year", ""),
        "vin": request.form.get("vin", ""),
        "partName": request.form.get("partName", ""),
        "partType": request.form.get("partType", "any")
    }
    stores = []

    try:
        # التأكد أن الشركة والطراز صحيحان من القائمة
        models = cars.get(data["make"], {})
        if data["model"] not in models:
            return render_template("results.html", result={"message": "اختر الشركة والطراز من القائمة أولًا."})

        # تحويل السنة من نص إلى رقم صحيح (مثل Integer.parseInt في جافا)
        data["year"] = int(data["year"])

        # إذا ضغط المستخدم «البحث عن كل القطع» في صفحة الفحص
        if request.path == "/search/all":
            names = request.form.getlist("detected") + request.form.getlist("partName")
            parts = []
            for name in names:
                name = name.strip()
                if name != "" and name not in parts:
                    parts.append(name)

            if len(parts) == 0:
                return render_template("results.html", result={"message": "حدد قطعة من التحليل أو اكتب قطعة للبحث عنها."})

            return render_template("all-results.html", parts=parts, data=data)

        # إرسال طلب البحث عن قطعة واحدة إلى خدمة n8n
        headers = {"x-api-key": API_KEY}
        response = requests.post(API_URL, json=data, headers=headers, timeout=90)
        response.raise_for_status()
        result = response.json()

        # جمع أسماء المتاجر الموجودة في النتائج لتشغيل فلتر (eBay / AliExpress)
        if result.get("items"):
            for product in result["items"]:
                stores.append(product.get("source"))

    except Exception:
        result = {"message": "تعذّر البحث الآن. تأكد من البيانات وجرّب مرة أخرى."}

    group = request.form.get("group", "single")
    return render_template("results.html", result=result, stores=stores, web_link=web_link, group=group)


# 6. دالة إرسال صورة السيارة إلى نموذج تحليل الضرر وعرض النتيجة في index.html
@app.post("/analyze")
def analyze():
    result = {"message": "خدمة تحليل الصور لم تُربط بعد. يمكنك إضافة القطع يدويًا."}

    if ANALYSIS_API_URL != "":
        try:
            photo = request.files.get("image")
            image_bytes = photo.read()

            if len(image_bytes) == 0 or len(image_bytes) > 5000000:
                result = {"message": "اختر صورة غير فارغة وحجمها لا يتجاوز 5 MB."}
            else:
                image_text = base64.b64encode(image_bytes).decode("utf-8")
                data = {"image": "data:" + photo.mimetype + ";base64," + image_text}
                response = requests.post(ANALYSIS_API_URL, json=data, timeout=90)
                response.raise_for_status()
                result = response.json()
        except Exception:
            result = {"message": "تعذّر تحليل الصورة. حاول مرة ثانية أو راجع مسؤول النموذج."}

    return render_template("analysis.html", analysis=result, web_link=web_link)


# 7. دالة المحادثة: ترسل رسالة المستخدم إلى خدمة الشات وتعرض الرد في نافذة المساعد
@app.post("/search/chat")
def chat():
    message = request.form.get("message", "").strip()
    reply = "اكتب رسالتك أولًا."
    result = None

    if message != "":
        try:
            data = {"message": message}
            response = requests.post(CHAT_API_URL, json=data, timeout=90)
            response.raise_for_status()
            answer = response.json()

            reply = answer.get("reply")
            if not reply:
                reply = answer.get("message")
            result = answer.get("result_from_backend")

            if not reply and not result:
                reply = "وصل رد من الخدمة بدون نص أو نتائج قابلة للعرض."
        except Exception:
            reply = "تعذّر الاتصال بخدمة الشات. حاول مرة ثانية."

    return render_template("results.html", reply=reply, result=result, web_link=web_link, in_chat=True)


# 8. تشغيل الموقع على المنفذ 8000 (مثل دالة main في جافا)
if __name__ == "__main__":
    app.run(port=8000)
