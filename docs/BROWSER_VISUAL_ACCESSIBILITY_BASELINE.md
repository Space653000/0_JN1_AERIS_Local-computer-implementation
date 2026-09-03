# AERIS Browser Visual / Accessibility Baseline

## Scope

This baseline adds a real-browser CI gate for the local Dashboard, Workspace and Services routes on Windows 2025 and Ubuntu 24.04.

The gate verifies:

- fixed-viewport headless browser screenshot creation at 1440×1000;
- valid non-trivial PNG output;
- same-route bit-exact screenshot repeatability within the same CI environment;
- visually distinct screenshots for Dashboard, Workspace and Services;
- basic accessibility semantics for language, primary navigation, live status and key form/search controls.

## Truth boundary

This is **not** a cross-version pixel-golden visual regression suite, not WCAG conformance certification, and not proof that every supported end-user display/browser/font stack is visually identical.

The `browser_e2e_visual_regression` local fixed-viewport, same-browser/environment scope is TESTED. This does not claim cross-browser or cross-version pixel identity; those release scopes require an explicitly declared support matrix and Human acceptance.
