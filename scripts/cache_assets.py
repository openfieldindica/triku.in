"""Content-address public assets; retain stable aliases for existing links."""
import hashlib
from html import escape, unescape
from pathlib import PurePosixPath
import posixpath
import re
from urllib.parse import urlsplit, urlunsplit

PREFIX = 'releases/assets/'
ASSET_EXTENSIONS = {'.css', '.js', '.svg', '.png', '.jpg', '.jpeg', '.webp',
                    '.ico', '.woff', '.woff2', '.ttf'}
HTML_URL = re.compile(r'''(?P<attribute>(?<![\w:-])(?:src|href)\s*=\s*)(?P<quote>["'])(?P<url>.*?)(?P=quote)''', re.I)
CSS_URL = re.compile(r'''url\(\s*(?P<quote>["']?)(?P<url>[^)"']*?)(?P=quote)\s*\)''', re.I)
CSS_IMPORT = re.compile(r'''(?P<import>@import\s+)(?P<quote>["'])(?P<url>.*?)(?P=quote)''', re.I)


def version_assets(files):
    if any(name.startswith('releases/') for name in files):
        raise ValueError('releases/ is reserved for generated assets')
    output = dict(files)
    names = {}
    visiting = set()

    def rewrite_url(value, owner):
        url = urlsplit(unescape(value))
        if url.scheme or url.netloc or not url.path:
            return value
        path = posixpath.normpath(posixpath.join(posixpath.dirname(owner), url.path)
                                 if not url.path.startswith('/') else url.path[1:])
        if PurePosixPath(path).suffix.lower() not in ASSET_EXTENSIONS:
            return value
        if path not in files:
            raise ValueError(f'Missing local asset {value} referenced by {owner}')
        return urlunsplit(('', '', '/' + version(path), url.query, url.fragment))

    def version(name):
        if name in names:
            return names[name]
        if name in visiting:
            raise ValueError(f'Cyclic CSS asset dependency: {name}')
        visiting.add(name)
        data = files[name]
        suffix = PurePosixPath(name).suffix.lower()
        if suffix == '.css':
            css = data.decode('utf-8')
            css = CSS_URL.sub(lambda m: 'url("' + rewrite_url(m['url'], name) + '")', css)
            css = CSS_IMPORT.sub(lambda m: m['import'] + m['quote'] +
                                 rewrite_url(m['url'], name) + m['quote'], css)
            data = css.encode('utf-8')
        # Current scripts are standalone. Relative module imports need a bundler
        # before they can move into this shared namespace.
        if suffix == '.js' and re.search(r'\bimport\s*(?:[({*\'"]|[\w$]+\s+from)', data.decode('utf-8')):
            raise ValueError(f'Bundle JavaScript imports before versioning: {name}')
        target = PREFIX + hashlib.sha256(data).hexdigest() + suffix
        output[target] = data
        names[name] = target
        visiting.remove(name)
        return target

    for name in sorted(files):
        if PurePosixPath(name).suffix.lower() in ASSET_EXTENSIONS:
            version(name)
    for name, data in files.items():
        if name.endswith('.html'):
            html = data.decode('utf-8')
            if re.search(r'<base\b|\bsrcset\s*=', html, re.I):
                raise ValueError('Add explicit base/srcset handling before packaging these pages')
            def replace(match):
                url = rewrite_url(match['url'], name)
                if url == match['url']:
                    return match[0]
                return match['attribute'] + match['quote'] + escape(url, quote=True) + match['quote']
            output[name] = HTML_URL.sub(replace, html).encode('utf-8')
    return output
