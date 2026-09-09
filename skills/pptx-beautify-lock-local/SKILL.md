# PPTX Beautify Lock — AERIS Local Registry Adapter

This registry entry exposes the locally reviewed source/build provenance without
installing or changing any user Home `.codex` / `.claude` content.

It verifies SHA-256 for selected source authorities and the compiled executable.
The executable is `NOT_SIGNED`; package provenance does not make it a trusted signed
binary. A real input PPTX and full per-deck acceptance workflow are required before
any production-quality claim.
