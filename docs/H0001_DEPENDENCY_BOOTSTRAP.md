# Root-scoped free engineering dependencies

CI run 199 passed the Windows host-Python unit suite but the one-click installer
then created an empty `.venv` and ran engineering tests without NumPy. Host
packages are not proof that the installed interpreter can execute capabilities.

Both one-click entrypoints and both developer bootstrap entrypoints now invoke
`scripts/bootstrap-engineering.py` with their own `.venv` interpreter before
tests. The helper rejects system Python, checks actual imports and exact versions,
uses pip isolated/non-interactive/binary-wheel-only mode, and restricts pip cache
and temporary build/install files to `.aeris` inside that checkout.

`--mode offline` never queries a package index or falls back to online mode.
Preinstall the pinned packages, or stage platform/Python-compatible free wheels
and their required dependencies under `portable_assets/wheels`. Missing compatible
wheels fail closed. No source compilation or paid package is introduced.

An independent review found that an assertion-only version probe could be removed
by `PYTHONOPTIMIZE=1`. A missing-package regression reproduced that false-ready
result. The probe now explicitly imports and exits nonzero on version mismatch;
the optimization setting cannot remove those checks. Seven focused tests pass.

Package availability is not licensed-professional, physical-measurement, role L3,
company-opening, offline-model-inference or full installer acceptance. CI must
still execute the actual clean-checkout installer smoke on Windows and Ubuntu.
