import unittest
import ctypes
from unittest.mock import patch

import aeris_runtime.machine as machine
from aeris_runtime.machine_qualification import qualify_facts


class MachineQualificationTests(unittest.TestCase):
    def test_windows_ram_uses_native_memory_api_without_powershell(self):
        class Kernel32:
            @staticmethod
            def GlobalMemoryStatusEx(pointer):
                pointer._obj.ullTotalPhys = 32 * 1024**3
                return 1

        with patch.object(machine.os, "name", "nt"), \
             patch.object(machine.ctypes, "windll", type("Windll", (), {"kernel32": Kernel32()})(), create=True), \
             patch.object(machine.subprocess, "check_output") as child_process:
            self.assertEqual(machine._ram_gb(), 32.0)
            child_process.assert_not_called()

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

    def test_vram_parser_ignores_npu_not_available_row(self):
        self.assertEqual(machine._parse_vram_gb(["24512", "[N/A]"]), 23.94)

    def test_vram_parser_returns_unknown_without_numeric_gpu_row(self):
        self.assertIsNone(machine._parse_vram_gb(["[N/A]", ""]))

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
