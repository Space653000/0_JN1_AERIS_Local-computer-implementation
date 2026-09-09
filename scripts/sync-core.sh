#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
ADMISSION_PYTHON="$ROOT/.venv/bin/python"
if [ ! -x "$ADMISSION_PYTHON" ]; then ADMISSION_PYTHON=python3; fi
"$ADMISSION_PYTHON" -B -m aeris_runtime.deployment_admission
CORE="$ROOT/.aeris/core-reference"
STATE="$ROOT/.aeris/state/core-target.json"
URL='https://github.com/Space653000/0_JN1_AERIS.git'
mkdir -p "$(dirname "$CORE")" "$(dirname "$STATE")"
command -v git >/dev/null 2>&1 || { echo 'git is required for core sync.' >&2; exit 1; }

if [ ! -d "$CORE/.git" ]; then
  git clone --filter=blob:none --branch v0.7.0-blueprint.1 "$URL" "$CORE"
else
  git -C "$CORE" fetch origin tag v0.7.0-blueprint.1
fi

TARGET='64576bdbe680170fc1ea27306d1a2ab494cac733'
test "$(git -C "$CORE" rev-parse 'v0.7.0-blueprint.1^{commit}')" = "$TARGET" || { echo 'Frozen Blueprint mismatch; no checkout.' >&2; exit 2; }
git -C "$CORE" checkout --detach "$TARGET"
git -C "$CORE" remote set-url --push origin 'DISABLED://AERIS-CORE-READ-ONLY'
cat > "$CORE/.git/hooks/pre-push" <<'HOOK'
#!/bin/sh
echo "DENIED: AERIS canonical core repository is read-only for Codex/local implementation." >&2
exit 1
HOOK
chmod +x "$CORE/.git/hooks/pre-push"
SHA="$(git -C "$CORE" rev-parse HEAD)"
python3 - "$STATE" "$SHA" <<'PY'
import json,sys,datetime
path,sha=sys.argv[1],sys.argv[2]
payload={"repository":"Space653000/0_JN1_AERIS","branch":"main","sha":sha,"synced_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"remote_write":"DENIED"}
open(path,'w',encoding='utf-8').write(json.dumps(payload,indent=2)+"\n")
PY
echo "Core reference synchronized read-only: $SHA"
