# AERIS Local UI

The implementation now ships an executable same-origin local control plane on the loopback supervisor port.

Canonical surfaces:

- `http://127.0.0.1:8765/` — Dashboard
- `http://127.0.0.1:8765/workspace` — Workspace
- `http://127.0.0.1:8765/services` — Services / roles / Knowledge / Audit
- `/api/v1/*` — local JSON control APIs

The UI is dependency-free HTML/CSS/JavaScript so it remains portable and offline-capable. It reads live local backend state; it does not manufacture HEALTHY/COMPLETE states. The 100 seats are visible and callable through a baseline local-AI role contract, while domain maturity remains governed by `config/maturity.json` and Evidence/Verification gates.

Visual direction follows the read-only Core/Kairos baseline. Future visual refinement must not weaken backend truth boundaries.
