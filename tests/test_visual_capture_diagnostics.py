"""Visual mismatch diagnostics locate changes without printing private text."""
import json
import unittest
from tests.browser_visual_accessibility import _dom_fingerprints


class VisualCaptureDiagnosticsTests(unittest.TestCase):
    def test_changed_nested_text_changes_only_its_own_ancestor_digests(self):
        a=_dom_fingerprints('<main id="main"><b id="state">PENDING</b><input id="input"><i id="stable">fixed</i></main>')
        b=_dom_fingerprints('<main id="main"><b id="state">READY</b><input id="input"><i id="stable">fixed</i></main>')
        self.assertEqual({k for k in a if a[k]!=b[k]},{'main','state'})
        self.assertEqual(a,_dom_fingerprints('<main id="main"><b id="state">PENDING</b><input id="input"><i id="stable">fixed</i></main>'))

    def test_private_text_is_not_in_the_diagnostic_manifest(self):
        result=_dom_fingerprints('<div id="status">private-customer-observation</div>')
        self.assertEqual(set(result),{'status'})
        self.assertNotIn('private-customer-observation',json.dumps(result))
        self.assertEqual(len(result['status']),64)


if __name__=='__main__':unittest.main()
