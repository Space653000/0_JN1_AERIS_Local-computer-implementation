# Offline Operation Policy

## What "offline-capable" means

AERIS can continue to run supported workflows without internet access **only if the local inference runtime and model weights were installed or copied to the machine beforehand**.

A cloud model cannot operate while the network is unavailable. The architecture solves this by making local AI the continuity layer.

## Required pre-staged assets

Before deliberate disconnection:

- this implementation repository;
- Python 3.10+;
- local model server/runtime;
- selected local model weights;
- optional cached `.aeris/core-reference`;
- required local Skills/methods/data/tools for the intended workflow.

## Hard offline mode

```bash
python -m aeris_runtime mode set offline
```

Semantics:

- route only to the local provider;
- do not call the cloud provider;
- do not refresh the remote core reference;
- use the last cached core target and local implementation state.

## Local mode

`local` also uses local AI only, but it does not imply that the rest of the machine/network is intentionally isolated. Use `offline` when the no-cloud invariant matters.

## Cloud failure behavior

In `cloud` mode, if `AERIS_CLOUD_FALLBACK_TO_LOCAL=true`, AERIS attempts the local provider after a cloud request failure, provided the local provider is reachable.

This is a continuity mechanism, not a claim that cloud and local models are equivalent in reasoning quality.

## Evidence requirement

Do not label a machine `OFFLINE READY` unless all of these have been verified:

1. disconnect the network or block external egress;
2. `mode set offline`;
3. `doctor` sees local provider/model;
4. a real local `chat` completes;
5. tests pass;
6. no secret is required;
7. required local acoustic tools/data are present for the target workflow.
