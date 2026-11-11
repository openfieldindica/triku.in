import hashlib
import unittest
from cache_assets import PREFIX, version_assets


class CacheAssetTests(unittest.TestCase):
    def target(self, data, suffix):
        return '/' + PREFIX + hashlib.sha256(data).hexdigest() + suffix

    def test_nested_pages_use_absolute_versioned_assets_and_keep_aliases(self):
        files = {'styles.css': b'body{color:red}', 'assets/logo.svg': b'<svg/>',
                 'delete-account/form.js': b'console.log("hello")',
                 'delete-account/index.html': b'<link href="../styles.css?v=1"><img src="/assets/logo.svg#mark"><script src="form.js"></script><a href="/privacy.html">Privacy</a>',
                 'app-ads.txt': b'publisher', '.well-known/assetlinks.json': b'[]'}
        result = version_assets(files)
        html = result['delete-account/index.html'].decode()
        for name, suffix in [('styles.css', '.css'), ('assets/logo.svg', '.svg'), ('delete-account/form.js', '.js')]:
            self.assertIn(self.target(files[name], suffix), html)
            self.assertEqual(result[name], files[name])
        self.assertIn('.css?v=1', html)
        self.assertIn('.svg#mark', html)
        self.assertIn('href="/privacy.html"', html)
        for name in ['app-ads.txt', '.well-known/assetlinks.json']:
            self.assertEqual(result[name], files[name])

    def test_css_dependencies_are_hashed_before_parents_and_changes_propagate(self):
        files = {'index.html': b'<link href="css/main.css">',
                 'css/main.css': b'@import "./base.css"; .logo{background:url(../logo.svg#mark)}',
                 'css/base.css': b'body{color:red}', 'logo.svg': b'<svg/>'}
        old = version_assets(files)
        new = version_assets(dict(files, **{'logo.svg': b'<svg>new</svg>'}))
        self.assertNotEqual(old['index.html'], new['index.html'])
        css = [data for name, data in old.items() if name.startswith(PREFIX) and b'@import' in data][0]
        self.assertIn(self.target(files['css/base.css'], '.css').encode(), css)
        self.assertIn((self.target(files['logo.svg'], '.svg') + '#mark').encode(), css)
        for name, data in old.items():
            if name.startswith(PREFIX):
                self.assertEqual(name.split('/')[-1].split('.')[0], hashlib.sha256(data).hexdigest())
        self.assertEqual(old, version_assets(dict(reversed(list(files.items())))))

    def test_external_data_and_fragment_urls_are_unchanged(self):
        html = b'<img src="https://example.com/logo.svg?a=1&amp;b=2"><img src="data:image/svg+xml;base64,AA"><a href="#x">X</a><script src="//example.com/app.js"></script><div data-src="missing.js"></div>'
        self.assertEqual(version_assets({'index.html': html})['index.html'], html)

    def test_local_query_strings_remain_html_escaped(self):
        html = b'<link href="main.css?a=1&amp;b=2">'
        result = version_assets({'index.html': html, 'main.css': b'body{}'})
        self.assertIn(b'.css?a=1&amp;b=2', result['index.html'])

    def test_missing_assets_cycles_and_reserved_paths_fail_closed(self):
        for files in [{'index.html': b'<script src="missing.js"></script>'},
                      {'a.css': b'@import "b.css"', 'b.css': b'@import "a.css"'},
                      {'releases/secret.txt': b'private'},
                      {'app.js': b'import "./module.js"'},
                      {'index.html': b'<base href="/other/">'}]:
            with self.subTest(files=files), self.assertRaises(ValueError):
                version_assets(files)
