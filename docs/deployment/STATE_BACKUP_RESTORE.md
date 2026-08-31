# Encrypted AERIS Private-State Backup / Restore

The public Portable Company repository/package is **software-only**. It deliberately excludes private runtime state. A full relocation requires a separate encrypted private-state package.

## What belongs in private state

When present, `scripts/private-state.py` includes:

- `.env` — cloud credentials/configuration;
- `.aeris/knowledge` — local Knowledge DB;
- `.aeris/state` — local mode/deployment/acceptance state;
- `.aeris/ingress` — downloaded public research artifacts;
- `data` — private engineering/customer data;
- `logs` — operational logs;
- `evidence` — engineering evidence;
- `memory` — local memory assets.

The Core cache is not included because it is public/read-only and can be synchronized or staged separately.

## Why `age` is required

AERIS does not implement homemade encryption. Python standard library does not provide a suitable modern authenticated portable file-encryption primitive, so secure relocation requires a real `age` CLI installation.

If `age` is missing, AERIS **refuses to call a plaintext ZIP a secure backup**.

## Export — passphrase mode

From the implementation repository:

```bash
python scripts/private-state.py export private-backups/AERIS-private-state.age
```

`age` asks for a passphrase interactively. The output is accompanied by:

```text
AERIS-private-state.age.manifest.json
```

The manifest records SHA-256, included paths, source commit, creation time and encryption mode. Never commit the encrypted backup or manifest if its metadata is sensitive.

## Export — recipient/key mode

```bash
python scripts/private-state.py export private-backups/AERIS-private-state.age --recipient age1...
```

Prefer recipient mode for managed systems because the decryption identity can be stored separately from the backup.

## Restore

Passphrase-encrypted:

```bash
python scripts/private-state.py import private-backups/AERIS-private-state.age
```

Recipient-encrypted:

```bash
python scripts/private-state.py import private-backups/AERIS-private-state.age --identity /secure/path/key.txt
```

Restore verifies the ciphertext SHA-256 and rejects archive path traversal before extraction.

## Required post-restore acceptance

A restored company is **not verified merely because extraction succeeded**. Run:

Windows:

```powershell
.\scripts\local-acceptance.ps1
```

Linux / Jetson:

```bash
bash scripts/local-acceptance.sh
```

For an air-gapped claim, disconnect/block external network and use the hard-offline acceptance mode documented in `docs/security/LOCAL_NETWORK_ENFORCEMENT.md`.

## Full relocation set

A complete machine move may need all three:

1. **Software Company Image** — public source/package.
2. **Encrypted Private State** — this document.
3. **Private Asset Pack** — model weights, proprietary installers/licenses, drivers, calibration assets and other legally portable machine assets.

Only after restore + tool-specific preflight + local acceptance may the new machine be promoted from `INSTALLED` to `VERIFIED`.
