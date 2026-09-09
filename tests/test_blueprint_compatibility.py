import json
import tempfile
import unittest
import shutil
from pathlib import Path
from aeris_runtime.config import ROOT
from aeris_runtime.blueprint_compatibility import POINTERS, TARGET, TAG, validate


class BlueprintCompatibilityTests(unittest.TestCase):
    def setUp(self):
        base = ROOT/'.aeris/test-temp'
        base.mkdir(parents=True,exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=base)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for path, keys in POINTERS.items():
            obj = value = {}
            for key in keys[:-1]: value[key] = {}; value = value[key]
            value[keys[-1]] = TARGET
            p = self.root/path
            p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text(json.dumps(obj))
        (self.root/'core.lock.json').write_text(json.dumps({'baseline_sha':TARGET,'tag':TAG,'canonical_roles':{'core_commit':TARGET}}))
        shutil.copytree(ROOT/'config/blueprint',self.root/'config/blueprint')
        for i in range(1,101):
            path=self.root/f'company/capabilities/R{i:03d}/capability.json'
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps({'canonical_core_sha':TARGET}))

    def test_mixed_core_versions_rejected(self):
        (self.root/'core.lock.json').write_text(json.dumps({'baseline_sha':'old'}))
        with self.assertRaisesRegex(ValueError,'mixed Core'):
            validate(self.root)

    def test_incompatible_schema_blocked(self):
        path=self.root/'config/blueprint/aeris.review.json'
        data=json.loads(path.read_text()); data['schema_version']=2
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError,'BLOCKED'):
            validate(self.root)

    def test_caller_compatible_label_has_no_authority(self):
        with self.assertRaisesRegex(ValueError,'BLOCKED'):
            validate(self.root,[{'schema_version':3,'state':'COMPATIBLE'}])

    def test_runtime_old_sha_aligned_rejected(self):
        with self.assertRaisesRegex(ValueError,'old runtime'):
            validate(self.root,runtime={'aligned':True,'core_sha':'old','implementation_sha':'old','candidate_sha':'new'})

    def test_candidate_does_not_imply_four_way_alignment(self):
        self.assertFalse(validate(self.root)['four_way_aligned'])

    def test_one_old_role_pointer_rejects_entire_candidate(self):
        (self.root/'company/capabilities/R100/capability.json').write_text(json.dumps({'canonical_core_sha':'old'}))
        with self.assertRaisesRegex(ValueError,'mixed Core Role Pack'):
            validate(self.root)
