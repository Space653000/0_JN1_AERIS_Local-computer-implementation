"""A Skill Golden result is not a role-domain acceptance result."""
import unittest
import copy
import json
import shutil
import tempfile
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

from aeris_runtime import evidence, audit
from aeris_runtime.engineering import factory, harness


class MaturityBoundaryTests(unittest.TestCase):
    def test_shared_skill_evidence_never_grants_role_l3(self):
        result = factory.matrix()
        # H0001 starts with no separate role-domain acceptance implementation.
        # Historical labels and valid shared Skill bundles cannot establish L3.
        self.assertEqual(result['maturity_counts']['L3'], 0)
        self.assertEqual(result['maturity_counts']['L4'], 0)

    def test_shared_skill_evaluation_without_professional_boundary_cannot_grant_l2(self):
        # Shared synthetic fixtures alone are not the missing professional
        # boundary evidence. This invariant survives future Role Suite support.
        pack=factory.load_pack('R009')
        self.assertEqual(factory.shared_skill_maturity(pack),'L1')

    def test_real_sealed_skill_run_capped_and_cross_role_bundle_rejected(self):
        temp_root=factory.ROOT/'.aeris/test-temp'; temp_root.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temp_root) as directory, ExitStack() as stack:
            root=Path(directory); packs=root/'packs'; state=root/'state'
            for role in ('R009','R010'):
                shutil.copytree(factory.PACKS/role,packs/role)
            for module,name,value in ((factory,'PACKS',packs),(factory,'STATE',state),
                    (evidence,'EVIDENCE_ROOT',root/'evidence'),(harness,'DB',root/'memory.sqlite3'),
                    (audit,'AUDIT_DIR',root/'audit'),(audit,'AUDIT_FILE',root/'audit/audit.jsonl'),
                    (audit,'LOCK_FILE',root/'audit/.lock')):
                stack.enter_context(patch.object(module,name,value))
            first=factory.evaluate_role('R009'); second=factory.evaluate_role('R010')
            self.assertEqual(first['level'],'L1')
            matrix={r['id']:r for r in factory.matrix()['roles']}
            self.assertEqual(matrix['R009']['level'],'L1')
            self.assertEqual(matrix['R010']['level'],'L1')
            self.assertEqual(matrix['R009']['coverage']['evaluated'],len(factory.load_pack('R009')['required_skills']))
            # A valid but different role's seal must not satisfy the target.
            index=state/'evaluations/R009.json'
            factory.write(index,{**first,'run_id':second['run_id'],'level':'L4'})
            self.assertEqual({r['id']:r for r in factory.matrix()['roles']}['R009']['coverage']['evaluated'],0)
            factory.write(index,first)
            # Existing valid evidence produced by a different predicate is stale.
            sealed_path=evidence.bundle_dir(first['run_id'])/'processed/capability-evaluation.json'
            record=json.loads(sealed_path.read_text())
            record['acceptance_engine_sha256']='0'*64
            replacement=evidence.create_bundle('SYNTHETIC-STALE-PREDICATE','test')
            folder=evidence.bundle_dir(replacement['run_id'])
            factory.write(folder/'processed/capability-evaluation.json',record)
            evidence.seal_bundle(replacement['run_id'],'test')
            factory.write(index,{**first,'run_id':replacement['run_id']})
            self.assertEqual({r['id']:r for r in factory.matrix()['roles']}['R009']['coverage']['evaluated'],0)

    def test_no_empty_checks_or_missing_negative_evidence_can_grant_execution(self):
        pack=factory.load_pack('R009'); runs=[]
        for skill in pack['required_skills']:
            fixture=factory.fixture_for('R009',skill)
            runs.append({'skill_id':skill,'input':fixture['input'],
                         'output':factory.catalog.execute(skill,fixture['input']),
                         'evaluation':factory.catalog.evaluate(skill)})
        self.assertTrue(factory.valid_skill_runs(runs,pack))
        self.assertFalse(factory.valid_skill_runs([],pack))
        for field,value in (('checks',[]),('negative_pass',False),('case_sha256','0'*64)):
            altered=copy.deepcopy(runs); altered[0]['evaluation'][field]=value
            self.assertFalse(factory.valid_skill_runs(altered,pack))


if __name__ == '__main__':
    unittest.main()
