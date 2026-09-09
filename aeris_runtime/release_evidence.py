"""Resolve authority from locally provisioned signed receipts, never caller labels.

The trust store is an operator-provisioned local authority boundary. There is no
API to enroll keys or mint approval receipts. Filesystem administrators remain
trusted; application hashes alone do not authenticate a Human.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import re
from datetime import datetime, timezone

from .config import ROOT
from . import evidence

TRUST_STORE = ROOT / '.aeris' / 'authority' / 'trust.json'
RECEIPTS = ROOT / '.aeris' / 'authority' / 'receipts'
MAX_AGE_SECONDS = 86400


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def validate_version_tuple(root, manifest, expected_hash, now):
    """Resolve the sealed four-way observation, not a caller alignment boolean."""
    versions = json.loads((root/'version_tuple.json').read_text(encoding='utf-8'))
    if hashlib.sha256(canonical(versions)).hexdigest() != expected_hash:
        raise ValueError('four-way version tuple integrity mismatch')
    from .blueprint_compatibility import TARGET
    core = versions['core_blueprint']
    implementation = versions['implementation']
    checkout = versions['local_checkout']
    running = versions['running_service']
    sha = implementation['commit_sha']
    if (core.get('repository') != 'Space653000/0_JN1_AERIS'
            or implementation.get('repository') != 'Space653000/0_JN1_AERIS_Local-computer-implementation'
            or core.get('commit_sha') != TARGET
            or not re.fullmatch(r'[0-9a-f]{40}', sha)
            or manifest['implementation_sha'] != sha
            or checkout['commit_sha'] != sha
            or running['implementation_sha'] != sha or running['core_sha'] != TARGET):
        raise ValueError('four-way version tuple is incompatible or DRIFT')
    if type(checkout.get('dirty')) is not bool:
        raise ValueError('local dirty state must be observed')
    for field in ('overlay_digest', 'configuration_digest', 'asset_digest'):
        if not re.fullmatch(r'[0-9a-f]{64}', checkout.get(field, '')):
            raise ValueError('missing checkout content digest')
    if any(running.get(k) != checkout[k] for k in ('configuration_digest', 'asset_digest')):
        raise ValueError('running configuration/asset drift')
    observed = datetime.fromisoformat(running['observed_at'])
    started = datetime.fromisoformat(running['started_at'])
    if (observed.tzinfo is None or started.tzinfo is None or not started <= observed <= now
            or (now-observed).total_seconds() > MAX_AGE_SECONDS):
        raise ValueError('missing or stale running-service observation')
    return versions


def resolve(ref, task, gate):
    """Validate exact task/artifact/scope, signature, source hashes and expiry."""
    if not isinstance(ref, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,120}', ref):
        raise ValueError('unresolvable authority Evidence ID')
    try:
        receipt = json.loads((RECEIPTS / (ref + '.json')).read_text(encoding='utf-8'))
        payload = receipt['payload']
        trust = json.loads(TRUST_STORE.read_text(encoding='utf-8'))
        principal = trust['principals'][payload['signer_id']]
        signature = hmac.new(bytes.fromhex(principal['key_hex']), canonical(payload), hashlib.sha256).hexdigest()
        if principal.get('revoked') is not False or not hmac.compare_digest(signature, receipt['signature']):
            raise ValueError('untrusted or tampered authority receipt')
        if len(bytes.fromhex(principal['key_hex'])) < 32:
            raise ValueError('insufficient authority key strength')
        metadata = task['metadata']
        binding = {k: metadata[k] for k in ('scope', 'artifact_id', 'artifact_sha256', 'implementer_id', 'implementer_context', 'version_tuple_sha256')}
        if any(not isinstance(v, str) or not v for v in binding.values()):
            raise ValueError('task authority binding missing')
        if payload['task_id'] != task['task_id'] or payload['gate'] != gate or payload['decision'] != 'PASS':
            raise ValueError('wrong task, gate or reviewer decision')
        if any(payload[k] != v for k, v in binding.items()):
            raise ValueError('wrong scope, artifact or implementation binding')
        now = datetime.now(timezone.utc)
        issued = datetime.fromisoformat(payload['issued_at'])
        expiry = datetime.fromisoformat(payload['expires_at'])
        if issued.tzinfo is None or expiry.tzinfo is None or not 0 <= (now-issued).total_seconds() <= MAX_AGE_SECONDS or not issued < now < expiry:
            raise ValueError('stale, future or expired Evidence')
        if gate not in principal['allowed_gates']:
            raise ValueError('signer lacks gate authority')
        if gate in {'G4_INDEPENDENT_REVIEW', 'G5_APPROVAL'}:
            if principal['subject_id'] == binding['implementer_id']:
                raise ValueError('same author renamed reviewer')
            if payload['reviewer_context'] == binding['implementer_context'] or not payload['reviewer_context']:
                raise ValueError('reviewer/implementer context collision')
            if payload['reviewer_context'] not in principal['isolated_contexts']:
                raise ValueError('unattested reviewer isolation')
        if gate == 'G5_APPROVAL' and (principal.get('kind') != 'HUMAN' or payload.get('approval_action') != 'APPROVE_EXACT_ARTIFACT'):
            raise ValueError('missing authenticated Human approval artifact')
        run = payload['run_id']
        if not isinstance(run, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,140}', run):
            raise ValueError('invalid Evidence run ID')
        if not evidence.validate_bundle(run)['valid']:
            raise ValueError('Evidence missing or integrity failure')
        root = evidence.bundle_dir(run)
        manifest = json.loads((root/'run_manifest.json').read_text(encoding='utf-8'))
        if manifest['task_id'] != task['task_id']:
            raise ValueError('Evidence belongs to another task')
        from .blueprint_compatibility import TARGET
        if manifest.get('canonical_core_sha') != TARGET:
            raise ValueError('Evidence Core version is incompatible with finalized Blueprint')
        created = datetime.fromisoformat(manifest['created_at_utc'])
        if created.tzinfo is None or not 0 <= (now-created).total_seconds() <= MAX_AGE_SECONDS:
            raise ValueError('stale or future source Evidence')
        sealed = hashlib.sha256((root/'bundle_manifest.json').read_bytes()).hexdigest()
        if not hmac.compare_digest(sealed, payload['bundle_sha256']):
            raise ValueError('resealed or tampered Evidence')
        validate_version_tuple(root, manifest, binding['version_tuple_sha256'], now)
        artifact = root/'processed'/'release-artifact.bin'
        if artifact.is_symlink() or root.is_symlink() or (root/'processed').is_symlink():
            raise ValueError('authority artifact cannot use symlink indirection')
        if hashlib.sha256(artifact.read_bytes()).hexdigest() != binding['artifact_sha256']:
            raise ValueError('artifact hash mismatch')
        return payload
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError('authority Evidence unavailable or malformed') from exc


def require_refs(refs, task, gate):
    if not refs:
        raise ValueError('authenticated gate Evidence required')
    return [resolve(ref, task, gate) for ref in refs]
