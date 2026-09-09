import json
import tempfile
import unittest
from pathlib import Path
from aeris_runtime.config import ROOT
from aeris_runtime.supervision_chain import publish, sha


class SupervisionChainTests(unittest.TestCase):
    def setUp(self):
        base = ROOT/'.aeris/test-temp'
        base.mkdir(parents=True,exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=base)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_unique_linked_immutable_triples(self):
        first = publish(self.root,'first',{})
        before = {p: Path(p).read_bytes() for p in first['paths']}
        second = publish(self.root,'second',{})
        self.assertEqual(second['snapshot']['snapshot_id'],'S0002')
        self.assertEqual(second['snapshot']['previous_snapshot_hash'],sha(before[first['paths'][1]]))
        self.assertEqual(second['snapshot']['chain_state'],'LINKED')
        for path,data in before.items(): self.assertEqual(Path(path).read_bytes(),data)

    def test_duplicate_legacy_ids_are_chain_unknown(self):
        for name in ('one','two'):
            (self.root/f'AERIS_SUPERVISION_SNAPSHOT_S0001_{name}.json').write_text('{}')
        result = publish(self.root,'report',{})['snapshot']
        self.assertEqual(result['snapshot_id'],'S0002')
        self.assertEqual(result['chain_state'],'CHAIN_UNKNOWN')
        self.assertIsNone(result['previous_snapshot'])

    def test_tampered_predecessor_is_not_verified(self):
        first = publish(self.root,'first',{})
        path = Path(first['paths'][1])
        path.write_text(json.dumps(json.loads(path.read_text()) | {'altered':True}))
        self.assertEqual(publish(self.root,'next',{})['snapshot']['chain_state'],'CHAIN_UNKNOWN')

    def test_concurrent_or_abandoned_writer_blocks(self):
        (self.root/'.snapshot-publication.lock').write_text('existing writer')
        with self.assertRaises(FileExistsError): publish(self.root,'report',{})

    def test_older_tamper_is_not_hidden_by_valid_latest_snapshot(self):
        first = publish(self.root,'first',{})
        publish(self.root,'second',{})
        Path(first['paths'][0]).write_text('tampered older report')
        self.assertEqual(publish(self.root,'third',{})['snapshot']['chain_state'],'CHAIN_UNKNOWN')
