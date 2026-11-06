import unittest
from package_site import public_name, association_files

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

if __name__ == '__main__': unittest.main()
