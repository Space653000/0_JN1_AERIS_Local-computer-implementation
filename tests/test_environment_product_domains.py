import copy
import json
import unittest
from pathlib import Path

from aeris_runtime import reproduction
from aeris_runtime.engineering import domain_review, environment_products as products
from aeris_runtime.engineering import environment_products_review as reviewers
from aeris_runtime.engineering import role_acceptance
from aeris_runtime.engineering.orchestration import run_role
from tests.engineering_test_support import isolated_engineering_state

ROOT = Path(__file__).parents[1]


def base(role):
    return json.loads((ROOT / f"golden/roles/{role}/golden.json").read_text())["base_input"]


SPECS = {
    "R058": ("R073", "thin-tv-panel-wall-dialogue-baseline", "thin-tv-panel-wall-dialogue-domain-review", products.analyze_tv, reviewers.review_tv, "panel_mode_verified"),
    "R059": ("R074", "doorbell-weather-intercom-baseline", "doorbell-weather-intercom-domain-review", products.analyze_doorbell, reviewers.review_doorbell, "weather_transfer_verified"),
    "R060": ("R075", "appliance-motor-notification-voice-baseline", "appliance-motor-notification-voice-domain-review", products.analyze_appliance, reviewers.review_appliance, "command_quality_verified"),
    "R061": ("R080", "ar-open-ear-leakage-tracking-wind-baseline", "ar-open-ear-leakage-tracking-wind-domain-review", products.analyze_open_ear, reviewers.review_open_ear, "head_tracking_verified"),
}


class EnvironmentProductDomainTests(unittest.TestCase):
    def test_each_product_owns_six_distinct_decisions(self):
        expected = {
            "R058": ["PANEL_RESONANCE_MARGIN", "DIALOGUE_HEADROOM", "WALL_CLEARANCE", "WOOFER_EXCURSION", "MOUNT_BUZZ_LEVEL", "PLACEMENT_COVERAGE"],
            "R059": ["WET_MESH_LOSS", "WIND_NOISE_LEVEL", "INTERCOM_FEEDBACK_MARGIN", "ECHO_COUPLING", "MOUNT_RESONANCE_LEVEL", "WEATHER_STATE_COVERAGE"],
            "R060": ["MOTOR_HARMONIC_CAPTURE", "OPERATING_STATE_COVERAGE", "NOTIFICATION_HEADROOM", "DRIVER_DUTY", "ENCLOSURE_LEAK_LOSS", "COMMAND_SNR"],
            "R061": ["AUDIBILITY_MARGIN", "PRIVACY_LEAKAGE", "HEAD_POSE_COVERAGE", "TRACKING_LATENCY", "WIND_CAPTURE_SNR", "FIT_RESPONSE_SPREAD"],
        }
        for role, spec in SPECS.items():
            with self.subTest(role=role):
                result = spec[3](base(role))
                self.assertEqual([c["id"] for c in result["checks"]], expected[role])
                self.assertEqual(result["disposition"], "BOUNDED_BASELINE_ACCEPT")
                self.assertFalse(result["physical_measurement_verified"])

    def test_physical_claims_and_unknown_fields_fail_closed(self):
        claims = {"R058": "physical_tv_verified", "R059": "physical_doorbell_verified",
                  "R060": "physical_appliance_verified", "R061": "physical_open_ear_verified"}
        for role, spec in SPECS.items():
            with self.subTest(role=role):
                with self.assertRaises(ValueError):
                    spec[3]({**base(role), claims[role]: True})
                invalid = {**base(role), "undeclared_pass": True}
                with self.assertRaises(ValueError):
                    spec[3](invalid)

    def test_independent_reviewers_reject_overclaims(self):
        for role, spec in SPECS.items():
            with self.subTest(role=role):
                candidate = spec[3](base(role))
                self.assertEqual(spec[4](base(role), candidate)["decision"], "BOUNDED_REVIEW_ACCEPT")
                altered = copy.deepcopy(candidate)
                altered[spec[5]] = True
                self.assertEqual(spec[4](base(role), altered)["decision"], "CHANGES_REQUIRED")

    def test_role_suites_route_to_capability_driven_independent_reviewers(self):
        with isolated_engineering_state():
            factory = role_acceptance.RoleAcceptanceFactory()
            for role, spec in SPECS.items():
                reviewer, skill, review_skill, analyze, _, _ = spec
                with self.subTest(role=role):
                    self.assertTrue(factory.evaluate(role, skill)["execution_passed"])
                    self.assertTrue(factory.evaluate(reviewer, review_skill)["execution_passed"])
                    run = run_role(role, skill, base(role), objective=f"Bound {role} product architecture", source_kind="SYNTHETIC")
                    self.assertEqual([r["role_id"] for r in run["pod"]["reviewers"]], [reviewer])
                    self.assertTrue(domain_review.review_status(run["review"]["review_run_id"])["valid"])
                    self.assertEqual(reproduction.reproduce_run(run["evidence_run_id"])["result"], "PASS")


if __name__ == "__main__":
    unittest.main()
