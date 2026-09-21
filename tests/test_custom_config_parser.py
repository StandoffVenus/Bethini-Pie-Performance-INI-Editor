import tempfile
import unittest
from pathlib import Path

from lib.customConfigParser import customConfigParser


class CustomConfigParserTests(unittest.TestCase):
    def test_keeps_first_duplicate_option(self):
        parser = customConfigParser()
        parser.read_string("[Display]\niSize W=1920\niSize W=800\n")
        self.assertEqual(parser.get("Display", "iSize W"), "1920")

    def test_reads_file_without_section_header(self):
        parser = customConfigParser()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prefs.ini"
            path.write_text("bBorderless=1\n[Display]\niSize W=1920\n", encoding="utf-8")
            read = parser.read(path, encoding="utf-8")
            self.assertEqual(read, [str(path)])
        self.assertEqual(parser.get("Display", "iSize W"), "1920")


if __name__ == "__main__":
    unittest.main()
