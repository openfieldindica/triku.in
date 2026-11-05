"""Package only reviewed public files; never publish repository/tooling files."""
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EXTENSIONS = {'.html', '.css', '.js', '.svg', '.png', '.jpg', '.jpeg', '.webp', '.ico', '.woff', '.woff2', '.ttf', '.txt'}
REQUIRED = {'index.html', 'privacy.html', 'terms-and-conditions.html', 'contact.html', 'app-ads.txt'}


def public_name(name):
    p = Path(name)
    return (not p.is_absolute() and '..' not in p.parts and
            not any(part.startswith('.') for part in p.parts) and
            p.parts[0] not in {'scripts', 'tests', 'docs', 'output', 'node_modules'} and
            p.suffix.lower() in EXTENSIONS and not p.name.endswith(('.test.js', '.spec.js')))


def build(root=ROOT):
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=root).decode().split('\0')
    names = sorted(n for n in tracked if n and public_name(n))
    if not REQUIRED.issubset(names):
        raise ValueError('Required public pages missing')
    output = root / 'output'; output.mkdir(exist_ok=True)
    with zipfile.ZipFile(output / 'website.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for name in names:
            path = root / name
            if path.is_symlink() or not path.is_file():
                raise ValueError('Public files must be regular files')
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())
    print(f'Packaged {len(names)} public files in output/website.zip')


if __name__ == '__main__':
    build()
