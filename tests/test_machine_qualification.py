import unittest
from unittest.mock import patch

import aeris_runtime.machine as machine
from aeris_runtime.machine_qualification import qualify_facts


class MachineQualificationTests(unittest.TestCase):
    def base_facts(self):
        return {
            "profile": "windows-cpu",
            "ram_gb": 16,
            "disk_free_gb": 50,
            "python_version": "3.11.9",
            "gpu": "not_detected",
            "vram_gb": None,
            "tools": {"git": True, "ollama": True, "nvidia-smi": False},
        }

    def test_supported_baseline_qualifies_without_claiming_accelerated_ai(self):
        result = qualify_facts(self.base_facts())
        self.assertEqual(result["overall_state"], "QUALIFIED_BASELINE")
        self.assertEqual(result["workloads"]["control_plane"]["state"], "QUALIFIED_BASELINE")
        self.assertEqual(result["workloads"]["deterministic_acoustic_analysis"]["state"], "QUALIFIED_BASELINE")
        self.assertEqual(result["workloads"]["nvidia_accelerated_local_ai"]["state"], "NOT_APPLICABLE")
        self.assertIn("not real-machine VERIFIED", result["truth"])

    def test_low_ram_fails_required_baseline(self):
        facts = self.base_facts()
        facts["ram_gb"] = 2
        result = qualify_facts(facts)
        self.assertEqual(result["overall_state"], "NOT_QUALIFIED")
        self.assertEqual(result["workloads"]["control_plane"]["state"], "NOT_QUALIFIED")

    def test_unknown_resource_blocks_instead_of_guessing(self):
        facts = self.base_facts()
        facts["disk_free_gb"] = None
        result = qualify_facts(facts)
        self.assertEqual(result["overall_state"], "BLOCKED_INCOMPLETE_EVIDENCE")
        self.assertEqual(result["workloads"]["deterministic_acoustic_analysis"]["state"], "BLOCKED_INCOMPLETE_EVIDENCE")

    def test_nvidia_workload_enforces_vram_and_tools(self):
        facts = self.base_facts()
        facts.update({
            "profile": "windows-nvidia-workstation",
            "gpu": "NVIDIA RTX TEST, 4096 MiB",
            "vram_gb": 4,
            "tools": {"git": True, "ollama": True, "nvidia-smi": True},
        })
        result = qualify_facts(facts)
        self.assertEqual(result["overall_state"], "QUALIFIED_BASELINE")
        self.assertEqual(result["workloads"]["nvidia_accelerated_local_ai"]["state"], "NOT_QUALIFIED")

    def test_unsupported_profile_never_qualifies_overall(self):
        facts = self.base_facts()
        facts["profile"] = "unsupported-unprofiled"
        result = qualify_facts(facts)
        self.assertEqual(result["overall_state"], "UNSUPPORTED_PROFILE")

    def test_machine_detect_embeds_qualification_without_fake_verification(self):
        with patch.object(machine.platform, "system", return_value="Windows"), \
             patch.object(machine.platform, "machine", return_value="AMD64"), \
             patch.object(machine, "_gpu", return_value="not_detected"), \
             patch.object(machine, "_vram_gb", return_value=None), \
             patch.object(machine, "_ram_gb", return_value=16), \
             patch.object(machine, "_disk_free_gb", return_value=50), \
             patch.object(machine.shutil, "which", side_effect=lambda name: f"C:/fake/{name}.exe" if name in {"git", "python", "ollama"} else None):
            result = machine.detect()
        self.assertEqual(result["profile"], "windows-cpu")
        self.assertEqual(result["support_state"], "SUPPORTED_PROFILE_QUALIFIED_BASELINE")
        self.assertEqual(result["qualification"]["overall_state"], "QUALIFIED_BASELINE")
        self.assertIn("not real-machine verification", result["truth"])


if __name__ == "__main__":
    unittest.main()
