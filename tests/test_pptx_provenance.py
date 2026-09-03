import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aeris_runtime import pptx_provenance as provenance


class PptxProvenanceTests(unittest.TestCase):
    def test_missing_private_artifacts_is_not_fake_verified_or_portable_failure(self):
        temp_root=provenance.ROOT/'.aeris/test-temp'
        temp_root.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temp_root) as directory:
            with patch.object(provenance,'ROOT',Path(directory)):
                result=provenance.verify()
            self.assertEqual(result['portable_provenance_contract']['state'],'VALID')
            self.assertEqual(result['result'],'LOCAL_ARTIFACT_NOT_PRESENT')
            self.assertFalse(result['provenance_valid'])
            self.assertEqual(result['capability_maturity'],'LOCAL_ARTIFACT_NOT_PRESENT')
            self.assertEqual(result['authenticode'],'NOT_SIGNED')
            self.assertFalse(result['trusted_signed_binary'])
            self.assertEqual(result['production_acceptance'],'NOT_RUN_NO_INPUT_PPTX')

    def test_actual_bytes_verified_and_existing_tamper_fails_even_with_missing_files(self):
        original=json.loads(provenance.PROVENANCE.read_text(encoding='utf-8-sig'))
        temp_root=provenance.ROOT/'.aeris/test-temp'
        temp_root.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temp_root) as directory:
            root=Path(directory); spec=copy.deepcopy(original)
            # Synthetic package bytes, never represented as a production EXE.
            source=b'synthetic source fixture\n'; executable=b'synthetic unsigned binary fixture'
            spec['source_root']='.aeris/review-sources/fixture'
            spec['source_files']={'README.md':hashlib.sha256(source).hexdigest().upper()}
            spec['executable'].update(path='.aeris/review-artifacts/fixture.exe',
                sha256=hashlib.sha256(executable).hexdigest().upper(),bytes=len(executable))
            source_path=root/spec['source_root']/'README.md'
            exe_path=root/spec['executable']['path']
            source_path.parent.mkdir(parents=True); exe_path.parent.mkdir(parents=True)
            source_path.write_bytes(source); exe_path.write_bytes(executable)
            contract_path=root/'provenance.json'; contract_path.write_text(json.dumps(spec),encoding='utf-8')
            with patch.object(provenance,'ROOT',root),patch.object(provenance,'PROVENANCE',contract_path):
                result=provenance.verify()
                self.assertEqual(result['result'],'PASS')
                self.assertTrue(result['provenance_valid'])
                self.assertFalse(result['trusted_signed_binary'])
                exe_path.write_bytes(b'tampered')
                self.assertEqual(provenance.verify()['result'],'FAIL')
                source_path.unlink()
                self.assertEqual(provenance.verify()['result'],'FAIL')

    def test_contract_rejects_escape_missing_hash_signed_and_production_claims(self):
        original=json.loads(provenance.PROVENANCE.read_text(encoding='utf-8-sig'))
        self.assertEqual(provenance.portable_contract(original)['state'],'VALID')
        variants=[]
        for value in ('../private','C:\\private','.aeris/../../private','not-private','\\\\server\\share'):
            spec=copy.deepcopy(original); spec['source_root']=value; variants.append(spec)
        for field,value in (('sha256','invalid'),('bytes',True),('authenticode','TRUSTED_SIGNED')):
            spec=copy.deepcopy(original); spec['executable'][field]=value; variants.append(spec)
        spec=copy.deepcopy(original); spec['acceptance']='PRODUCTION_ACCEPTED'; variants.append(spec)
        spec=copy.deepcopy(original); spec['source_files']={}; variants.append(spec)
        for spec in variants:
            with self.subTest(spec=spec):
                self.assertEqual(provenance.portable_contract(spec)['state'],'INVALID')


if __name__ == "__main__":
    unittest.main()
