import test from 'node:test';
import assert from 'node:assert/strict';
import { mountOtpRequest } from '../assets/otp-request.mjs';
function fixture(fetchImpl = async () => ({ ok: true, json: async () => ({ success: true }) })) {
  let callbacks;
  let submit;
  let resets = 0;
  let sent = 0;
  const requests = [];
  const form = { reportValidity: () => true, addEventListener: (name, fn) => { if (name === 'submit') submit = fn; }, removeEventListener() {} };
  const button = {};
  const status = { setAttribute() {} };
  const cleanup = mountOtpRequest({ form, phoneInput: { value: '9876543210' }, submitButton: button, status, container: {}, siteKey: 'public-key', apiBaseUrl: 'https://api.triku.in', onSent: () => sent++, turnstile: {
    render: (_, config) => { callbacks = config; return 'widget'; }, reset: () => resets++, remove() {}
  }, fetchImpl: (...args) => { requests.push(args); return fetchImpl(...args); } });
  return { button, status, requests, callbacks, cleanup, submit: () => submit({ preventDefault() {} }), get resets() { return resets; }, get sent() { return sent; } };
}
test('no SMS request before verification; token submitted only to protected endpoint', async () => {
  const f = fixture();
  await f.submit(); assert.equal(f.requests.length, 0);
  f.callbacks.callback('fresh-token'); await f.submit();
  assert.equal(f.requests[0][0], 'https://api.triku.in/auth/otp/web/request');
  assert.deepEqual(JSON.parse(f.requests[0][1].body), { phone: '9876543210', turnstileToken: 'fresh-token' });
  assert.equal(f.sent, 1); assert.equal(f.resets, 1);
  await f.submit(); assert.equal(f.requests.length, 1);
});
test('expired or failed verification disables submission', async () => {
  const f = fixture();
  for (const name of ['expired-callback', 'error-callback', 'timeout-callback']) {
    f.callbacks.callback('token'); f.callbacks[name](); await f.submit();
    assert.equal(f.button.disabled, true);
  }
  assert.equal(f.requests.length, 0);
});
test('duplicate clicks cannot dispatch two sends', async () => {
  let complete;
  const f = fixture(() => new Promise(resolve => { complete = resolve; }));
  f.callbacks.callback('token'); const first = f.submit(); await f.submit();
  assert.equal(f.requests.length, 1);
  complete({ ok: true, json: async () => ({ success: true }) }); await first;
});
test('network error and rate limit never fall back or automatically resend', async () => {
  for (const response of [() => Promise.reject(new Error('offline')), async () => ({ ok: false, status: 429 })]) {
    const f = fixture(response); f.callbacks.callback('token'); await f.submit();
    assert.equal(f.requests.length, 1); assert.equal(f.sent, 0); assert.equal(f.resets, 1); assert.equal(f.button.disabled, true);
  }
});
test('unconfigured widget fails closed', () => {
  const button = {}; const status = {};
  mountOtpRequest({ siteKey: '', turnstile: {}, submitButton: button, status });
  assert.equal(button.disabled, true); assert.match(status.textContent, /unavailable/);
});
