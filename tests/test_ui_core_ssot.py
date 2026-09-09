import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


class UiCoreSsotTests(unittest.TestCase):
    def test_three_pages_use_core_visual_assets_and_live_api_binding(self):
        for name,page in (("dashboard.html","dashboard"),("workspace.html","workspace"),("services.html","services")):
            text=(ROOT/"ui"/"web"/name).read_text(encoding="utf-8")
            self.assertIn(f'data-page="{page}"',text)
            self.assertIn('/assets/aeris.css',text)
            self.assertIn('/assets/aeris-theme.js',text)
            self.assertIn('/assets/aeris-live.js',text)
        js=(ROOT/"ui"/"web"/"aeris-live.js").read_text(encoding="utf-8")
        self.assertIn("setInterval(refresh,10000)",js)
        self.assertIn("visibilitychange",js)
        self.assertIn("addEventListener('focus',refresh)",js)
        self.assertIn("location.reload()",js)

    def test_core_assets_are_served_directly_from_read_only_cache(self):
        source=(ROOT/"aeris_runtime"/"controlplane.py").read_text(encoding="utf-8")
        self.assertIn('core_assets = {"aeris.css", "aeris-theme.js"}',source)
        self.assertIn('ROOT / ".aeris" / "core-reference" / rel',source)


if __name__ == "__main__": unittest.main()
