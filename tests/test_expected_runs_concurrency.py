import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

import aeris_runtime.expected_runs as er


class ExpectedRunsConcurrencyTests(unittest.TestCase):
    def test_parallel_marks_do_not_share_a_temp_filename(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(er, "REGISTRY_PATH", Path(tmp) / "runs.json"):
            er.register("heartbeat", max_age_sec=60)
            errors=[]
            def mark():
                try: er.mark("heartbeat", True, audit_event=False)
                except Exception as exc: errors.append(exc)
            threads=[threading.Thread(target=mark) for _ in range(24)]
            [t.start() for t in threads];[t.join() for t in threads]
            self.assertEqual(errors, [])
            self.assertEqual(json.loads(er.REGISTRY_PATH.read_text(encoding="utf-8"))["expected_runs"]["heartbeat"]["last_result"], "SUCCESS")


if __name__ == "__main__": unittest.main()
