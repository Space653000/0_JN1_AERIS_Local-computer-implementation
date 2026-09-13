# AERIS Access Control — public intro page vs. locked operational system

## Why this exists

The plan going forward: a public "intro" website (status, features, blueprint
overview — no live operational data) that links back to the locally-running
AERIS instance. Only the intro page is meant to be openly reachable; every
operational page and API — dashboard, workspace, progress center, activity
log, services, and all `/api/v1/*` business endpoints — must require the
owner to sign in first, regardless of whether the request originates from
the loopback browser or a future remote connect-back path.

## What's public vs. what's locked

**Public, no session required:**
- `/` — the intro page (`ui/web/intro.html`): describes AERIS's purpose,
  the G0-G5 verification model, the 100-role capability library, and the
  P0-P6 blueprint phases in prose. Deliberately does not fetch or embed any
  live `/api/v1/*` data.
- `/login` — the sign-in page.
- `POST /api/v1/auth/login`, `GET /api/v1/auth/status` — needed for the
  login page itself to function.
- `/assets/*` — static CSS/JS. These are just presentation code, not
  operational data; serving them publicly is no different from anyone being
  able to view a public site's page source.

**Everything else requires a valid session with the right permission:**
`/dashboard`, `/workspace`, `/progress`, `/activity`, `/services`, `/admin`,
and every `/api/v1/*` endpoint other than the two auth ones above. An
unauthenticated request to an HTML page gets a 302 redirect to `/login`; an
unauthenticated request to an API endpoint gets a 401 JSON error; a
*signed-in* request to a page or mutating action the account was not
granted gets a 403. See `aeris_runtime/controlplane.py`'s
`PUBLIC_GET_PATHS`/`PUBLIC_POST_PATHS`/`PROTECTED_UI_PAGE_PERMISSIONS`/
`MUTATING_API_PREFIXES` for the exact allowlist and permission map —
everything not explicitly listed there is locked by default, not the other
way around.

## Accounts: one owner, any number of granted accounts

There is exactly **one owner**, set locally once:

```bash
python -m aeris_runtime auth set-credentials
```

This prompts interactively (`getpass`, so the password is never echoed to
the terminal or written to any log) and **wipes every other account and
session** — it's the local, filesystem-level reset path, not something to
run casually once other accounts exist. Only a salted PBKDF2-HMAC-SHA256
hash (310,000 iterations) is ever persisted, to
`.aeris/state/auth_credentials.json` — a path already covered by the
repository's blanket `.aeris/` `.gitignore` rule, so it can never be
accidentally committed. The plaintext password is never seen, stored, or
transmitted by anything other than the browser form and this one local
prompt.

The owner has every permission, including managing accounts (`admin`), and
cannot be removed or demoted through the API — only by re-running
`set-credentials`.

**The owner can grant additional accounts**, each scoped to an explicit
subset of pages/actions, two ways:

- The `/admin` page (owner-only; a "帳號管理" link appears in the sidebar
  for the owner on every protected page): add a username/password, tick
  which pages it can see, and optionally whether it can execute skills or
  create tasks (`capabilities_execute` — the one grantable permission that
  covers mutating actions, not just viewing).
- The CLI: `python -m aeris_runtime auth grant-user <username> --permissions
  dashboard progress` (prompts for the password via `getpass`);
  `auth list-users`; `auth revoke-user <username>`.

A granted account can **never** hold `admin` — it isn't in the grantable
permission set at all (`aeris_runtime/auth.py`'s `GRANTABLE_PERMISSIONS`),
so there's no checkbox to misconfigure into an accidental second owner.

Check what's currently configured:

```bash
python -m aeris_runtime auth status
```

## How sessions work

- A successful login sets an `HttpOnly`, `SameSite=Strict` cookie
  (`aeris_session`) valid for 12 hours.
- Sessions are held **in memory only**, never persisted to disk. Restarting
  the local supervisor — which `AERIS_START.bat`/`AERIS_START.ps1` does on
  every run — invalidates every session, so you sign in again after each
  restart. For a single-owner system restarted often, this trade favors a
  smaller blast radius (a leaked session-store file would otherwise grant
  standing access) over the minor inconvenience of re-logging in.
- Repeated failed logins trigger a temporary lockout (8 failures within a
  5-minute window) — see `aeris_runtime/auth.py`'s `MAX_FAILED_ATTEMPTS`/
  `LOCKOUT_WINDOW_S`.

## What this does *not* cover yet (genuinely open, not silently ignored)

- **No real rate limiting or WAF in front of a future public tunnel.** The
  lockout in `auth.py` is a basic in-process safeguard, not a substitute for
  a reverse proxy with real abuse protection if this is ever exposed to the
  public internet (the user's stated future plan: a public intro site that
  connects back to the local instance). Building that tunnel/proxy layer is
  a separate, larger decision — not attempted here.
- **No HTTPS/TLS.** The control plane serves plain HTTP on loopback. The
  session cookie does not carry the `Secure` flag because there is no TLS
  to require it under. If a public-facing tunnel is added later, that
  layer needs to terminate TLS and this cookie should be revisited to add
  `Secure`.
- **Permission granularity stops at "which pages" plus one "can execute"
  flag.** There's no per-role-seat or per-skill permission (e.g. "can see
  R073 but not R012"); a granted account either can or can't execute/create
  anything at all via `capabilities_execute`. Finer-grained permissions
  were not requested and would be speculative scope beyond what's asked.
