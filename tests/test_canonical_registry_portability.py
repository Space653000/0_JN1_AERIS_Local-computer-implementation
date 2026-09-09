import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aeris_runtime.engineering import factory
from aeris_runtime.engineering.canonical_registry import load, validate_source


class CanonicalRegistryPortabilityTests(unittest.TestCase):
    def test_clean_checkout_without_private_core_cache_resolves_roles(self):
        temp_root=factory.ROOT/'.aeris'/'test-temp'
        temp_root.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temp_root) as directory:
            root=Path(directory)
            for rel in ('core.lock.json','company/organization/roles.v1.json'):
                (root/rel).parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(factory.ROOT/rel,root/rel)
            self.assertFalse((root/'.aeris').exists())
            with patch.object(factory,'ROOT',root):
                roles=factory.canonical_roles()
                self.assertEqual(len(roles),100)
                self.assertEqual(roles[47]['name'],'TWS Earbuds')
                path=root/'company/organization/roles.v1.json'
                registry=json.loads(path.read_text(encoding='utf-8-sig'))
                registry['groups']['Product Chiefs'][3]='Forged Chief'
                path.write_text(json.dumps(registry),encoding='utf-8')
                with self.assertRaisesRegex(ValueError,'digest|drift'):
                    factory.canonical_roles()

    def test_pin_drift_and_order_drift_fail_closed_without_cache(self):
        temp_root=factory.ROOT/'.aeris/test-temp'; temp_root.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temp_root) as directory:
            root=Path(directory)
            for rel in ('core.lock.json','company/organization/roles.v1.json'):
                (root/rel).parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(factory.ROOT/rel,root/rel)
            lock_path=root/'core.lock.json'; lock=json.loads(lock_path.read_text(encoding='utf-8-sig'))
            pin=lock['canonical_roles'].copy()
            for field,value in (('core_commit','0'*40),('ordered_groups_sha256','0'*64),('extraction','UNREVIEWED')):
                lock['canonical_roles']={**pin,field:value}
                lock_path.write_text(json.dumps(lock),encoding='utf-8')
                with self.assertRaises(ValueError): load(root)
            lock['canonical_roles']=pin; lock_path.write_text(json.dumps(lock),encoding='utf-8')
            path=root/'company/organization/roles.v1.json'; registry=json.loads(path.read_text())
            registry['groups']=dict(reversed(list(registry['groups'].items())))
            path.write_text(json.dumps(registry),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'digest'): load(root)

    def test_present_source_cannot_silently_drift(self):
        pin=json.loads((factory.ROOT/'core.lock.json').read_text(encoding='utf-8-sig'))['canonical_roles']
        registry=json.loads((factory.ROOT/'company/organization/roles.v1.json').read_text())
        with self.assertRaisesRegex(ValueError,'source digest'):
            validate_source(b'window.AERIS_ROLE_GROUPS={};',pin,registry['groups'])


if __name__=='__main__': unittest.main()
