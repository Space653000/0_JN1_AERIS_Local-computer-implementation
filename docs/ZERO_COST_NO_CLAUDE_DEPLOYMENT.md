# AERIS Zero-Cost / No-Claude Default Deployment

## Scope

The default AERIS bootstrap/opening path is designed to require **no paid professional acoustic software, no paid cloud API credential, no Claude Code installation and no Claude token**.

Codex remains the default local builder/deployer/operator. Claude Code remains an optional reviewer path only when the Human Chief Engineer explicitly requests it.

## Default bootstrap

The supported default path may install or use only baseline components required for the local runtime (Python, Git where online Core sync is needed, Ollama or a compatible local provider, and the configured local model). These components must not be treated as permission to auto-accept any third-party EULA or package/source agreement.

If an upstream installer/package/source requires explicit agreement, AERIS must fail closed and surface the minimum Human Gate. It must not add `--accept-package-agreements`, `--accept-source-agreements`, purchase a license, invent a credential, or silently substitute a paid cloud service.

## Professional tools

COMSOL, MATLAB, APx, KLIPPEL, SoundCheck and ACQUA integrations are optional professional scopes. Their adapters remain `BLOCKED_EXTERNAL` until the exact software/hardware/license/calibration environment exists and passes its own E2E Evidence. They are not prerequisites for default Company Opening.

## Independent review

Independent-review requirements are capability/authority separation requirements, not a Claude dependency. The deterministic reviewer allocator uses AERIS reviewer seats by default. It does not launch an external model. A real review record is still required where the R0-R4 policy requires independent review.

## Machine-verifiable contract

`config/zero_cost_no_claude.v1.json` is validated by `aeris_runtime/deployment_policy.py` and `tests/test_zero_cost_deployment.py`.

CI must fail if the default installer/autopilot starts auto-accepting package/license agreements, invokes the optional Claude wrapper, auto-installs paid professional tools, requires a Claude token, or makes an optional licensed adapter a default prerequisite.

## Truth boundary

This policy means **AERIS itself does not require paid software or Claude for its default bootstrap/opening path**. It is not legal advice and does not guarantee an upstream vendor can never change pricing or license terms. Any future upstream agreement or monetary requirement becomes an explicit Human/External Gate rather than being silently accepted.
