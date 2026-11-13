"""Legal documents remain independently addressable and cross-linked."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class LegalPagesTests(unittest.TestCase):
    def test_separate_documents_and_navigation(self):
        terms = (ROOT / 'terms-of-use.html').read_text()
        legality = (ROOT / 'legality.html').read_text()
        self.assertIn('<section id="terms-of-use"', terms)
        self.assertNotIn('<section id="legality"', terms)
        self.assertIn('<section id="legality"', legality)
        self.assertNotIn('<section id="terms-of-use"', legality)
        for document in (terms, legality):
            self.assertIn('href="terms-of-use.html"', document)
            self.assertIn('href="legality.html"', document)
        self.assertIn('id="legality"', terms)  # Existing fragment links remain useful.

if __name__ == '__main__':
    unittest.main()
