from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class LiveUiContractTests(unittest.TestCase):
    def test_index_loads_live_refresh_after_main_app(self):
        html = (ROOT / "ui" / "web" / "index.html").read_text(encoding="utf-8")
        app = html.index('/assets/app.js')
        live = html.index('/assets/live-refresh.js')
        self.assertLess(app, live)

    def test_live_refresh_covers_all_mutable_control_plane_panels(self):
        js = (ROOT / "ui" / "web" / "live-refresh.js").read_text(encoding="utf-8")
        for fn in (
            "loadStatus",
            "loadProjects",
            "loadTasks",
            "loadRoles",
            "loadSkills",
            "loadWorkflows",
            "loadAudit",
        ):
            self.assertIn(fn, js)
        self.assertIn("setInterval(refreshLivePanels", js)
        self.assertIn("visibilitychange", js)
        self.assertIn("window.addEventListener('focus'", js)

    def test_frontend_assets_hot_reload_without_cache(self):
        js = (ROOT / "ui" / "web" / "live-refresh.js").read_text(encoding="utf-8")
        for asset in ("/", "/assets/app.js", "/assets/styles.css", "/assets/themes.css", "/assets/live-refresh.js"):
            self.assertIn(asset, js)
        self.assertIn("cache:'no-store'", js)
        self.assertIn("location.reload()", js)

    def test_dark_and_light_theme_urls_persist_across_spa_navigation(self):
        html = (ROOT / "ui" / "web" / "index.html").read_text(encoding="utf-8")
        js = (ROOT / "ui" / "web" / "app.js").read_text(encoding="utf-8")
        css = (ROOT / "ui" / "web" / "themes.css").read_text(encoding="utf-8")
        theme_init = (ROOT / "ui" / "web" / "theme-init.js").read_text(encoding="utf-8")
        # The theme bootstrap must live in an external file: controlplane's
        # CSP sends script-src 'self' with no 'unsafe-inline'/nonce, so an
        # inline <script>...</script> body is silently blocked by the
        # browser and never runs.
        self.assertIn('<script src="/assets/theme-init.js"></script>', html)
        self.assertIn("requestedTheme==='light'?'light':'dark'", theme_init)
        self.assertIn('id="themeToggle"', html)
        self.assertIn("?theme=${currentTheme()}", js)
        self.assertIn('data-theme="light"', css)
        self.assertIn("visual_baseline", js)


if __name__ == "__main__":
    unittest.main()
