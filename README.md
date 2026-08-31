# AERIS Local Computer Implementation

> **Executable local implementation repository for AERIS.**
>
> Canonical target / read-only SSOT: `https://github.com/Space653000/0_JN1_AERIS/tree/main`

## Repository contract

The two repositories have different authority:

```text
0_JN1_AERIS (main)
  = READ-ONLY target / architecture / research / UI / governance SSOT
                  │
                  │ clone / fetch / inspect / compare ONLY
                  ▼
0_JN1_AERIS_Local-computer-implementation
  = executable local runtime / code / tests / deployment / model adapters
                  │
                  ▼
Local computer
  = actual execution state, data, models, logs and evidence
```

**Codex must never write to `Space653000/0_JN1_AERIS`.** All implementation work belongs here or in a local clone of this repository.

## North-star runtime behavior

AERIS must remain usable when cloud AI or the internet is unavailable.

Supported runtime modes:

| Mode | Behavior |
|---|---|
| `offline` | Hard local-only mode. No cloud provider may be called. |
| `local` | Use local AI only. |
| `cloud` | Prefer cloud AI; if cloud fails, automatically fall back to local AI unless strict fallback is disabled. |
| `auto` | Prefer local AI; use configured cloud AI only when local is unavailable. |

Default local provider: **Ollama-compatible local HTTP API** on `127.0.0.1:11434`.

Cloud provider: **OpenAI-compatible HTTPS API** selected entirely through environment variables. This permits provider switching without changing AERIS domain code.

## One-click local deployment

### Windows

```powershell
git clone https://github.com/Space653000/0_JN1_AERIS_Local-computer-implementation.git
cd 0_JN1_AERIS_Local-computer-implementation
powershell -ExecutionPolicy Bypass -File .\INSTALL_AERIS_LOCAL.ps1
```

### Linux / macOS

```bash
git clone https://github.com/Space653000/0_JN1_AERIS_Local-computer-implementation.git
cd 0_JN1_AERIS_Local-computer-implementation
bash ./INSTALL_AERIS_LOCAL.sh
```

The installer uses only Python standard-library runtime dependencies. It creates `.venv`, local state directories, `.env`, and — when network + Git are available — a **read-only cached clone** of the canonical core target.

## Run

Windows:

```powershell
.\scripts\run.ps1 doctor
.\scripts\run.ps1 mode set local
.\scripts\run.ps1 chat "請說明目前 AERIS runtime 狀態"
```

Linux / macOS:

```bash
./scripts/run.sh doctor
./scripts/run.sh mode set local
./scripts/run.sh chat "請說明目前 AERIS runtime 狀態"
```

Direct Python interface:

```bash
python -m aeris_runtime doctor
python -m aeris_runtime mode show
python -m aeris_runtime mode set offline
python -m aeris_runtime chat "hello"
```

## Local AI prerequisite

AERIS does **not** bundle model weights into Git. Install or pre-stage a local inference server before disconnecting from the internet. The default configuration expects Ollama and a small local model:

```text
AERIS_LOCAL_BASE_URL=http://127.0.0.1:11434
AERIS_LOCAL_MODEL=qwen2.5:3b
```

Change the model in `.env` without changing source code.

## Cloud AI switching

Copy `.env.example` to `.env` and set:

```text
AERIS_CLOUD_BASE_URL=https://api.openai.com/v1
AERIS_CLOUD_MODEL=<cloud-model-id>
AERIS_CLOUD_API_KEY=<secret>
```

Secrets are local only and must never be committed.

## Core target synchronization

When online:

```powershell
.\scripts\sync-core.ps1
```

or:

```bash
./scripts/sync-core.sh
```

This creates/updates `.aeris/core-reference` from the canonical `0_JN1_AERIS/main`, records the SHA in `.aeris/state/core-target.json`, disables push on that cached clone, and installs a deny `pre-push` hook.

When offline, AERIS continues using the last cached core target and the tracked `core.lock.json` baseline.

## Codex packaging rule

A ZIP or clone of **this repository** must contain everything Codex needs to bootstrap the local runtime except:

- model weights;
- cloud API credentials;
- proprietary acoustic tools or licenses;
- large engineering datasets.

Codex should start by reading `AGENTS.md`, then run the installer, `doctor`, and tests before implementing new local capabilities.

## Important directories

```text
aeris_runtime/      minimal model router + CLI runtime
config/             provider/runtime configuration
docs/               local architecture and deployment rules
scripts/            bootstrap, run, sync and validation helpers
tests/              offline-safe unit tests
.aeris/             GENERATED local state/cache (gitignored)
data/               GENERATED/private local engineering data (gitignored)
logs/               GENERATED runtime logs (gitignored)
```

## Truth rule

```text
Core GitHub main = what AERIS should be.
This implementation repo = how AERIS is implemented locally.
Local state/evidence = what actually ran on this computer.
```

Never collapse these three layers into one.