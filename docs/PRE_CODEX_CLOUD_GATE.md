# AERIS Pre-Codex Cloud Gate

The local Codex cycle is allowed only after cloud-reproducible work has been closed on GitHub.

Required before telling the Human to enter Codex:

- canonical Core main governance CI is green and Core SHA is aligned;
- Implementation PR CI passes on Windows 2025 and Ubuntu 24.04;
- the repair is merged to `main`;
- merge-after-main CI passes on Windows 2025 and Ubuntu 24.04;
- zero-cost / no-Claude default deployment gates pass;
- no known P0/P1/P2 cloud-reproducible blocker remains;
- no known stale-truth contradiction remains that would cause local Codex to rediscover or redo cloud-fixable work.

This gate does **not** claim whole-company completion. Real machine inference, reboot/persistence, hard-offline, machine-specific resource qualification, physical measurement/calibration, licensed professional tools, release signing and Human R3/R4 approval remain outside cloud-only proof where applicable.
