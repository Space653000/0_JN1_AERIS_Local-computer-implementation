import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import aeris_runtime.skills_runtime as skills


class AcousticSkillTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.csv = self.root / "fr.csv"
        self.csv.write_text(
            "frequency_hz,level_db\n100,80\n200,81\n500,79\n1000,82\n2000,80\n",
            encoding="utf-8",
        )
        self.patch = patch.object(skills, "_ALLOWED_INPUT_ROOTS", (self.root,))
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        self.tmp.cleanup()

    def test_measurement_import_validation(self):
        result = skills.measurement_import_validation(str(self.csv))
        self.assertEqual(result["result"], "PASS")
        self.assertEqual(result["points"], 5)
        self.assertTrue(result["strictly_increasing"])

    def test_fr_analysis_is_deterministic(self):
        result = skills.frequency_response_analysis(str(self.csv), 100, 2000)
        self.assertEqual(result["peak_to_peak_db"], 3.0)
        self.assertEqual(result["average_db"], 80.4)
        self.assertEqual(result["minimum_point"]["frequency_hz"], 500.0)
        self.assertEqual(result["maximum_point"]["frequency_hz"], 1000.0)

    def test_requirement_verification_reports_margin(self):
        result = skills.requirement_verification(str(self.csv), {"band_hz": [100, 2000], "max_peak_to_peak_db": 4.0})
        self.assertEqual(result["result"], "PASS")
        self.assertEqual(result["checks"][0]["margin"], 1.0)

    def test_outside_allowed_roots_is_rejected(self):
        other = Path(self.tmp.name).parent / "outside-aeris-skill.csv"
        other.write_text("frequency_hz,level_db\n100,1\n200,2\n", encoding="utf-8")
        try:
            with self.assertRaises(ValueError):
                skills.measurement_import_validation(str(other))
        finally:
            other.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
