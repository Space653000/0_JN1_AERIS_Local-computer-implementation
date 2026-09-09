import json
import shutil
import tempfile
import unittest
from pathlib import Path

from aeris_runtime.config import ROOT
from aeris_runtime.blueprint_compatibility import (
    GOVERNANCE,
    POINTERS,
    TAG,
    TARGET,
    validate,
)


ACTIVE_FILES = [
    'core.lock.json',
    'config/blueprint_compatibility.json',
    'config/core_alignment.json',
    'config/autopilot.json',
    'company/company.manifest.json',
    'config/maturity.json',
    'config/review_gate.v1.json',
]


class BlueprintCompatibilityTests(unittest.TestCase):
    def setUp(self):
        base = ROOT / '.aeris/test-temp'
        base.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=base)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

        for relative in ACTIVE_FILES:
            source = ROOT / relative
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

        shutil.copytree(ROOT / 'config/blueprint', self.root / 'config/blueprint')
        for index in range(1, 101):
            path = self.root / f'company/capabilities/R{index:03d}/capability.json'
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps({
                'canonical_core_sha': TARGET,
                'source_generation_core_sha': '82f4554623b2d87185dac39a3b93194af7dd5275',
            }))

    def mutate(self, relative, keys, value):
        path = self.root / relative
        data = json.loads(path.read_text(encoding='utf-8-sig'))
        cursor = data
        for key in keys[:-1]:
            cursor = cursor[key]
        cursor[keys[-1]] = value
        path.write_text(json.dumps(data))

    def test_exact_candidate_consumers_are_internally_consistent(self):
        result = validate(self.root)
        self.assertFalse(result['four_way_aligned'])
        self.assertFalse(result['runtime_cutover'])
        self.assertTrue(all(row['current'] == TARGET for row in result['pointers']))
        self.assertTrue(all(row['current'] == GOVERNANCE for row in result['governance']))

    def test_mixed_core_versions_rejected(self):
        self.mutate('core.lock.json', ('baseline_sha',), 'old')
        with self.assertRaisesRegex(ValueError, 'mixed Core'):
            validate(self.root)

    def test_old_governance_revision_rejected(self):
        self.mutate(
            'config/core_alignment.json',
            ('review_alignment', 'architecture_version'),
            '0.6.0-review.1',
        )
        with self.assertRaisesRegex(ValueError, 'governance'):
            validate(self.root)

    def test_old_autopilot_review_revision_rejected(self):
        self.mutate('config/autopilot.json', ('review_revision',), '2026-09-07.1')
        with self.assertRaisesRegex(ValueError, 'governance'):
            validate(self.root)

    def test_legacy_sol_hold_cannot_be_active_admission_state(self):
        self.mutate(
            'config/autopilot.json',
            ('admission_precondition', 'state'),
            'HOLD_FOR_SOL_RED_TEAM',
        )
        with self.assertRaisesRegex(ValueError, 'Autopilot governance'):
            validate(self.root)

    def test_unbounded_full_build_truth_rule_rejected(self):
        self.mutate(
            'config/autopilot.json',
            ('truth_rule',),
            'Two canonical URLs authorize Full-Build.',
        )
        with self.assertRaisesRegex(ValueError, 'Autopilot governance'):
            validate(self.root)

    def test_company_stale_hold_rejected(self):
        self.mutate(
            'company/company.manifest.json',
            ('review_hold',),
            'HOLD_FOR_SOL_RED_TEAM',
        )
        with self.assertRaisesRegex(ValueError, 'company manifest governance'):
            validate(self.root)

    def test_incompatible_schema_blocked(self):
        path = self.root / 'config/blueprint/aeris.review.json'
        data = json.loads(path.read_text())
        data['schema_version'] = 2
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'BLOCKED'):
            validate(self.root)

    def test_caller_compatible_label_has_no_authority(self):
        with self.assertRaisesRegex(ValueError, 'BLOCKED'):
            validate(self.root, [{'schema_version': 3, 'state': 'COMPATIBLE'}])

    def test_runtime_old_sha_aligned_rejected(self):
        with self.assertRaisesRegex(ValueError, 'old runtime'):
            validate(
                self.root,
                runtime={
                    'aligned': True,
                    'core_sha': 'old',
                    'implementation_sha': 'old',
                    'candidate_sha': 'new',
                },
            )

    def test_candidate_does_not_imply_four_way_alignment(self):
        self.assertFalse(validate(self.root)['four_way_aligned'])

    def test_one_old_role_pointer_rejects_entire_candidate(self):
        path = self.root / 'company/capabilities/R100/capability.json'
        path.write_text(json.dumps({
            'canonical_core_sha': 'old',
            'source_generation_core_sha': '82f4554623b2d87185dac39a3b93194af7dd5275',
        }))
        with self.assertRaisesRegex(ValueError, 'mixed Core Role Pack'):
            validate(self.root)

    def test_role_pointer_migration_does_not_erase_generation_provenance(self):
        path = self.root / 'company/capabilities/R100/capability.json'
        path.write_text(json.dumps({'canonical_core_sha': TARGET}))
        with self.assertRaisesRegex(ValueError, 'source-generation provenance'):
            validate(self.root)


if __name__ == '__main__':
    unittest.main()
