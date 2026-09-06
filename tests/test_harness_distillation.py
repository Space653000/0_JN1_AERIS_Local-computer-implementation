import tempfile
import unittest
from pathlib import Path

from aeris_runtime.engineering.harness import Harness
from aeris_runtime.config import ROOT


class DistillationTests(unittest.TestCase):
    def setUp(self):
        temp_root=ROOT/'.aeris/test-temp'; temp_root.mkdir(parents=True,exist_ok=True)
        self.directory=tempfile.TemporaryDirectory(dir=temp_root)
        self.addCleanup(self.directory.cleanup)
        self.memory=Harness(Path(self.directory.name)/'memory.sqlite3')

    def test_empty_project_produces_no_invented_insight(self):
        result=self.memory.distill('empty')
        self.assertEqual(result['state'],'NO_SOURCE_EVENTS')
        self.assertEqual(self.memory.events('empty'),[])

    def test_distillation_is_source_derived_and_does_not_reingest_itself(self):
        failed=self.memory.append('P','FAILURE_LIBRARY',{
            'failure_mode':'clipping','root_cause':'ADC headroom exceeded',
            'next_discriminating_experiment':'repeat at -6 dB gain'},'R031')
        agreed=self.memory.append('P','CONSENSUS_DISAGREEMENT',{
            'decision':'ACCEPT','unresolved':[]},'R033')
        lesson=self.memory.append('P','LESSON_MEMORY',{
            'lesson':'A lower gain distinguishes overload from capsule distortion'},'R031')
        first=self.memory.distill('P')
        self.assertEqual(first['failure_count'],1)
        self.assertEqual(first['failure_clusters'][0]['failure_mode'],'clipping')
        self.assertEqual(first['root_cause_observations'][0]['value'],'ADC headroom exceeded')
        self.assertEqual(first['next_discriminating_experiments'][0]['value'],'repeat at -6 dB gain')
        self.assertEqual(first['lessons'][0]['source_event_hashes'],[lesson['event_hash']])
        count=len(self.memory.events('P'))
        second=self.memory.distill('P')
        self.assertEqual(second['state'],'NO_NEW_SOURCE_EVENTS')
        self.assertEqual(len(self.memory.events('P')),count)
        self.assertEqual(second['source_set_sha256'],first['source_set_sha256'])
        self.assertEqual(set(first['source_event_hashes']),{failed['event_hash'],agreed['event_hash'],lesson['event_hash']})
        self.assertTrue(self.memory.verify()['valid'])


if __name__=='__main__': unittest.main()
