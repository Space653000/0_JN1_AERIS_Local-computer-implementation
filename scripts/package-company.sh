#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="${1:-$ROOT/dist}"
STAGE="$ROOT/.aeris/package-$STAMP"
mkdir -p "$OUT" "$STAGE"
tar --exclude=.git --exclude=.venv --exclude=.aeris --exclude=data --exclude=logs --exclude=dist --exclude=.env --exclude='__pycache__' -cf - -C "$ROOT" . | tar -xf - -C "$STAGE"
SHA="UNKNOWN"; command -v git >/dev/null 2>&1 && SHA="$(git -C "$ROOT" rev-parse HEAD 2>/dev/null || echo UNKNOWN)"
printf '{"company":"AERIS","image_type":"portable_company_image","created_at":"%s","source_commit":"%s"}\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$SHA" > "$STAGE/RELOCATION_MANIFEST.json"
tar -czf "$OUT/AERIS-Portable-Company-$STAMP.tar.gz" -C "$STAGE" .
rm -rf "$STAGE"
echo "Created: $OUT/AERIS-Portable-Company-$STAMP.tar.gz"
echo "Run company status + doctor after relocation."
