// الطلبات تنفذها HTMX؛ هذا التنبيه يظهر فقط إذا انقطع اتصال الموقع.
document.body.addEventListener('htmx:beforeRequest', function (event) {
  const error = event.target.querySelector('.connection-error');
  if (error) error.hidden = true;
});
document.body.addEventListener('htmx:afterRequest', function (event) {
  const error = event.target.querySelector('.connection-error');
  if (error) error.hidden = event.detail.successful;
});
