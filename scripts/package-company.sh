#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="${1:-$ROOT/dist}"
STAGE="$ROOT/.aeris/package-$STAMP"
mkdir -p "$OUT" "$STAGE"
tar \
  --exclude=.git --exclude=.venv --exclude=.aeris --exclude=data --exclude=logs \
  --exclude=dist --exclude=dist-ci --exclude=.env --exclude=portable_assets \
  --exclude=private-backups --exclude='__pycache__' --exclude=.pytest_cache \
  -cf - -C "$ROOT" . | tar -xf - -C "$STAGE"
SHA="UNKNOWN"; command -v git >/dev/null 2>&1 && SHA="$(git -C "$ROOT" rev-parse HEAD 2>/dev/null || echo UNKNOWN)"
python3 - "$STAGE/RELOCATION_MANIFEST.json" "$SHA" <<'PY'
import datetime,json,sys
path,sha=sys.argv[1:]
payload={
  'company':'AERIS',
  'image_type':'portable_company_image',
  'image_scope':'SOFTWARE_ONLY_NO_PRIVATE_STATE_NO_PRIVATE_ASSETS',
  'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
  'source_commit':sha,
  'private_state_included':False,
  'portable_assets_included':False,
  'release_metadata':'release-metadata/',
  'restore_requirement':'For full relocation, separately supply encrypted private state and Human-controlled Private Asset Pack, then run local acceptance.'
}
open(path,'w',encoding='utf-8').write(json.dumps(payload,indent=2)+'\n')
PY
python3 "$STAGE/scripts/release-metadata.py" --root "$STAGE" --output "$STAGE/release-metadata" --source-commit "$SHA"
PKG="$OUT/AERIS-Portable-Company-Software-$STAMP.tar.gz"
tar -czf "$PKG" -C "$STAGE" .
rm -rf "$STAGE"
echo "Created software-only package: $PKG"
echo 'Package includes SBOM.spdx.json, PROVENANCE.json and SHA256SUMS under release-metadata/.'
echo 'Private state and portable_assets were deliberately excluded. See docs/deployment/STATE_BACKUP_RESTORE.md.'
