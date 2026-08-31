"""Hard privacy boundary for AERIS one-way cloud ingress."""
from __future__ import annotations

from dataclasses import dataclass
import re


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


_SECRET_PATTERNS = [
    ("private key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----", re.I)),
    ("bearer token", re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{16,}", re.I)),
    ("OpenAI-style API key", re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b", re.I)),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("credential assignment", re.compile(r"\b(?:password|passwd|secret|api[_-]?key|token)\s*[:=]\s*[^\s]{8,}", re.I)),
]

_PRIVATE_MARKERS = re.compile(
    r"(?:confidential|strictly confidential|customer confidential|internal only|nda|機密|客戶機密|內部限定|不得外流)",
    re.I,
)


def public_query_risk_reasons(text: str) -> list[str]:
    """Best-effort DLP screening before a query is eligible for public cloud.

    This is defense-in-depth, not a substitute for OS/network DLP. False negatives are
    possible, so the user must still treat the public-research channel as public.
    """
    reasons: list[str] = []
    if len(text) > 20_000:
        reasons.append("query exceeds 20,000 characters; bulk local content is not allowed")
    for label, pattern in _SECRET_PATTERNS:
        if pattern.search(text):
            reasons.append(f"possible {label}")
    if _PRIVATE_MARKERS.search(text):
        reasons.append("query contains a private/confidential marker")
    return reasons


def assert_public_query_content_safe(text: str) -> None:
    reasons = public_query_risk_reasons(text)
    if reasons:
        raise CloudEgressDenied(
            "AERIS blocked this public-cloud research query: " + "; ".join(reasons) + ". "
            "Use local chat for private engineering content, or manually rewrite the query using public information only."
        )
