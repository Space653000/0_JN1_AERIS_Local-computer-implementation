import subprocess
import unittest
from unittest.mock import patch

from tests import browser_e2e


class BrowserE2EHarnessTests(unittest.TestCase):
    def test_single_timeout_retries_with_fresh_profile_then_requires_real_dom(self):
        with patch.object(
            browser_e2e,
            "_run_browser_process",
            side_effect=[
                subprocess.TimeoutExpired(cmd=["browser"], timeout=browser_e2e.BROWSER_TIMEOUT_SEC),
                (0, '<html><script src="/assets/app.js"></script><div id="dashboard" class="view active-view">本機聲學工程公司</div></html>', ""),
            ],
        ) as runner:
            dom = browser_e2e._dump_dom_with_bounded_timeout_retry("browser", "http://127.0.0.1:1/", "/")
        self.assertIn("本機聲學工程公司", dom)
        self.assertEqual(runner.call_count, 2)
        first_cmd = runner.call_args_list[0].args[0]
        second_cmd = runner.call_args_list[1].args[0]
        first_profile = next(x for x in first_cmd if x.startswith("--user-data-dir="))
        second_profile = next(x for x in second_cmd if x.startswith("--user-data-dir="))
        self.assertNotEqual(first_profile, second_profile)

    def test_repeated_timeout_fails_closed(self):
        timeout = subprocess.TimeoutExpired(cmd=["browser"], timeout=browser_e2e.BROWSER_TIMEOUT_SEC)
        with patch.object(browser_e2e, "_run_browser_process", side_effect=[timeout, timeout]):
            with self.assertRaisesRegex(RuntimeError, "timed out"):
                browser_e2e._dump_dom_with_bounded_timeout_retry("browser", "http://127.0.0.1:1/", "/")

    def test_nonzero_browser_exit_is_not_retried_or_hidden(self):
        with patch.object(browser_e2e, "_run_browser_process", return_value=(9, "", "fatal browser error")) as runner:
            with self.assertRaisesRegex(RuntimeError, "exit=9"):
                browser_e2e._dump_dom_with_bounded_timeout_retry("browser", "http://127.0.0.1:1/", "/")
        self.assertEqual(runner.call_count, 1)


if __name__ == "__main__":
    unittest.main()
