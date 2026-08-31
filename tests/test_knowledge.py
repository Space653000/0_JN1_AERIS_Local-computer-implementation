import unittest
from aeris_runtime.knowledge import build_index, stats
from aeris_runtime.machine import detect

class LocalServicesTests(unittest.TestCase):
    def test_knowledge_database_builds_locally(self):
        result=build_index(); self.assertGreaterEqual(result["documents_total"],1); self.assertTrue(stats()["local_only"])
    def test_machine_detection_returns_profile(self):
        result=detect(); self.assertIn("profile",result); self.assertIn("os",result)

if __name__=="__main__": unittest.main()
