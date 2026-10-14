from flask import Flask, render_template, request
import requests
from cars import cars

app = Flask(__name__, template_folder=".", static_folder="assets")
API_URL = "https://baseerah.duckdns.org/webhook/parts-search"
API_KEY = "X9p#vL2$mPq7!kR4"

# قبول رابط عادي أو رابط منسوخ بصيغة Markdown.
def web_link(link):
    link = str(link or "").strip()
    if link.startswith("[") and "](" in link:
        link = link.split("](", 1)[1].split(" ", 1)[0].rstrip(")")
    if link.startswith("https://") or link.startswith("http://"):
        return link
    return ""

# فتح صفحات الموقع.
@app.route("/")
@app.route("/<page>.html")
def show_page(page="index"):
    if page not in ["index", "parts", "about"]:
        return "الصفحة غير موجودة", 404
    return render_template(page + ".html")

# طرازات الشركة المختارة؛ HTMX يضعها في قائمة الطراز.
@app.get("/models")
def show_models():
    return render_template("models.html", models=cars.get(request.args.get("make"), {}))

# استقبال نموذج البحث، ثم إعادة البطاقات إلى مكانها في الصفحة.
@app.post("/search/products")
def search():
    try:
        data = request.form.to_dict()
        data.pop("condition", None)
        if data.get("model") not in cars.get(data.get("make"), {}):
            return render_template("products.html", result={"message": "اختر الشركة والطراز من القائمة أولًا."})
        headers = {"x-api-key": API_KEY.strip()}
        data["year"] = int(data["year"])
        response = requests.post(API_URL, json=data, headers=headers, timeout=90)
        response.raise_for_status()
        result = response.json()
        stores = []
        for item in result.get("items") or []:
            stores.append(item.get("source"))
        return render_template("products.html", result=result, stores=stores, web_link=web_link)
    except Exception:
        return render_template("products.html", result={"message": "تعذّر البحث الآن. تأكد من البيانات وجرّب مرة أخرى."})

if __name__ == "__main__":
    app.run(port=8000)
