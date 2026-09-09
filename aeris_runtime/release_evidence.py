"""Resolve release authority from locally provisioned signed receipts.

Gate receipts are authoritative only when BOTH sides of an independent review
are authenticated:

* the implementer signs an exact task/Evidence/artifact/version binding, and
* the reviewer signs the gate decision from a distinct trusted subject/context.

The trust store is an operator-provisioned local authority boundary. There is no
API here to enroll keys or mint receipts. Filesystem administrators remain
trusted; application signatures do not protect against a compromised OS/admin.
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
IMPLEMENTER_PURPOSE = 'IMPLEMENTER_ATTESTATION'

_TASK_BINDING_FIELDS = (
    'scope',
    'artifact_id',
    'artifact_sha256',
    'implementer_id',
    'implementer_context',
    'version_tuple_sha256',
    'implementer_attestation_ref',
)


def canonical(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(',', ':'),
        ensure_ascii=False,
        allow_nan=False,
    ).encode()


def _safe_ref(value, *, what):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,120}', value):
        raise ValueError(f'unresolvable {what} ID')
    return value


def _fresh_window(payload, now, *, what):
    issued = datetime.fromisoformat(payload['issued_at'])
    expiry = datetime.fromisoformat(payload['expires_at'])
    if (
        issued.tzinfo is None
        or expiry.tzinfo is None
        or not 0 <= (now - issued).total_seconds() <= MAX_AGE_SECONDS
        or not issued < now < expiry
    ):
        raise ValueError(f'stale, future or expired {what}')


def _principal(trust, signer_id):
    principal = trust['principals'][signer_id]
    if principal.get('revoked') is not False:
        raise ValueError('authority principal is revoked or malformed')
    subject = principal.get('subject_id')
    if not isinstance(subject, str) or not subject:
        raise ValueError('authority principal subject missing')
    key_hex = principal.get('key_hex')
    if not isinstance(key_hex, str):
        raise ValueError('authority key missing')
    key = bytes.fromhex(key_hex)
    if len(key) < 32:
        raise ValueError('insufficient authority key strength')
    return principal, key


def _verify_signed_receipt(receipt, trust):
    payload = receipt['payload']
    if not isinstance(payload, dict):
        raise ValueError('authority receipt payload malformed')
    signer_id = _safe_ref(payload['signer_id'], what='signer')
    principal, key = _principal(trust, signer_id)
    signature = receipt.get('signature')
    if not isinstance(signature, str):
        raise ValueError('authority receipt signature missing')
    expected = hmac.new(key, canonical(payload), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise ValueError('untrusted or tampered authority receipt')
    return payload, principal, key


def _load_receipt(ref):
    ref = _safe_ref(ref, what='authority Evidence')
    return json.loads((RECEIPTS / (ref + '.json')).read_text(encoding='utf-8'))


def _task_binding(task):
    metadata = task['metadata']
    binding = {key: metadata[key] for key in _TASK_BINDING_FIELDS}
    if any(not isinstance(value, str) or not value for value in binding.values()):
        raise ValueError('task authority binding missing')
    if not re.fullmatch(r'[0-9a-f]{64}', binding['artifact_sha256']):
        raise ValueError('task artifact hash malformed')
    if not re.fullmatch(r'[0-9a-f]{64}', binding['version_tuple_sha256']):
        raise ValueError('task version-tuple hash malformed')
    _safe_ref(binding['implementer_attestation_ref'], what='implementer attestation')
    return binding


def _resolve_implementer(task, trust, binding, run_id, bundle_sha256, now):
    """Authenticate the claimed implementer; caller metadata alone is never identity."""
    receipt = _load_receipt(binding['implementer_attestation_ref'])
    payload, principal, key = _verify_signed_receipt(receipt, trust)
    if payload.get('type') != IMPLEMENTER_PURPOSE:
        raise ValueError('wrong implementer attestation type')
    if principal.get('can_implement') is not True:
        raise ValueError('signer lacks implementer authority')
    contexts = principal.get('execution_contexts')
    if not isinstance(contexts, list) or any(not isinstance(item, str) or not item for item in contexts):
        raise ValueError('implementer execution-context policy malformed')

    subject = principal['subject_id']
    if subject != binding['implementer_id']:
        raise ValueError('caller implementer alias is not authenticated')
    if binding['implementer_context'] not in contexts:
        raise ValueError('unattested implementer context')

    expected = {
        'task_id': task['task_id'],
        'scope': binding['scope'],
        'artifact_id': binding['artifact_id'],
        'artifact_sha256': binding['artifact_sha256'],
        'implementer_id': subject,
        'implementer_context': binding['implementer_context'],
        'version_tuple_sha256': binding['version_tuple_sha256'],
        'run_id': run_id,
        'bundle_sha256': bundle_sha256,
    }
    if any(payload.get(key) != value for key, value in expected.items()):
        raise ValueError('implementer attestation binding mismatch')
    _fresh_window(payload, now, what='implementer attestation')
    return {
        'subject_id': subject,
        'context': binding['implementer_context'],
        'signer_id': payload['signer_id'],
        'key_fingerprint': hashlib.sha256(key).hexdigest(),
    }


def validate_version_tuple(root, manifest, expected_hash, now):
    """Resolve the sealed four-way observation, not a caller alignment boolean."""
    versions = json.loads((root / 'version_tuple.json').read_text(encoding='utf-8'))
    if hashlib.sha256(canonical(versions)).hexdigest() != expected_hash:
        raise ValueError('four-way version tuple integrity mismatch')

    from .blueprint_compatibility import TARGET

    core = versions['core_blueprint']
    implementation = versions['implementation']
    checkout = versions['local_checkout']
    running = versions['running_service']
    sha = implementation['commit_sha']
    if (
        core.get('repository') != 'Space653000/0_JN1_AERIS'
        or implementation.get('repository') != 'Space653000/0_JN1_AERIS_Local-computer-implementation'
        or core.get('commit_sha') != TARGET
        or not re.fullmatch(r'[0-9a-f]{40}', sha)
        or manifest['implementation_sha'] != sha
        or checkout['commit_sha'] != sha
        or running['implementation_sha'] != sha
        or running['core_sha'] != TARGET
    ):
        raise ValueError('four-way version tuple is incompatible or DRIFT')

    if checkout.get('dirty') is not False:
        raise ValueError('formal authority requires a clean observed local checkout')
    for field in ('overlay_digest', 'configuration_digest', 'asset_digest'):
        if not re.fullmatch(r'[0-9a-f]{64}', checkout.get(field, '')):
            raise ValueError('missing checkout content digest')
    if any(running.get(key) != checkout[key] for key in ('configuration_digest', 'asset_digest')):
        raise ValueError('running configuration/asset drift')

    observed = datetime.fromisoformat(running['observed_at'])
    started = datetime.fromisoformat(running['started_at'])
    if (
        observed.tzinfo is None
        or started.tzinfo is None
        or not started <= observed <= now
        or (now - observed).total_seconds() > MAX_AGE_SECONDS
    ):
        raise ValueError('missing or stale running-service observation')
    return versions


def resolve(ref, task, gate):
    """Validate exact task/artifact/scope, both identities, signatures and expiry."""
    ref = _safe_ref(ref, what='authority Evidence')
    try:
        receipt = _load_receipt(ref)
        trust = json.loads(TRUST_STORE.read_text(encoding='utf-8'))
        payload, principal, reviewer_key = _verify_signed_receipt(receipt, trust)
        binding = _task_binding(task)

        if (
            payload.get('task_id') != task['task_id']
            or payload.get('gate') != gate
            or payload.get('decision') != 'PASS'
        ):
            raise ValueError('wrong task, gate or reviewer decision')
        if any(payload.get(key) != value for key, value in binding.items()):
            raise ValueError('wrong scope, artifact or implementation binding')

        now = datetime.now(timezone.utc)
        _fresh_window(payload, now, what='Evidence')

        allowed_gates = principal.get('allowed_gates')
        if (
            not isinstance(allowed_gates, list)
            or any(not isinstance(item, str) or not item for item in allowed_gates)
            or gate not in allowed_gates
        ):
            raise ValueError('signer lacks gate authority')

        run = _safe_ref(payload['run_id'], what='Evidence run')
        bundle_sha256 = payload['bundle_sha256']
        if not isinstance(bundle_sha256, str) or not re.fullmatch(r'[0-9a-f]{64}', bundle_sha256):
            raise ValueError('Evidence bundle hash malformed')

        implementer = _resolve_implementer(task, trust, binding, run, bundle_sha256, now)

        reviewer_context = payload.get('reviewer_context')
        if gate in {'G4_INDEPENDENT_REVIEW', 'G5_APPROVAL'}:
            isolated = principal.get('isolated_contexts')
            if (
                not isinstance(isolated, list)
                or any(not isinstance(item, str) or not item for item in isolated)
            ):
                raise ValueError('reviewer isolation policy malformed')
            if principal['subject_id'] == implementer['subject_id']:
                raise ValueError('reviewer/implementer subject collision or alias collision')
            if hashlib.sha256(reviewer_key).hexdigest() == implementer['key_fingerprint']:
                raise ValueError('reviewer/implementer credential alias collision')
            if (
                not isinstance(reviewer_context, str)
                or not reviewer_context
                or reviewer_context == implementer['context']
            ):
                raise ValueError('reviewer/implementer context collision')
            if reviewer_context not in isolated:
                raise ValueError('unattested reviewer isolation')

        if gate == 'G5_APPROVAL' and (
            principal.get('kind') != 'HUMAN'
            or principal.get('human_authority') != 'Human Chief Engineer'
            or payload.get('approval_action') != 'APPROVE_EXACT_ARTIFACT'
        ):
            raise ValueError('missing authenticated Human approval artifact')

        if not evidence.validate_bundle(run)['valid']:
            raise ValueError('Evidence missing or integrity failure')
        root = evidence.bundle_dir(run)
        manifest = json.loads((root / 'run_manifest.json').read_text(encoding='utf-8'))
        if manifest['task_id'] != task['task_id']:
            raise ValueError('Evidence belongs to another task')
        if manifest.get('created_by') != implementer['subject_id']:
            raise ValueError('Evidence implementer identity does not match authenticated implementer')

        from .blueprint_compatibility import TARGET
        if manifest.get('canonical_core_sha') != TARGET:
            raise ValueError('Evidence Core version is incompatible with finalized Blueprint')

        created = datetime.fromisoformat(manifest['created_at_utc'])
        if created.tzinfo is None or not 0 <= (now - created).total_seconds() <= MAX_AGE_SECONDS:
            raise ValueError('stale or future source Evidence')

        sealed = hashlib.sha256((root / 'bundle_manifest.json').read_bytes()).hexdigest()
        if not hmac.compare_digest(sealed, bundle_sha256):
            raise ValueError('resealed or tampered Evidence')

        validate_version_tuple(root, manifest, binding['version_tuple_sha256'], now)

        artifact = root / 'processed' / 'release-artifact.bin'
        if artifact.is_symlink() or root.is_symlink() or (root / 'processed').is_symlink():
            raise ValueError('authority artifact cannot use symlink indirection')
        if hashlib.sha256(artifact.read_bytes()).hexdigest() != binding['artifact_sha256']:
            raise ValueError('artifact hash mismatch')

        resolved = dict(payload)
        resolved['_resolved_authority'] = {
            'reviewer_subject_id': principal['subject_id'],
            'reviewer_context': reviewer_context,
            'implementer_subject_id': implementer['subject_id'],
            'implementer_context': implementer['context'],
        }
        return resolved
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError('authority Evidence unavailable or malformed') from exc


def require_refs(refs, task, gate):
    if not refs:
        raise ValueError('authenticated gate Evidence required')
    return [resolve(ref, task, gate) for ref in refs]
