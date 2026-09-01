import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aeris_runtime import audit


class AuditLedgerTests(unittest.TestCase):
    def test_hash_chain_passes_and_tamper_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "audit.jsonl"
            lock = root / ".lock"
            with patch.object(audit, "AUDIT_DIR", root), patch.object(audit, "LOCK_FILE", lock):
                first = audit.append_event("ONE", "tester", {"value": 1}, path=path)
                second = audit.append_event("TWO", "tester", {"value": 2}, path=path)
                self.assertEqual(second["prev_hash"], first["record_hash"])
                self.assertTrue(audit.verify_ledger(path)["valid"])

                lines = path.read_text(encoding="utf-8").splitlines()
                record = json.loads(lines[0])
                record["payload"]["value"] = 999
                lines[0] = json.dumps(record, sort_keys=True, separators=(",", ":"))
                path.write_text("\n".join(lines) + "\n", encoding="utf-8")
                result = audit.verify_ledger(path)
                self.assertFalse(result["valid"])
                self.assertTrue(any("record_hash mismatch" in error for error in result["errors"]))

    def test_empty_or_missing_ledger_is_valid_baseline(self):
        with tempfile.TemporaryDirectory() as td:
            result = audit.verify_ledger(Path(td) / "missing.jsonl")
            self.assertTrue(result["valid"])
            self.assertEqual(result["records"], 0)


if __name__ == "__main__":
    unittest.main()
