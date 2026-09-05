"""Isolate real SQLite, workflow and evidence IO without mocking their logic."""
from contextlib import ExitStack, contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from aeris_runtime import audit, controlplane, evidence, reproduction, taskstate, verification, workflow
from aeris_runtime.config import ROOT
from aeris_runtime.engineering import factory, harness, role_acceptance


@contextmanager
def isolated_engineering_state():
    base = ROOT/'.aeris/test-temp'
    base.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=base) as directory, ExitStack() as stack:
        root = Path(directory)
        for module, name, value in (
            (controlplane,'DB_PATH',root/'control.sqlite3'), (factory,'STATE',root/'factory'),
            (role_acceptance,'STATE',root/'role-acceptance'), (harness,'DB',root/'memory.sqlite3'),
            (taskstate,'TASK_ROOT',root/'tasks'), (evidence,'EVIDENCE_ROOT',root/'evidence'),
            (verification,'VERIFICATION_ROOT',root/'verification'), (workflow,'WORKFLOW_ROOT',root/'workflows'),
            (reproduction,'REPRO_ROOT',root/'reproduction'), (audit,'AUDIT_DIR',root/'audit'),
            (audit,'AUDIT_FILE',root/'audit/audit.jsonl'), (audit,'LEDGER_PATH',root/'audit/audit.jsonl'),
            (audit,'LOCK_FILE',root/'audit/.lock')):
            stack.enter_context(patch.object(module, name, value))
        yield root
