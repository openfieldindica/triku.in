const form = document.querySelector('#deletion-form');
const phone = document.querySelector('#phone');
const otp = document.querySelector('#otp');
const message = document.querySelector('#message');
const statusPanel = document.querySelector('#status-panel');
const api = document.body.dataset.api;
const storageKey = `triku-deletion-receipt:${api}`;
let proof = null;
let busy = false;
async function request(path, data) {
  const response = await fetch(`${api}/auth/deletion/${path}`, {
    method: 'POST', credentials: 'omit', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data), signal: AbortSignal.timeout(15000)
  });
  if (!response.ok) throw new Error(response.status === 429 ? 'Please wait before trying again.' : 'Unable to continue. Check your code or request a new one. For help, email grievance@perifury.com.');
  return response.json();
}
function storedReceipt() { try { return sessionStorage.getItem(storageKey); } catch { return null; } }
function saveReceipt(receipt) { try { sessionStorage.setItem(storageKey, receipt); } catch { /* Recovery remains available by OTP. */ } }
function showStatus(result) {
  statusPanel.hidden = false;
  document.querySelector('#request-id').textContent = result.requestId;
  document.querySelector('#request-status').textContent = result.status === 'COMPLETED'
    ? 'Account deletion completed. Required KYC, tax, payout and financial records remain protected.'
    : result.blocker === 'FUNDS_OR_CONTESTS'
      ? 'Request accepted. Support must resolve your funds or contests before final deletion. Contact us with your request number.'
      : 'Request accepted. Access is locked and cleanup is in progress, including provider review.';
  form.hidden = true;
}
async function run(action) {
  if (busy) return;
  busy = true;
  document.querySelectorAll('button').forEach(button => { button.disabled = true; });
  message.textContent = 'Please wait…';
  try { await action(); message.textContent = ''; }
  catch (error) { message.textContent = error instanceof Error ? error.message : 'Please try again.'; }
  finally { busy = false; document.querySelectorAll('button').forEach(button => { button.disabled = false; }); }
}
document.querySelector('#send').addEventListener('click', () => {
  if (!phone.reportValidity()) return;
  void run(async () => {
    await request('otp/request', { phone: phone.value });
    proof = null;
    document.querySelector('#confirmation').hidden = true;
    document.querySelector('#verification').hidden = false;
    document.querySelector('#sent-message').textContent = 'If this number is registered, a code has been sent. Wait at least 30 seconds before resending.';
    otp.focus();
  });
});
phone.addEventListener('input', () => { proof = null; document.querySelector('#verification').hidden = true; document.querySelector('#confirmation').hidden = true; });
document.querySelector('#verify').addEventListener('click', () => {
  if (!otp.reportValidity()) return;
  void run(async () => {
    const result = await request('otp/verify', { phone: phone.value, otp: otp.value });
    proof = result.proof;
    document.querySelector('#confirmation').hidden = false;
    document.querySelector('#confirm').focus();
  });
});
form.addEventListener('submit', event => {
  event.preventDefault();
  if (!proof || !document.querySelector('#consent').checked) return;
  void run(async () => {
    const result = await request('request', { proof, confirmed: true });
    saveReceipt(result.receipt);
    showStatus(result);
    proof = null; phone.value = ''; otp.value = '';
  });
});
document.querySelector('#refresh').addEventListener('click', () => void run(async () => {
  const receipt = storedReceipt();
  if (!receipt) throw new Error('Verify your phone again to recover your request status.');
  showStatus(await request('status', { receipt }));
}));
document.querySelector('#recover').addEventListener('click', () => { form.hidden = false; statusPanel.hidden = true; phone.focus(); });
if (storedReceipt()) void run(async () => showStatus(await request('status', { receipt: storedReceipt() })));
