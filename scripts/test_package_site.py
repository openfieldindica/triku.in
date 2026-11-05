import unittest
from package_site import public_name

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

if __name__ == '__main__': unittest.main()
