import unittest
import os
from pathlib import Path
import tempfile
from unittest.mock import patch
import zipfile
from package_site import public_name, association_files, build, REQUIRED

class PackageTests(unittest.TestCase):
    def test_excludes_private_and_tooling_files(self):
        for name in ['.env', '.git/config', '.github/workflows/build.yml', 'scripts/build.js',
                     'tests/fixture.html', 'output/secret.txt', '../secret.txt', 'CNAME',
                     'delete-account/delete-account.test.js', 'README.md', 'assets/.secret.txt']:
            with self.subTest(name=name): self.assertFalse(public_name(name))
    def test_includes_nested_public_routes(self):
        for name in ['index.html', 'app-ads.txt', 'delete-account/index.html',
                     'delete-account/staging/index.html', 'delete-account/delete-account.js', 'assets/logo.svg']:
            with self.subTest(name=name): self.assertTrue(public_name(name))

    def test_generates_both_android_identities_for_one_host(self):
        production = ':'.join(['AA'] * 32)
        staging = ':'.join(['BB'] * 32)
        import json
        files = association_files({
            'APP_SITE_ANDROID_SHA256_FINGERPRINTS': production,
            'APP_SITE_STAGING_ANDROID_SHA256_FINGERPRINTS': staging,
            'APP_SITE_APPLE_TEAM_ID': 'ABCDE12345',
            'REQUIRE_APP_LINK_ASSOCIATIONS': 'true',
        })
        android = json.loads(files['.well-known/assetlinks.json'])
        apple = json.loads(files['.well-known/apple-app-site-association'])
        self.assertEqual([entry['target']['package_name'] for entry in android],
                         ['com.perifury.triku', 'com.perifury.triku.staging'])
        self.assertEqual(apple['applinks']['details'][1]['components'][0]['/'], '/staging/contests/*')

    def test_release_requires_real_production_signing_identity(self):
        with self.assertRaises(ValueError):
            association_files({'REQUIRE_APP_LINK_ASSOCIATIONS': 'true'})

    def test_build_is_reproducible_and_packages_only_tracked_public_dependencies(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in REQUIRED:
                (root/name).write_text('<link href="styles.css">' if name == 'index.html' else 'public')
            (root/'styles.css').write_text('body{color:red}')
            (root/'untracked.js').write_text('private')
            tracked = '\0'.join([*sorted(REQUIRED), 'styles.css', '.env', 'scripts/build.js']).encode()
            with patch('package_site.subprocess.check_output', return_value=tracked), patch.dict(os.environ, {}, clear=True):
                build(root)
                first = (root/'output/website.zip').read_bytes()
                build(root)
            self.assertEqual(first, (root/'output/website.zip').read_bytes())
            with zipfile.ZipFile(root/'output/website.zip') as archive:
                names = archive.namelist()
                self.assertNotIn('untracked.js', names)
                self.assertNotIn('.env', names)
                versioned = [name for name in names if name.startswith('releases/assets/')]
                self.assertEqual(len(versioned), 1)
                self.assertIn(('/' + versioned[0]).encode(), archive.read('index.html'))
                self.assertEqual(archive.read(versioned[0]), archive.read('styles.css'))

if __name__ == '__main__': unittest.main()
