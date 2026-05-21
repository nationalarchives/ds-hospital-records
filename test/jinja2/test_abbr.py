from django.test import TestCase

from config.jinja2 import abbr


class TestAbbr(TestCase):
    def test_abbr_circa_with_space(self):
        self.assertEqual(abbr("c. 1900"), '<abbr title="circa">c.</abbr> 1900')

    def test_abbr_circa_without_space(self):
        self.assertEqual(abbr("c.1900"), '<abbr title="circa">c.</abbr>1900')

    def test_abbr_colon_codes(self):
        value = "PLI: Foo LA: Bar"
        expected = (
            '<abbr title="Poor Law Institution">PLI</abbr>: Foo '
            '<abbr title="Local Authority">LA</abbr>: Bar'
        )
        self.assertEqual(abbr(value), expected)

    def test_abbr_other_codes(self):
        value = "AC: GER: LRO: AR: NRA: C: CAT: VOL: MNT:"
        expected = (
            '<abbr title="Acute">AC</abbr>: '
            '<abbr title="Geriatric">GER</abbr>: '
            '<abbr title="Local Record Office">LRO</abbr>: '
            '<abbr title="At Repository">AR</abbr>: '
            '<abbr title="National Register of Archives">NRA</abbr>: '
            '<abbr title="Children">C</abbr>: '
            '<abbr title="Catalogue">CAT</abbr>: '
            '<abbr title="Voluntary">VOL</abbr>: '
            '<abbr title="Mental">MNT</abbr>:'
        )
        self.assertEqual(abbr(value), expected)

    def test_abbr_no_change(self):
        self.assertEqual(abbr("No abbreviations here"), "No abbreviations here")
