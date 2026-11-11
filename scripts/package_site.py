"""Package only reviewed public files; never publish repository/tooling files."""
from pathlib import Path
import json
import os
import re
import subprocess
import zipfile
from cache_assets import version_assets

ROOT = Path(__file__).resolve().parents[1]
EXTENSIONS = {'.html', '.css', '.js', '.svg', '.png', '.jpg', '.jpeg', '.webp', '.ico', '.woff', '.woff2', '.ttf', '.txt'}
REQUIRED = {'index.html', 'privacy.html', 'terms-and-conditions.html', 'contact.html', 'app-ads.txt'}
ANDROID_ASSOCIATION = '.well-known/assetlinks.json'
APPLE_ASSOCIATION = '.well-known/apple-app-site-association'


def public_name(name):
    p = Path(name)
    return (not p.is_absolute() and '..' not in p.parts and
            not any(part.startswith('.') for part in p.parts) and
            p.parts[0] not in {'scripts', 'tests', 'docs', 'output', 'node_modules'} and
            p.suffix.lower() in EXTENSIONS and not p.name.endswith(('.test.js', '.spec.js')))


def fingerprints(value):
    values = [item.strip() for item in value.split(',') if item.strip()]
    if any(not re.fullmatch(r'(?:[0-9A-F]{2}:){31}[0-9A-F]{2}', item) for item in values):
        raise ValueError('App-link signing fingerprint must be uppercase colon-separated SHA-256')
    return values


def association_files(env):
    production = fingerprints(env.get('APP_SITE_ANDROID_SHA256_FINGERPRINTS', ''))
    staging = fingerprints(env.get('APP_SITE_STAGING_ANDROID_SHA256_FINGERPRINTS', ''))
    team = env.get('APP_SITE_APPLE_TEAM_ID', '')
    if env.get('REQUIRE_APP_LINK_ASSOCIATIONS') == 'true' and not production:
        raise ValueError('Production Play app-signing fingerprint is required for a release artifact')
    if staging and not production:
        raise ValueError('Staging fingerprint requires the production fingerprint')
    if team and not re.fullmatch(r'[A-Z0-9]{10}', team):
        raise ValueError('Apple Team ID must be 10 uppercase letters or digits')
    result = {}
    if production:
        statements = []
        for package, certs in [('com.perifury.triku', production), ('com.perifury.triku.staging', staging)]:
            if certs:
                statements.append({'relation': ['delegate_permission/common.handle_all_urls'], 'target': {
                    'namespace': 'android_app', 'package_name': package,
                    'sha256_cert_fingerprints': certs}})
        result[ANDROID_ASSOCIATION] = (json.dumps(statements, indent=2) + '\n').encode()
    if team:
        details = []
        for package, prefix in [('com.perifury.triku', ''), ('com.perifury.triku.staging', '/staging')]:
            details.append({'appIDs': [f'{team}.{package}'], 'components': [
                {'/': f'{prefix}/contests/*'}, {'/': f'{prefix}/events/*'},
                {'/': f'{prefix}/wallet'}, {'/': f'{prefix}/verification/aadhaar'}]})
        result[APPLE_ASSOCIATION] = (json.dumps({'applinks': {'details': details}}, indent=2) + '\n').encode()
    return result


def build(root=ROOT):
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=root).decode().split('\0')
    names = sorted(n for n in tracked if n and public_name(n))
    generated = association_files(os.environ)
    if not REQUIRED.issubset(names):
        raise ValueError('Required public pages missing')
    files = dict(generated)
    for name in names:
        path = root / name
        if path.is_symlink() or not path.is_file():
            raise ValueError('Public files must be regular files')
        files[name] = path.read_bytes()
    files = version_assets(files)
    output = root / 'output'; output.mkdir(exist_ok=True)
    with zipfile.ZipFile(output / 'website.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    print(f'Packaged {len(files)} public files in output/website.zip')


if __name__ == '__main__':
    build()
