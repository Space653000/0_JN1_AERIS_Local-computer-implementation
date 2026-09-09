"""Immutable V6 report triples. Only the supervision output directory is written.

Manifest links the exact snapshot bytes, avoiding a circular self-hash. Ambiguous
legacy history is explicitly UNKNOWN, never reconstructed from filename order.
"""
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


def sha(data):
    return hashlib.sha256(data).hexdigest()


def history_valid(seen):
    """Revalidate every link and both manifest entries, not just the last row."""
    if not seen or set(seen) != set(range(1, max(seen)+1)):
        return False
    previous_hash = None
    try:
        for number in sorted(seen):
            if len(seen[number]) != 1:
                return False
            path = seen[number][0]
            data = path.read_bytes()
            row = json.loads(data)
            report = path.with_name(path.name.replace('SNAPSHOT', 'REPORT')).with_suffix('.md')
            manifest = path.with_name(path.name.replace('SNAPSHOT', 'MANIFEST')).with_suffix('.sha256')
            lines = manifest.read_text(encoding='utf-8').splitlines()
            if f'{sha(data)}  {path.name}' not in lines or f'{sha(report.read_bytes())}  {report.name}' not in lines:
                return False
            if row.get('snapshot_id') != f'S{number:04d}' or row.get('previous_snapshot_hash') != previous_hash:
                return False
            if row.get('previous_snapshot_id') != (f'S{number-1:04d}' if number > 1 else None):
                return False
            if row.get('chain_state') != ('GENESIS' if number == 1 else 'LINKED'):
                return False
            if row.get('current_report_hash') != sha(report.read_bytes()):
                return False
            previous_hash = sha(data)
        return True
    except (OSError, ValueError, TypeError):
        return False


def publish(directory, report, payload):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    lock = directory / '.snapshot-publication.lock'
    # Exclusive creation fails closed after a crashed writer; no auto-unlock.
    with lock.open('x', encoding='utf-8') as handle:
        handle.write(datetime.now(timezone.utc).isoformat())
    try:
        seen = {}
        for path in directory.rglob('AERIS_SUPERVISION_SNAPSHOT_S*_*.json'):
            match = re.search(r'_S(\d+)_', path.name)
            if match:
                seen.setdefault(int(match[1]), []).append(path)
        previous_number = max(seen, default=0)
        previous = seen.get(previous_number, [])
        chain_state = 'GENESIS' if not seen else 'CHAIN_UNKNOWN'
        link = None
        if len(previous) == 1:
            path = previous[0]
            prior_bytes = path.read_bytes()
            prior = json.loads(prior_bytes)
            link = {'snapshot_id': f'S{previous_number:04d}',
                    'file': path.relative_to(directory).as_posix(), 'sha256': sha(prior_bytes)}
            # Legacy or broken/gapped chains cannot acquire a verified history.
            if history_valid(seen):
                chain_state = 'LINKED'
        number = previous_number + 1
        snapshot_id = f'S{number:04d}'
        now = datetime.now(timezone.utc)
        suffix = f'{snapshot_id}_{now.strftime("%Y%m%d_%H%M%S_%f")}'
        report_path = directory / f'AERIS_SUPERVISION_REPORT_{suffix}.md'
        snapshot_path = directory / f'AERIS_SUPERVISION_SNAPSHOT_{suffix}.json'
        manifest_path = directory / f'AERIS_SUPERVISION_MANIFEST_{suffix}.sha256'
        report_bytes = report.encode('utf-8')
        snapshot = dict(payload, schema_version=6, snapshot_id=snapshot_id,
                        previous_snapshot_id=link['snapshot_id'] if link else None,
                        previous_snapshot_hash=link['sha256'] if link else None,
                        previous_snapshot=link, chain_state=chain_state,
                        generated_at=now.isoformat(), current_report_hash=sha(report_bytes),
                        manifest_linkage=manifest_path.name)
        snapshot_bytes = (json.dumps(snapshot, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode('utf-8')
        manifest_bytes = (f'{sha(report_bytes)}  {report_path.name}\n'
                          f'{sha(snapshot_bytes)}  {snapshot_path.name}\n').encode('utf-8')
        # Manifest is the commit marker. A partial triple is never complete.
        for path, content in ((report_path,report_bytes),(snapshot_path,snapshot_bytes),(manifest_path,manifest_bytes)):
            with path.open('xb') as handle:
                handle.write(content)
        return {'snapshot': snapshot, 'paths': [str(report_path), str(snapshot_path), str(manifest_path)]}
    finally:
        lock.unlink()
