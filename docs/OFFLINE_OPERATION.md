# Offline Operation Policy

## What "offline-capable" means

AERIS can continue supported workflows without internet access **only when every dependency required by that workflow already exists locally and passes acceptance**.

A cloud model cannot operate while the network is unavailable. Local AI is the continuity layer; it is not evidence that the rest of the AERIS engineering company is complete.

## Required pre-staged assets

Before deliberate disconnection, prepare as applicable:

- this implementation repository/software image;
- a verified read-only canonical Core cache or checksum-manifested snapshot;
- Python 3.10+ and required venv support;
- local inference runtime **already installed** or supplied by a genuinely self-contained, machine-specific, verified offline package;
- selected local model weights/model store;
- required Skills / Methods / Standards metadata / workflow definitions for the intended task;
- required local engineering data;
- required proprietary tools, drivers, licenses and calibration assets.

### Linux / Jetson Ollama warning

`ollama-install.sh` is a bootstrap/network installer. Merely copying that shell script into `portable_assets/installers/` does **not** make a clean Linux/Jetson machine air-gap installable.

Therefore, when `Mode=offline` and Ollama is absent, AERIS now fails closed instead of executing that script. Until a verified self-contained runtime package format is implemented, prepare Ollama before disconnection.

## Private provider network boundary

Default:

```text
AERIS_LOCAL_NETWORK_SCOPE=loopback
```

Only `localhost`, `127.0.0.0/8` or `::1` are eligible for private engineering.

Explicit Human opt-in for a controlled LAN inference node:

```text
AERIS_LOCAL_NETWORK_SCOPE=trusted_lan
AERIS_LOCAL_BASE_URL=http://192.168.x.x:11434
```

`trusted_lan` accepts only literal RFC1918 / IPv6 ULA / loopback IP addresses. Public/global addresses and arbitrary hostnames are rejected. This is application policy; it does not replace network segmentation/TLS/firewall controls appropriate to the sensitivity of the data.

## Offline mode

```bash
python -m aeris_runtime mode set offline
```

Semantics:

- cloud provider is not used;
- public URL ingress is disabled;
- private engineering remains constrained to endpoint-policy-compliant local/trusted-LAN provider;
- remote Core is not refreshed;
- verified cached/snapshotted Core and local assets are used.

Software `offline` mode alone is not an air gap.

## Local mode

`local` also routes AI locally, but does not claim the machine/network is isolated from the internet.

## Cloud failure behavior

Only the **public research channel** can use Cloud AI. If `AERIS_CLOUD_FALLBACK_TO_LOCAL=true`, a failed public cloud request may use the endpoint-policy-compliant local provider. If false, the cloud failure is surfaced instead of silently falling back.

Private engineering never becomes cloud work because of mode, cost, fallback or provider failure.

## Evidence requirement

Do not label a machine/workflow `OFFLINE VERIFIED` unless all applicable requirements pass:

1. `python -m aeris_runtime core verify` passes;
2. the machine profile is known and its required local acceptance is applicable;
3. local endpoint policy passes;
4. real local inference completes;
5. `mode set offline` and real offline-mode inference complete;
6. unit/security tests pass;
7. required Skills/data/tools are present for the target workflow;
8. for a Hard Offline claim, external network is disconnected/blocked and multi-path probes are blocked;
9. `.aeris/state/LOCAL_ACCEPTANCE.json` is retained as evidence.

Even after Hard Offline probes pass, the precise claim is **tested outbound paths were blocked**, not a mathematical proof that every OS/firmware/process path can never egress.
