// Reusable infrastructure for a complete web flow. This does not delete accounts.
// Provision the site key in Non-interactive mode in Cloudflare's dashboard.
export function mountOtpRequest({ form, phoneInput, submitButton, status, container,
  siteKey, apiBaseUrl, onSent, turnstile = window.turnstile, fetchImpl = fetch }) {
  if (!siteKey || !turnstile || typeof onSent !== 'function') {
    submitButton.disabled = true;
    status.textContent = 'Verification is unavailable. Please contact grievance@perifury.com.';
    return () => {};
  }
  const base = new URL(apiBaseUrl);
  if (base.protocol !== 'https:' && !(base.protocol === 'http:' && ['localhost', '127.0.0.1'].includes(base.hostname))) {
    throw new Error('OTP API must use HTTPS');
  }
  let token = '';
  let busy = false;
  let disposed = false;
  let controller;
  status.setAttribute('role', 'status');
  status.setAttribute('aria-live', 'polite');
  submitButton.disabled = true;
  status.textContent = 'Verifying your browser…';
  const invalidate = message => {
    token = '';
    submitButton.disabled = true;
    if (!busy && !disposed) status.textContent = message;
  };
  const widget = turnstile.render(container, {
    sitekey: siteKey,
    action: 'otp_request',
    size: 'flexible',
    callback: value => {
      if (disposed) return;
      token = value;
      submitButton.disabled = busy;
      if (!busy) status.textContent = 'Browser verified. You can request your OTP.';
    },
    'expired-callback': () => invalidate('Verification expired. Please retry verification.'),
    'error-callback': () => { invalidate('Verification failed. Please retry or contact grievance@perifury.com.'); return true; },
    'timeout-callback': () => invalidate('Verification timed out. Please retry verification.')
  });
  const submit = async event => {
    event.preventDefault();
    if (disposed || busy || !token || !form.reportValidity()) return;
    busy = true;
    submitButton.disabled = true;
    status.textContent = 'Requesting your OTP…';
    const responseToken = token;
    token = ''; // Single use, including failures and uncertain network responses.
    controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);
    try {
      const response = await fetchImpl(new URL('/auth/otp/web/request', base).href, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'omit',
        body: JSON.stringify({ phone: phoneInput.value.trim(), turnstileToken: responseToken }),
        signal: controller.signal
      });
      if (disposed) return;
      if (!response.ok) {
        status.textContent = response.status === 429
          ? 'Too many requests. Please wait before trying again.'
          : 'Unable to request an OTP. Please retry or contact grievance@perifury.com.';
        return;
      }
      const result = await response.json();
      if (result.success !== true) throw new Error('Invalid response');
      status.textContent = 'OTP requested. Check your phone.';
      onSent();
    } catch {
      if (!disposed) status.textContent = 'We could not confirm delivery. Please wait before retrying or contact grievance@perifury.com.';
    } finally {
      clearTimeout(timeout);
      busy = false;
      if (!disposed) {
        submitButton.disabled = true;
        turnstile.reset(widget);
      }
    }
  };
  const retry = () => { if (!busy && !disposed) { invalidate('Verifying your browser…'); turnstile.reset(widget); } };
  form.addEventListener('submit', submit);
  form.addEventListener('retryverification', retry);
  return () => {
    disposed = true;
    controller?.abort();
    form.removeEventListener('submit', submit);
    form.removeEventListener('retryverification', retry);
    turnstile.remove(widget);
  };
}
