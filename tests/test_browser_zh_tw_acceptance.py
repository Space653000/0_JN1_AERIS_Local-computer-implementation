import unittest
from unittest.mock import patch

from tests import browser_zh_tw_acceptance as acceptance


class BrowserZhTwAcceptanceTests(unittest.TestCase):
    def test_main_fails_when_visible_text_violations_exist(self):
        with patch.object(acceptance, "crawl", return_value={"passed": False}):
            self.assertEqual(acceptance.main(), 1)

    def test_main_passes_only_when_all_routes_pass(self):
        with patch.object(acceptance, "crawl", return_value={"passed": True}):
            self.assertEqual(acceptance.main(), 0)


if __name__ == "__main__":
    unittest.main()
