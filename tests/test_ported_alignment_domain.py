import copy
import math
import unittest

from aeris_runtime.engineering import ported_alignment, ported_alignment_review
from aeris_runtime.engineering import domain_review, role_acceptance
from aeris_runtime.engineering.orchestration import run_role
from aeris_runtime import reproduction
from tests.engineering_test_support import isolated_engineering_state


BASE = {
    "model": "IDEAL_LUMPED_HELMHOLTZ_PORT",
    "sound_speed_m_s": 343.0,
    "sound_speed_lower_m_s": 340.0,
    "sound_speed_upper_m_s": 346.0,
    "cavity_volume_m3": 0.020,
    "cavity_volume_lower_m3": 0.019,
    "cavity_volume_upper_m3": 0.021,
    "port_area_m2": 0.003,
    "port_area_lower_m2": 0.0028,
    "port_area_upper_m2": 0.0032,
    "physical_length_m": 0.20,
    "end_correction_m": 0.04,
    "effective_length_lower_m": 0.23,
    "effective_length_upper_m": 0.25,
    "volume_velocity_peak_m3_s": 0.020,
    "volume_velocity_upper_m3_s": 0.022,
    "minimum_tuning_hz": 35.0,
    "maximum_tuning_hz": 50.0,
    "maximum_port_velocity_m_s": 8.0,
    "analysis_max_hz": 300.0,
    "minimum_longitudinal_mode_ratio": 2.0,
    "largest_dimension_m": 0.20,
    "maximum_dimension_wavelength_ratio": 0.20,
}


class PortedAlignmentDomainTests(unittest.TestCase):
    def test_role_specific_port_decision_and_bounds(self):
        result = ported_alignment.analyze(BASE)
        expected = 343.0 / (2 * math.pi) * math.sqrt(0.003 / (0.020 * 0.24))
        self.assertAlmostEqual(result["tuning_hz"], expected, places=12)
        self.assertLessEqual(result["tuning_interval_hz"][0], result["tuning_hz"])
        self.assertGreaterEqual(result["tuning_interval_hz"][1], result["tuning_hz"])
        self.assertAlmostEqual(result["port_velocity_m_s"], 0.020 / 0.003, places=12)
        self.assertEqual(
            [row["id"] for row in result["checks"]],
            ["TUNING_INTERVAL", "PORT_VELOCITY", "LONGITUDINAL_MODE_SEPARATION", "LUMPED_GEOMETRY_VALIDITY"],
        )
        self.assertEqual(result["disposition"], "BOUNDED_BASELINE_ACCEPT")
        self.assertFalse(result["physical_measurement_verified"])
        self.assertFalse(result["chuffing_verified"])
        self.assertFalse(result["waveguide_directivity_verified"])

    def test_velocity_and_model_boundaries_fail_closed(self):
        result = ported_alignment.analyze({**BASE, "maximum_port_velocity_m_s": 7.0})
        self.assertFalse(result["checks"][1]["passed"])
        self.assertEqual(result["disposition"], "DESIGN_REVISION_REQUIRED")
        with self.assertRaises(ValueError):
            ported_alignment.analyze({**BASE, "model": "CFD_VERIFIED"})
        with self.assertRaises(ValueError):
            ported_alignment.analyze({**BASE, "effective_length_lower_m": 0.25})
        with self.assertRaises(ValueError):
            ported_alignment.analyze({**BASE, "port_area_m2": float("nan")})

    def test_independent_review_recomputes_and_rejects_false_candidate(self):
        candidate = ported_alignment.analyze(BASE)
        accepted = ported_alignment_review.review(BASE, candidate)
        self.assertEqual(accepted["decision"], "BOUNDED_REVIEW_ACCEPT")
        false_candidate = copy.deepcopy(candidate)
        false_candidate["port_velocity_upper_m_s"] = 1.0
        rejected = ported_alignment_review.review(BASE, false_candidate)
        self.assertEqual(rejected["decision"], "CHANGES_REQUIRED")
        self.assertEqual(rejected["disagreements"][0]["field"], "port_velocity_upper_m_s")
        with self.assertRaises(ValueError):
            ported_alignment_review.review(BASE, {**candidate, "physical_acceptance": True})

    def test_r011_routes_to_independently_evidenced_second_r021_capability(self):
        with isolated_engineering_state():
            runner = role_acceptance.RoleAcceptanceFactory()
            executor = runner.evaluate("R011", "speaker-ported-alignment-baseline")
            reviewer = runner.evaluate("R021", "speaker-port-lumped-domain-review")
            self.assertTrue(executor["execution_passed"], executor)
            self.assertTrue(reviewer["execution_passed"], reviewer)
            # R021's other sealed-box reviewer capability remains missing, so
            # aggregate L1 must not hide the exact current port qualification.
            aggregate = runner.status("R021")
            self.assertEqual(aggregate["level"], "L1")
            self.assertEqual(aggregate["passed_capability_count"], 1)
            report = run_role(
                "R011", "speaker-ported-alignment-baseline", BASE,
                objective="Bound ideal port tuning and velocity before physical validation",
                source_kind="SYNTHETIC",
            )
            self.assertEqual(report["review"]["decision"], "BOUNDED_REVIEW_ACCEPT")
            self.assertEqual([item["role_id"] for item in report["pod"]["reviewers"]], ["R021"])
            self.assertTrue(domain_review.review_status(report["review"]["review_run_id"])["valid"])
            self.assertEqual(reproduction.reproduce_run(report["evidence_run_id"])["result"], "PASS")


if __name__ == "__main__":
    unittest.main()
