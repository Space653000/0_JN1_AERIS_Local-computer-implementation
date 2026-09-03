import json
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock,patch

from aeris_runtime.engineering.intake import understand


class EngineeringIntakeTests(unittest.TestCase):
    def test_local_proposal_is_not_evidence_or_automatic_execution(self):
        router=MagicMock(); router.chat.return_value=SimpleNamespace(text=json.dumps({"objective":"measure delay","needed_skills":["gcc-phat-tdoa"],"hypotheses":["channel timing mismatch"]}),provider="local-test",model="test")
        with patch("aeris_runtime.engineering.intake.route_pod",return_value={"state":"PLANNED"}),patch("aeris_runtime.engineering.intake.Harness") as memory:
            result=understand("Estimate two-microphone delay",router=router)
            self.assertEqual(result["classification"],"INFERENCE")
            self.assertFalse(result["execution_performed"])
            self.assertIn("reference",result["required_input_fields"]["gcc-phat-tdoa"])
            memory.return_value.append.assert_called_once()

    def test_hallucinated_skill_and_measurement_fields_are_rejected(self):
        for proposal in ({"objective":"x","needed_skills":["licensed-comsol-auto"],"hypotheses":[]},
                         {"objective":"x","needed_skills":["spectral-analysis"],"hypotheses":[],"measured_spl":94}):
            router=MagicMock(); router.chat.return_value=SimpleNamespace(text=json.dumps(proposal))
            with self.assertRaises(ValueError): understand("speaker question",router=router)
