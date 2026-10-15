from flask import Flask, render_template, request
import requests
import base64

# إنشاء كائن الموقع من Flask، مثل إنشاء كائن من كلاس في Java.
# الصفحات في المجلد الحالي، والتنسيق والصور في assets.
app = Flask(__name__, template_folder=".", static_folder="assets")

# روابط الخدمات ومفتاح البحث.
API_URL = "https://baseerah.duckdns.org/webhook/parts-search"
API_KEY = "X9p#vL2$mPq7!kR4"
CHAT_API_URL = "https://parts-api-fragrant-glitter-6532.fly.dev/extract"
ANALYSIS_API_URL = ""  # رابط نموذج الضرر؛ صيغة JSON المقترحة موضحة في README.

# بيانات ثابتة: لكل شركة أسماء طرازاتها بالإنجليزية والعربية.
cars = {
    "Toyota": {"Camry": "كامري", "Corolla": "كورولا", "Yaris": "يارس"},
    "Hyundai": {"Elantra": "إلنترا", "Sonata": "سوناتا", "Accent": "أكسنت"},
    "Kia": {"Pegas": "بيجاس", "Sportage": "سبورتاج", "K5": "كي 5"},
    "Nissan": {"Sunny": "صني", "Patrol": "باترول", "X-Trail": "إكس تريل"},
    "Ford": {"Taurus": "توروس", "Territory": "تيريتوري", "Explorer": "إكسبلورر"},
    "GMC": {"Yukon": "يوكن", "Sierra": "سييرا", "Acadia": "أكاديا"}
}

# فتح الصفحات: كل رابط له دالة تفتح ملف HTML واضحًا.
@app.route("/")
@app.route("/index.html")
def home():
    return render_template("index.html", analysis_ready=bool(ANALYSIS_API_URL))


@app.route("/parts.html")
def parts():
    return render_template("parts.html")


@app.route("/about.html")
def about():
    return render_template("about.html")


# قراءة اسم الشركة، ثم إرسال طرازاتها إلى القائمة في الصفحة.
@app.get("/models")
def show_models():
    make = request.args.get("make", "")
    models = cars.get(make, {})
    return render_template("models.html", models=models)


# تجهيز رابط الصورة أو المنتج؛ بعض الردود تأتي بصيغة [اسم](رابط).
def web_link(link):
    if link is None:
        return ""

    link = str(link).strip()

    if link.startswith("[") and "](" in link:
        # نأخذ الرابط الذي يأتي بعد ](، ثم نزيل النص الزائد والقوس الأخير.
        link = link.split("](", 1)[1].split(" ", 1)[0].rstrip(")")

    if link.startswith("https://") or link.startswith("http://"):
        return link
    return ""


# البحث: نقرأ الحقول، نرسلها للخدمة، ثم نعرض الرد.
@app.post("/search/products")
@app.post("/search/all")
def search():
    # الأسماء بين علامتي التنصيص هي أسماء الحقول المطلوبة من الخدمة.
    data = {
        "make": request.form.get("make", ""),
        "model": request.form.get("model", ""),
        "year": request.form.get("year", ""),
        "vin": request.form.get("vin", ""),
        "partName": request.form.get("partName", ""),
        "partType": request.form.get("partType", "any")
    }
    stores = []

    # try يشغّل الخطوات؛ except يعرض رسالة إذا حدث خطأ.
    try:
        make = data["make"]
        model = data["model"]
        models = cars.get(make, {})

        if model not in models:
            result = {"message": "اختر الشركة والطراز من القائمة أولًا."}
        else:
            data["year"] = int(data["year"])  # تحويل السنة من نص إلى عدد.
            if request.path == "/search/all":
                # القطع المحددة + القطع المكتوبة؛ نحذف الفراغ والتكرار.
                names = request.form.getlist("detected") + data["partName"].splitlines()
                parts = []
                for name in names:
                    name = name.strip()
                    if name and name not in parts:
                        parts.append(name)
                if not parts:
                    result = {"message": "حدد قطعة من التحليل أو اكتب قطعة للبحث عنها."}
                else:
                    # المكتبة تبحث عن كل قطعة وتعرض ردها بمجرد وصوله.
                    return render_template("all-results.html", parts=parts, data=data)
                return render_template("results.html", result=result)

            headers = {"x-api-key": API_KEY}

            # إرسال البيانات؛ مهلة الانتظار 90 ثانية.
            response = requests.post(API_URL, json=data, headers=headers, timeout=90)
            response.raise_for_status()  # ينتقل إلى except إذا رفضت الخدمة الطلب.
            result = response.json()  # تحويل الرد إلى بيانات يمكن قراءتها.

            # معرفة المتاجر الموجودة حتى يعمل فلتر eBay وAliExpress.
            for product in result.get("items") or []:
                stores.append(product.get("source"))

    except Exception:
        result = {"message": "تعذّر البحث الآن. تأكد من البيانات وجرّب مرة أخرى."}

    return render_template("results.html", result=result, stores=stores, web_link=web_link,
                           group=request.form.get("group", "single"))


# الصورة تصبح نص Base64 حتى نرسلها داخل JSON. لا نخزن الصور في الموقع.
@app.post("/analyze")
def analyze():
    photo = request.files.get("image")
    result = {"success": False, "message": "خدمة تحليل الصور لم تُربط بعد. يمكنك إضافة القطع يدويًا."}
    if ANALYSIS_API_URL:
        if not photo or photo.mimetype not in ["image/jpeg", "image/png", "image/webp"]:
            result["message"] = "اختر صورة JPG أو PNG أو WebP."
        else:
            try:
                image = photo.read(5 * 1024 * 1024 + 1)
                if not image or len(image) > 5 * 1024 * 1024:
                    result["message"] = "اختر صورة غير فارغة وحجمها لا يتجاوز 5 MB."
                else:
                    image = base64.b64encode(image).decode("utf-8")
                    data = {"image": "data:" + photo.mimetype + ";base64," + image}
                    response = requests.post(ANALYSIS_API_URL, json=data, timeout=90)
                    response.raise_for_status()
                    result = response.json()
                    if result.get("success"):
                        # نتحقق من القائمة قبل عرضها؛ لا نخمن قطعًا من عندنا.
                        if not isinstance(result.get("damages"), list):
                            raise ValueError("damages must be a list")
                        for damage in result["damages"]:
                            if not isinstance(damage.get("partName"), str) or not damage["partName"].strip():
                                raise ValueError("partName is missing")
            except requests.Timeout:
                result = {"message": "التحليل تأخر. جرّب مرة ثانية، أو أضف القطع يدويًا."}
            except Exception:
                result = {"message": "تعذّر التحليل أو جاءت البيانات بصيغة مختلفة. راجع مسؤول نموذج الضرر."}
    return render_template("analysis.html", analysis=result, web_link=web_link)


# المحادثة: نرسل النص فقط. الخدمة الخارجية مسؤولة عن فهمه.
@app.post("/search/chat")
def chat():
    message = request.form.get("message", "")
    message = message.strip()
    reply = "اكتب رسالتك أولًا."
    result = None  # لا توجد منتجات قبل وصول رد الخدمة.

    if message != "":
        try:
            data = {"message": message}
            response = requests.post(CHAT_API_URL, json=data, timeout=90)
            response.raise_for_status()
            answer = response.json()

            # قد يأتي النص باسم reply أو message حسب رد الخدمة.
            reply = answer.get("reply")
            if not reply:
                reply = answer.get("message")
            result = answer.get("result_from_backend")

            if not reply and not result:
                reply = "وصل رد من الخدمة بدون نص أو نتائج قابلة للعرض. أرسل هذه الملاحظة لمسؤول الشات."

        except requests.Timeout:
            reply = "خدمة الشات تأخرت في الرد. حاول مرة ثانية."
        except Exception:
            reply = "تعذّر الاتصال بخدمة الشات أو حدث خطأ فيها. جرّب لاحقًا، وإذا تكرر الخطأ راجع مسؤول الشات."

    return render_template("results.html", reply=reply, result=result, web_link=web_link, in_chat=True)


# تشغيل الموقع عندما نشغّل هذا الملف مباشرة.
if __name__ == "__main__":
    app.run(port=8000)
