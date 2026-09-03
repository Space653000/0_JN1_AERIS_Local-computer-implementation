# Local completion evidence boundaries

The original local-software inventory contained 10 gaps. Final real-machine
checks exposed two additional defects, for 12 total. One installer defect on
2026-09-03 was that invoking
`ollama list` caused Windows Ollama desktop autostart, inherited log handles and
an update check. The attempt was interrupted; its log remains in
`.aeris/evidence/completion-autopilot-720309a.log` and is not PASS evidence.
The updater reported an already-downloaded bundle outside the installation
root. That existing directory was neither cleaned nor altered by the repair.

Model availability now uses bounded loopback HTTP probes, including a negative
test for an absent server/model. If startup is necessary, the launcher invokes
`ollama.exe serve` directly and confines its child USERPROFILE, AppData, model,
temporary and log paths to `.aeris`. Existing model API access is read-only
during installation when the requested model is already available.

Windows regression: `tests/windows/test-ollama-api.ps1`.
Child-process isolation regression: `tests/test_ollama_service.py`.
CI configuration includes the Windows regression; this pass does not execute
remote CI because the Human prohibits GitHub writes/pushes.

The historical Scheduled Task result `0x800710E0` means the operator or
administrator refused the request. That code alone does not identify which
task policy caused the refusal. The local repair preserves a matching running
task, avoids duplicate starts, resolves the base Python executable and retries
only when the task is not running. Current task state and historical result are
reported separately. Successful current-session operation is not proof of
pre-login, reboot or logoff persistence.

Completion evidence must match the current implementation commit. Screenshot
SHA-256 is recomputed, and stale browser, monitor or acceptance reports fail
closed. Local zero software gaps is bounded by the explicit inventory and
tested baselines; it does not assert commercial release, licensed professional
tool equivalence, expert validation or physical calibration.

The other defect was a still-running Python supervisor from the previous day:
disk changes and a new Git commit had not reloaded its imported modules.
`/health` now reports the commit captured at module import and process ID.
The completion gate rejects an older or unreported live revision even when
browser reports and on-disk files match the new commit.
