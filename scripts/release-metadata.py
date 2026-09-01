#!/usr/bin/env python3
"""Generate dependency-free SPDX file inventory, provenance and SHA256SUMS for AERIS packages."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import platform
import subprocess
from pathlib import Path

EXCLUDED_PARTS = {".git", ".venv", ".aeris", "data", "logs", "portable_assets", "private-backups", "__pycache__", ".pytest_cache"}
EXCLUDED_NAMES = {".env", "SBOM.spdx.json", "PROVENANCE.json", "SHA256SUMS"}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def inventory(root: Path, output_dir: Path) -> list[tuple[str, str, int]]:
    rows=[]
    output_resolved=output_dir.resolve()
    for path in sorted(root.rglob("*")):
        try:
            resolved=path.resolve()
        except OSError:
            continue
        if output_resolved == resolved or output_resolved in resolved.parents:
            continue
        rel=path.relative_to(root)
        if any(part in EXCLUDED_PARTS for part in rel.parts) or path.name in EXCLUDED_NAMES:
            continue
        if path.is_symlink():
            raise RuntimeError(f"Release metadata refuses symlink: {rel.as_posix()}")
        if path.is_file():
            rows.append((rel.as_posix(),digest(path),path.stat().st_size))
    return rows


def git_head(root: Path) -> str:
    try:
        return subprocess.check_output(["git","-C",str(root),"rev-parse","HEAD"],text=True,timeout=5).strip()
    except Exception:
        return "UNKNOWN"


def core_baseline(root: Path) -> str:
    path=root/"core.lock.json"
    try:
        return str(json.loads(path.read_text(encoding="utf-8-sig")).get("baseline_sha","UNKNOWN"))
    except Exception:
        return "UNKNOWN"


def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=Path("."))
    p.add_argument("--output",type=Path,default=Path("release-metadata"))
    p.add_argument("--source-commit",default="")
    a=p.parse_args()
    root=a.root.resolve(); out=a.output.resolve(); out.mkdir(parents=True,exist_ok=True)
    rows=inventory(root,out)
    source=a.source_commit.strip() or git_head(root)
    aggregate=hashlib.sha256("\n".join(f"{sha}  {name}" for name,sha,_ in rows).encode()).hexdigest()
    created=dt.datetime.now(dt.timezone.utc).isoformat()

    spdx={
      "spdxVersion":"SPDX-2.3",
      "dataLicense":"CC0-1.0",
      "SPDXID":"SPDXRef-DOCUMENT",
      "name":"AERIS-Portable-Company-Software",
      "documentNamespace":f"https://aeris.local/spdx/{aggregate}",
      "creationInfo":{"created":created,"creators":["Tool: AERIS release-metadata.py"]},
      "packages":[{
        "name":"AERIS-Portable-Company-Software",
        "SPDXID":"SPDXRef-Package-AERIS",
        "downloadLocation":"NOASSERTION",
        "filesAnalyzed":True,
        "packageVerificationCode":{"packageVerificationCodeValue":aggregate},
        "licenseConcluded":"NOASSERTION",
        "licenseDeclared":"NOASSERTION",
        "copyrightText":"NOASSERTION"
      }],
      "files":[{
        "fileName":"./"+name,
        "SPDXID":"SPDXRef-File-"+sha[:20],
        "checksums":[{"algorithm":"SHA256","checksumValue":sha}],
        "licenseConcluded":"NOASSERTION",
        "copyrightText":"NOASSERTION"
      } for name,sha,_ in rows]
    }
    (out/"SBOM.spdx.json").write_text(json.dumps(spdx,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    provenance={
      "schema_version":1,
      "kind":"AERIS_SOFTWARE_IMAGE_PROVENANCE",
      "created_at_utc":created,
      "source_commit":source,
      "core_baseline_sha":core_baseline(root),
      "inventory_sha256":aggregate,
      "file_count":len(rows),
      "generator":{"python":platform.python_version(),"platform":platform.platform()},
      "scope":"software-only; no private state, secrets, model weights, proprietary assets or customer data",
      "verification":"verify SHA256SUMS and SBOM after transfer; then run local acceptance on destination machine"
    }
    (out/"PROVENANCE.json").write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (out/"SHA256SUMS").write_text("".join(f"{sha}  {name}\n" for name,sha,_ in rows),encoding="utf-8")
    print(json.dumps({"files":len(rows),"inventory_sha256":aggregate,"output":str(out)},indent=2))
    return 0


if __name__=="__main__": raise SystemExit(main())
