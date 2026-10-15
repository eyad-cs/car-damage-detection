// عناصر المحادثة التي نستخدمها أكثر من مرة.
const form = document.getElementById('chat-form');
const input = document.getElementById('chat-message');
const messages = document.getElementById('chat-messages');

// إضافة رسالة نصية وتحريك المحادثة إلى آخر رسالة.
function addMessage(text, sender) {
  const message = document.createElement('p');
  message.className = 'chat-message ' + sender;
  message.dir = 'auto';
  message.textContent = text;
  messages.appendChild(message);
  messages.scrollTop = messages.scrollHeight;
}

// HTMX يرسل الطلب؛ هنا نظهر رسالة المستخدم ونفرغ الحقل فقط.
form.addEventListener('htmx:beforeRequest', function () {
  addMessage(input.value, 'chat-user');
  input.value = '';
});

// إظهار تنبيه إذا فشل اتصال الصفحة بالخادم.
form.addEventListener('htmx:afterRequest', function (event) {
  if (!event.detail.successful) {
    addMessage('تعذّر إرسال الرسالة. تأكد من اتصالك وحاول مرة ثانية.', 'chat-assistant');
  }
});
