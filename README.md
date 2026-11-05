# Triku public website

Static public pages for triku.in. GitHub Pages remains the live host until a separately approved DNS cutover. This PR does not change Pages configuration or publish to AWS.

## Release artifact

Run `python3 -m unittest discover -s scripts -p 'test_*.py'` and `python3 scripts/package_site.py`.
The packager takes tracked public files only, including nested deletion routes when merged. Tooling, tests, hidden files, CNAME and documentation are excluded. Do not store private data in public HTML/assets.

After review/merge, dispatch **Build website artifact** on main. It validates JavaScript and any tracked `*.test.js` tests, then produces `production-website/website.zip`. No AWS credentials are used. A pull-request artifact is for validation and cannot be promoted by the deployment importer.

The restricted `openfieldindica/triku-production-deploy` repository imports the successful main artifact and its SHA-256 into a reviewed release manifest. Deployment and rollback happen there after separate approval. See its `docs/website-hosting.md`.

The account-deletion page is a separate PR. Build a fresh artifact after that PR merges; this hosting change does not itself ship deletion or change API CORS. Existing Pages branch publishing can still publish merged public page changes until Pages is disabled during cutover; merging this tooling only adds non-product files.
