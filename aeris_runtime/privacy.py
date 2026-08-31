"""Hard privacy boundary for AERIS one-way cloud ingress."""
from __future__ import annotations

from dataclasses import dataclass


class CloudEgressDenied(RuntimeError):
    """Raised when a request would send local/private context to a cloud provider."""


@dataclass(frozen=True)
class CloudRequestPolicy:
    workload: str
    attach_memory: bool = False
    attach_evidence: bool = False
    attach_local_files: bool = False
    attach_private_data: bool = False

    @property
    def cloud_safe(self) -> bool:
        return (
            self.workload == "public_research"
            and not self.attach_memory
            and not self.attach_evidence
            and not self.attach_local_files
            and not self.attach_private_data
        )


def assert_cloud_safe(policy: CloudRequestPolicy) -> None:
    if not policy.cloud_safe:
        raise CloudEgressDenied(
            "AERIS denies cloud egress for local/private context. "
            "Cloud is available only through public_research with no local memory, evidence, files or private data attached."
        )
