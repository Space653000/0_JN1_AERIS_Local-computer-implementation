import unittest
from pathlib import Path

from aeris_runtime.config import ROOT
from aeris_runtime.knowledge import build_index, search, stats
from aeris_runtime.machine import detect


class LocalServicesTests(unittest.TestCase):
    def test_knowledge_database_builds_locally(self):
        result = build_index()
        self.assertGreaterEqual(result["documents_total"], 1)
        snapshot = stats()
        self.assertTrue(snapshot["local_only"])
        self.assertIn(snapshot["search_engine"], {"sqlite_fts5", "sqlite_like_fallback"})

    def test_deleted_source_is_removed_from_index(self):
        root = ROOT / "knowledge"
        root.mkdir(exist_ok=True)
        probe = root / "__aeris_stale_index_test__.md"
        probe.write_text("AERIS_STALE_INDEX_SENTINEL_94721", encoding="utf-8")
        try:
            build_index()
            self.assertTrue(search("AERIS_STALE_INDEX_SENTINEL_94721"))
        finally:
            probe.unlink(missing_ok=True)
        result = build_index()
        self.assertGreaterEqual(result["removed_stale"], 1)
        self.assertEqual(search("AERIS_STALE_INDEX_SENTINEL_94721"), [])

    def test_machine_detection_returns_profile(self):
        result = detect()
        self.assertIn("profile", result)
        self.assertIn("os", result)


if __name__ == "__main__":
    unittest.main()
