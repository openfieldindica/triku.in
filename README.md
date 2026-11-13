# Triku public website

Static public pages for triku.in. GitHub Pages remains the live host until a separately approved DNS cutover. This PR does not change Pages configuration or publish to AWS.

## Release artifact

Run `python3 -m unittest discover -s scripts -p 'test_*.py'` and `python3 scripts/package_site.py`.
The packager takes tracked public files only, including nested deletion routes when merged. Tooling, tests, hidden files, CNAME and documentation are excluded. Do not store private data in public HTML/assets.

After review/merge, dispatch **Build website artifact** on main. It validates JavaScript and tracked `*.test.js` / `*.test.mjs` tests, then produces `production-website/website.zip`. No AWS credentials are used. A pull-request artifact is for validation and cannot be promoted by the deployment importer.

The same `triku.in` host provides Android and iOS app-link association files. The reviewed build generates `/.well-known/assetlinks.json` from `APP_SITE_ANDROID_SHA256_FINGERPRINTS` (production Play app-signing certificate) and optional `APP_SITE_STAGING_ANDROID_SHA256_FINGERPRINTS`; `APP_SITE_APPLE_TEAM_ID` optionally generates `/.well-known/apple-app-site-association`. Configure these as repository Actions variables. A manually dispatched release build fails without the production Android fingerprint. Production links use `/contests/...`, `/events/...`, `/wallet` and `/verification/aadhaar`; staging uses the same routes under `/staging/`. CloudFront routes them to `open-app.html` when the installed app does not claim the link.

The restricted `openfieldindica/triku-production-deploy` repository imports the successful main artifact and its SHA-256 into a reviewed release manifest. Deployment and rollback happen there after separate approval. See its `docs/website-hosting.md`.

## Static asset caching

The artifact packager rewrites local HTML asset URLs to absolute
`/releases/assets/<sha256>.<extension>` URLs. CSS dependencies are rewritten before
their parent CSS is hashed, so an image/font change also changes its stylesheet URL.
Identical bytes retain the same URL across builds. Original asset paths remain in
the ZIP as revalidated compatibility aliases. HTML, `app-ads.txt`, and app-link
association files keep their stable URLs and must not receive immutable caching.

The deployment repository must apply its reviewed shared-asset CloudFront origin
and cache behavior before publishing this artifact. Shared assets live outside the
active release directory and remain available across rollouts and rollbacks. Only
paths whose SHA-256 matches their bytes receive a one-year immutable cache header.
Source pages and local previews continue using ordinary filenames; generated files
belong only in the artifact, never in Git.

The packager handles the site's quoted HTML `src`/`href` references and CSS
`url()`/quoted `@import` dependencies. Current JavaScript files are standalone.
Missing dependencies, CSS cycles, module imports, HTML `base`/`srcset`, and source
files in the reserved `releases/` namespace fail the build. Introduce a module
bundler or extend these checks before adopting those constructs.

The account-deletion page is a separate PR. Build a fresh artifact after that PR merges; this hosting change does not itself ship deletion or change API CORS. Existing Pages branch publishing can still publish merged public page changes until Pages is disabled during cutover; merging this tooling only adds non-product files.

## App legal documents

`terms-of-use.html` contains Terms of Use; `legality.html` contains the separate
Legality explanation. Both pages cross-link. Existing `/terms-of-use.html#legality`
links reach a link to the extracted document. This is a presentation-only split;
legal wording and document dates are preserved. Publish both website pages before
releasing the mobile Terms & Legality submenu. No publication is implied by this branch.
