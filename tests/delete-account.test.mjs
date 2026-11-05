import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { runInNewContext } from 'node:vm';
const source = await readFile(new URL('../delete-account/delete-account.js', import.meta.url), 'utf8');
function setup() {
  const elements = new Map();
  const get = selector => {
    if (!elements.has(selector)) elements.set(selector, { value: '', hidden: true, checked: false, listeners: {}, textContent: '', reportValidity: () => true, focus() {}, addEventListener(event, listener) { this.listeners[event] = listener; } });
    return elements.get(selector);
  };
  const calls = [];
  const storage = new Map();
  const responses = [{ success: true }, { proof: 'proof' }, { receipt: 'receipt', requestId: 'request-1', status: 'REQUESTED' }];
  runInNewContext(source, { document: { body: { dataset: { api: 'https://api.staging.triku.in' } }, querySelector: get, querySelectorAll: () => [...elements.values()] },
    sessionStorage: { getItem: key => storage.get(key), setItem: (key, value) => storage.set(key, value) }, AbortSignal,
    fetch: async (url, options) => { calls.push({ url, options }); return { ok: true, json: async () => responses.shift() }; } });
  const trigger = async (selector, event = 'click') => { get(selector).listeners[event]({ preventDefault() {} }); await new Promise(resolve => setImmediate(resolve)); };
  return { get, calls, storage, trigger };
}
test('verification never logs in or creates an account; deletion requires separate confirmation', async () => {
  const { get, calls, storage, trigger } = setup();
  get('#phone').value = '9876543210';
  await trigger('#send');
  assert.equal(calls.length, 1);
  get('#otp').value = '123456';
  await trigger('#verify');
  assert.equal(calls.length, 2);
  await trigger('#deletion-form', 'submit');
  assert.equal(calls.length, 2, 'unchecked confirmation cannot delete');
  get('#consent').checked = true;
  await trigger('#deletion-form', 'submit');
  assert.equal(calls.length, 3);
  assert.deepEqual(JSON.parse(calls[2].options.body), { proof: 'proof', confirmed: true });
  assert.equal(get('#request-id').textContent, 'request-1');
  assert.equal(storage.get('triku-deletion-receipt:https://api.staging.triku.in'), 'receipt');
  assert.ok(calls.every(call => call.url.startsWith('https://api.staging.triku.in/auth/deletion/')));
  assert.ok(calls.every(call => call.options.credentials === 'omit'));
});
test('changing phone invalidates the verified proof', async () => {
  const { get, calls, trigger } = setup();
  await trigger('#send'); await trigger('#verify');
  get('#phone').value = '9876543211'; await trigger('#phone', 'input');
  get('#consent').checked = true; await trigger('#deletion-form', 'submit');
  assert.equal(calls.length, 2);
});
test('production and staging pages use fixed, different API targets', async () => {
  const production = await readFile(new URL('../delete-account/index.html', import.meta.url), 'utf8');
  const staging = await readFile(new URL('../delete-account/staging/index.html', import.meta.url), 'utf8');
  assert.match(production, /data-api="https:\/\/api\.triku\.in"/);
  assert.match(staging, /data-api="https:\/\/api\.staging\.triku\.in"/);
  assert.match(production, /grievance@perifury.com/);
  assert.match(production, /KYC, tax, payout and financial records remain protected/);
});
