import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import aeris_runtime.evidence as evidence
import aeris_runtime.reproduction as reproduction
import aeris_runtime.skills_runtime as skills_runtime


class ReproductionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.inputs = root / "inputs"
        self.inputs.mkdir()
        self.csv = self.inputs / "fr.csv"
        self.csv.write_text("frequency_hz,level_db\n100,90\n200,91\n1000,89\n", encoding="utf-8")
        self.old_evidence = evidence.EVIDENCE_ROOT
        self.old_repro = reproduction.REPRO_ROOT
        self.old_allowed = skills_runtime._ALLOWED_INPUT_ROOTS
        evidence.EVIDENCE_ROOT = root / "evidence"
        reproduction.REPRO_ROOT = root / "reproduction"
        skills_runtime._ALLOWED_INPUT_ROOTS = (self.inputs,)

    def tearDown(self):
        evidence.EVIDENCE_ROOT = self.old_evidence
        reproduction.REPRO_ROOT = self.old_repro
        skills_runtime._ALLOWED_INPUT_ROOTS = self.old_allowed
        self.tmp.cleanup()

    @patch("aeris_runtime.evidence.append_event")
    def test_inline_engineering_replay_and_tamper_rejection(self, _audit):
        from aeris_runtime.engineering import catalog, reporting
        skill='thermal-rc'
        params=catalog.definitions()[skill]['fixture']['input']
        run_id='RUN-ENGINEERING-REPRO'
        evidence.create_bundle('TASK-1','test',run_id=run_id,method_snapshot={'skill_id':skill})
        result=catalog.execute(skill,params)
        root=evidence.bundle_dir(run_id)
        (root/'processed'/'skill_result.json').write_bytes(catalog.canonical(result))
        reporting.write_artifacts(root,params,result,{'source_kind':'SYNTHETIC'})
        evidence.seal_bundle(run_id,'test')
        self.assertEqual(reproduction.reproduce_run(run_id)['result'],'PASS')
        self.assertIn('SYNTHETIC',(root/'report.md').read_text(encoding='utf-8'))
        (root/'raw'/'engineering-input.json').write_text('{}',encoding='utf-8')
        self.assertNotEqual(reproduction.reproduce_run(run_id)['result'],'PASS')

    @patch("aeris_runtime.evidence.append_event")
    def test_replay_matches_even_when_transport_path_changes(self, _audit):
        run_id = "RUN-REPRO-1"
        params = {"low_hz": 100.0, "high_hz": 1000.0}
        evidence.create_bundle(
            "TASK-1",
            "test",
            run_id=run_id,
            input_paths=[self.csv],
            method_snapshot={"skill_id": "frequency-response-analysis", "parameters": params},
        )
        expected = skills_runtime.run_skill("frequency-response-analysis", {"input_path": str(self.csv), **params})
        root = evidence.bundle_dir(run_id)
        (root / "processed" / "skill_result.json").write_text(json.dumps(expected, indent=2) + "\n", encoding="utf-8")
        evidence.seal_bundle(run_id, "test")

        report = reproduction.reproduce_run(run_id)
        self.assertEqual(report["result"], "PASS")
        self.assertTrue(report["deterministic_result_match"])
        self.assertNotEqual(report["expected"]["input"], report["actual"]["input"])
        self.assertEqual(report["canonical_expected"], report["canonical_actual"])


if __name__ == "__main__":
    unittest.main()
