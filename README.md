# Triku public website

Static public pages for `https://triku.in`. As of 5 November 2026, Namecheap apex/www DNS points to the AWS CloudFront distribution `E1PVBO8FXCYZZO`, backed by a private, versioned S3 bucket. GitHub Pages remains configured as a temporary rollback path; merging this repository does not publish to AWS.

The current AWS website release is `42043197344-1`, built from `caa51f7` and deployed by [run 42046698604](https://github.com/openfieldindica/triku-production-deploy/actions/runs/42046698604). It includes the account-deletion pages at `/delete-account/` and `/delete-account/staging/`. On 6 November, both paths, the homepage, and `/privacy.html` returned HTTP 200 over HTTPS. A successful page load does not verify the deletion API flow.

## Release artifact

Run `python3 -m unittest discover -s scripts -p 'test_*.py'` and `python3 scripts/package_site.py`.
The packager takes tracked public files only, including nested deletion routes when merged. Tooling, tests, hidden files, CNAME and documentation are excluded. Do not store private data in public HTML/assets.

After review/merge, dispatch **Build website artifact** on main. It validates JavaScript and any tracked `*.test.js` tests, then produces `production-website/website.zip`. No AWS credentials are used. A pull-request artifact is for validation and cannot be promoted by the deployment importer.

The same `triku.in` host provides Android and iOS app-link association files. The reviewed build generates `/.well-known/assetlinks.json` from `APP_SITE_ANDROID_SHA256_FINGERPRINTS` (production Play app-signing certificate) and optional `APP_SITE_STAGING_ANDROID_SHA256_FINGERPRINTS`; `APP_SITE_APPLE_TEAM_ID` optionally generates `/.well-known/apple-app-site-association`. Configure these as repository Actions variables. A manually dispatched release build fails without the production Android fingerprint. Production links use `/contests/...`, `/events/...`, `/wallet` and `/verification/aadhaar`; staging uses the same routes under `/staging/`. CloudFront routes them to `open-app.html` when the installed app does not claim the link.

The restricted `openfieldindica/triku-production-deploy` repository imports the successful main artifact and its SHA-256 into a reviewed release manifest. Deployment and rollback happen there after separate approval. See its `docs/website-hosting.md`.

The account-deletion page merged in website PR #3 and was included in the current AWS release. The reviewed production API task template lists both website hosts in `CORS_ORIGIN`. Verify actual browser preflight, OTP and deletion behavior with a controlled test account before claiming end-to-end deletion works. GitHub Pages branch publishing is still configured; retire it only after the rollback window is closed and the AWS site is accepted.
