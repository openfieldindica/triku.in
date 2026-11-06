const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { runInNewContext } = require('node:vm');
const test = require('node:test');

const code = readFileSync('open-app.js', 'utf8');
for (const path of ['/contests/c1', '/contests/c1/results', '/events/e1', '/wallet',
  '/verification/aadhaar', '/staging/contests/c1', '/staging/events/e1', '/staging/wallet']) {
  test(`fallback opens ${path}`, () => {
    let href;
    runInNewContext(code, {
      window: { location: { pathname: path } },
      document: { querySelector: selector => selector === '[data-open-app]'
        ? { setAttribute: (_, value) => { href = value; } }
        : { set textContent(_) {} } }
    });
    assert.equal(href, `triku:/${path.replace(/^\/staging/, '')}`);
  });
}
