"""The full portable matrix must have time to run every non-weakened gate."""
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]


class CIRuntimeBudgetTests(unittest.TestCase):
    def test_job_budget_covers_repeated_entrypoint_acceptance(self):
        workflow=(ROOT/'.github/workflows/ci.yml').read_text(encoding='utf-8')
        match=re.search(r'^\s*timeout-minutes:\s*(\d+)\s*$',workflow,re.MULTILINE)
        self.assertIsNotNone(match)
        # The 434-test fixed-source suite is now about 20 minutes per OS before
        # installer, Autopilot, wrapper and portable-package smoke gates run.
        # A 50-minute job repeatedly cancelled otherwise-successful tail gates.
        self.assertGreaterEqual(int(match.group(1)),75)
        # These remain distinct acceptance paths; timeout repair must not delete them.
        for gate in ('Unit tests including Core alignment privacy trust acoustics watchdog reproduction',
                     'one-click installer smoke without external runtime installation',
                     'full Autopilot entrypoint CI smoke',
                     'Optional Claude-wrapper CI smoke (no Claude/token invocation)',
                     'portable package smoke with SBOM/provenance and external digest'):
            self.assertIn(gate,workflow)


if __name__=='__main__':unittest.main()
