# Non-interactive web OTP component

`assets/otp-request.mjs` is ready to mount inside a complete web flow. It does not
implement account deletion or a website login session. The current deletion
placeholder is intentionally unchanged. Do not expose a dead-end OTP form before
that flow is implemented; the existing OTP verifier creates accounts.

## Provisioning

Create a Cloudflare Turnstile widget in **Non-interactive** mode, restricted to
`triku.in`. Use separate widgets for staging/production. Non-interactive is a
Cloudflare widget setting, not a JavaScript mode flag. Hosting remains GitHub Pages.

- Public website config: the returned site key and exact HTTPS API origin.
- API secrets: `TURNSTILE_SECRET_KEY`.
- API configuration: `TURNSTILE_HOSTNAMES=triku.in`; review shared OTP budgets,
  trusted proxy hops and add the website's exact origin to CORS when mounting.
- Never commit a secret key or place one in a browser bundle.

Load Cloudflare's script from
`https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit` with async
and defer. Mount after its load event. On script failure, keep submission disabled
and show the support contact. If adding CSP, allow the documented Cloudflare
script/frame origins; don't proxy or self-host the script.

Use a labelled phone input (`type="tel"`, `autocomplete="tel"`, required), a widget
container, a status element, a disabled Send OTP button, a Retry verification
button and a visible `mailto:grievance@perifury.com` support link. Call:

```js
import { mountOtpRequest } from './assets/otp-request.mjs';
const dispose = mountOtpRequest({
  form, phoneInput, submitButton, status, container,
  siteKey: publicConfig.turnstileSiteKey,
  apiBaseUrl: publicConfig.apiBaseUrl,
  onSent: showNextStep
});
retryButton.addEventListener('click', () => {
  form.dispatchEvent(new Event('retryverification'));
});
// Call dispose() when removing the form.
```

The component sends only to `/auth/otp/web/request` with action `otp_request`.
The backend must verify the token's success, hostname and action before sending.
Expired, failed, used and timed-out tokens cannot enable another send. Every send
requires fresh verification; the component resets the widget after completion.
No automatic SMS retry, mobile-endpoint fallback, URL token, or local storage is
used. A 429 displays a wait message. Duplicate clicks are suppressed. A failed
verification offers retry/support without granting an SMS bypass.

Cloudflare tokens and provider secrets are never displayed. Update the privacy
notice to disclose Cloudflare bot protection when this component is actually
mounted and enabled. No third-party script loads on existing pages in this PR.

Run `node --test tests/otp-request.test.mjs` and `node --check assets/otp-request.mjs`.
Production acceptance requires a real configured widget and backend, including
expired/replayed tokens, blocked scripts and mobile browser testing. Mock tests
verify application behavior, not Cloudflare's bot detection.

References:
https://developers.cloudflare.com/turnstile/concepts/widget/
https://developers.cloudflare.com/turnstile/get-started/server-side-validation/
