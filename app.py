from flask import Flask, render_template, request, send_from_directory
import requests

# تشغيل Flask: صفحات HTML هنا، والصور والخطوط داخل assets.
app = Flask(__name__, template_folder=".", static_folder="assets")

# رابط البحث الحالي. إذا كانت Authentication = None اترك المفتاح فارغًا.
API_URL = "https://baseerah.duckdns.org/webhook/parts-search"
API_KEY = "X9p#vL2$mPq7!kR4"


# كتابة السعر بجانب العملة. الصفر سعر صحيح، مثل الشحن المجاني.
def format_price(price):
    if not isinstance(price, dict) or price.get("value") is None or not price.get("currency"):
        return "غير متاح"
    return str(price["value"]) + " " + str(price["currency"])


# السماح بروابط الويب فقط عند عرض صور وروابط المنتجات.
def is_web_link(url):
    if not isinstance(url, str):
        return False
    return url.startswith("https://") or url.startswith("http://")


# إرسال ملف التنسيق للمتصفح.
@app.route("/style.css")
def show_css():
    return send_from_directory(app.root_path, "style.css")


# GET يفتح الصفحة، و POST يرسل بيانات نموذج البحث.
@app.route("/")
@app.route("/<page>.html", methods=["GET", "POST"])
def show_page(page="index"):
    if page not in ("index", "parts", "report", "about"):
        return "الصفحة غير موجودة", 404

    items = []
    message = "أدخل بيانات السيارة واسم القطعة، ثم اضغط ابحث وقارن."

    # أسماء الحقول تبقى كما هي لأن خدمة n8n تستقبلها بهذه الأسماء.
    if request.method == "POST" and page == "parts":
        data = request.form.to_dict()
        try:
            data["year"] = int(data.get("year", ""))
        except ValueError:
            message = "أدخل سنة الصنع كرقم صحيح."
        else:
            # لا نرسل مفتاحًا وهميًا أو فارغًا إلى الخدمة.
            headers = {}
            if API_KEY.strip():
                headers["x-api-key"] = API_KEY.strip()
            try:
                response = requests.post(
                    API_URL, json=data, headers=headers, timeout=60
                )
                response.raise_for_status()
                result = response.json()
                # الرد المطلوب كائن يحتوي success وقائمة items.
                if not isinstance(result, dict):
                    message = "صيغة رد خدمة البحث غير صحيحة؛ راجع رد Webhook في n8n."
                elif result.get("success"):
                    products = result.get("items", [])
                    if isinstance(products, list) and all(isinstance(item, dict) for item in products):
                        items = products
                        message = "ما لقينا نتائج مناسبة."
                    else:
                        message = "قائمة المنتجات في رد الخدمة غير صحيحة؛ يجب أن تكون items قائمة."
                else:
                    message = result.get("message") or "خدمة البحث لم ترجع نتائج؛ راجع تنفيذ n8n."
            except UnicodeEncodeError:
                message = "قيمة API_KEY غير صحيحة. ضع المفتاح الفعلي أو اتركها فارغة إذا كانت المصادقة None."
            except requests.Timeout:
                message = "خدمة البحث تأخرت في الرد. انتظر قليلًا ثم جرّب مرة أخرى."
            except requests.HTTPError:
                message = "خدمة البحث أعادت خطأ HTTP " + str(response.status_code) + ". راجع الرابط والمصادقة وتنفيذ n8n."
            except requests.exceptions.JSONDecodeError:
                message = "خدمة البحث لم ترجع JSON صالحًا؛ راجع رد Webhook في n8n."
            except requests.RequestException:
                message = "تعذّر الاتصال بخدمة البحث. تحقق من الرابط والمفتاح."

    # وضع النتائج والرسالة داخل HTML قبل إرساله للمتصفح.
    return render_template(
        page + ".html", items=items, message=message,
        format_price=format_price, is_web_link=is_web_link
    )


# عنوان الموقع بعد التشغيل: http://127.0.0.1:8000
if __name__ == "__main__":
    app.run(port=8000)
