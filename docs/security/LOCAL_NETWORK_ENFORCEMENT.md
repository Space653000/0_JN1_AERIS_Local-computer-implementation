# AERIS Local Network / Data-Egress Enforcement

AERIS distinguishes **application policy** from **machine enforcement**. They are not the same assurance level.

## Level P1 — Application privacy boundary (implemented/tested)

- private engineering chat always routes to local provider;
- public research never auto-attaches Memory/Evidence/local files/customer data;
- DLP heuristics block obvious secrets/confidential markers;
- public URL ingress blocks loopback/private/link-local addresses and unsafe redirects;
- `offline` mode blocks AERIS public URL ingress and cloud model routing.

This protects normal AERIS behavior, but it cannot control unrelated software or a compromised Python process.

## Level P2 — Dedicated-machine outbound control (local deployment requirement)

For machines containing customer/measurement/private engineering data:

1. use a dedicated OS account for AERIS;
2. enable full-disk encryption (BitLocker on Windows, LUKS or equivalent on Linux);
3. keep OS firewall enabled;
4. disable unsolicited inbound services not required by the deployment;
5. do not expose Ollama (`11434`) to untrusted networks;
6. keep local provider bound to loopback unless a specifically approved trusted-LAN inference node is used;
7. disable automatic cloud sync for `.aeris/`, `data/`, `evidence/`, `memory/`, `logs/`, `portable_assets/`;
8. keep private backups encrypted; never upload them to the public GitHub repository;
9. use endpoint protection and OS patching appropriate to the organization.

## Level P3 — Strong cloud-ingress isolation (target architecture; local implementation still required)

For the strongest interpretation of "cloud can bring public information in, but cannot read AERIS private state", run the **Public Research / Ingress Gateway in a separate security boundary**:

```text
Internet / Cloud AI
        │
        ▼
NETWORKED PUBLIC GATEWAY
(container / VM / separate OS account)
        │
        │ may write only sanitized public artifacts
        ▼
PUBLIC INGRESS DROP
        │
        ▼
LOCAL AERIS PRIVATE ZONE
(no gateway access to Memory/Evidence/customer/raw measurement stores)
```

Recommended implementations:

- Windows: Hyper-V/Windows Sandbox/WSL VM or a dedicated low-privilege account with filesystem ACLs and outbound allow rules.
- Linux: rootless Podman/Docker or a dedicated system user/network namespace with read access denied to AERIS private directories.
- Air-gapped lab: use a separate internet-connected research machine, export public artifacts with hash/manifest, then import them into the AERIS lab machine.

Do **not** call P3 implemented until the chosen isolation mechanism is deployed and adversarially tested on the actual machine.

## HARD OFFLINE verification

`offline` in software is necessary but not sufficient for an air-gap claim. To verify hard offline:

1. physically disconnect Ethernet/Wi-Fi or apply a tested deny-all external egress firewall profile;
2. run `scripts/local-acceptance.ps1 -HardOffline` on Windows, or `AERIS_HARD_OFFLINE=1 bash scripts/local-acceptance.sh` on Linux/Jetson;
3. confirm real local inference succeeds;
4. preserve `.aeris/state/LOCAL_ACCEPTANCE.json` as evidence;
5. reconnect only after the task/security policy permits it.

## Important limitation

Network firewalls cannot determine whether text is confidential. DLP/classification, filesystem isolation, least privilege and Human review remain necessary. The strongest practical design is **separate public gateway + private local engineering zone**, not a promise that one unrestricted process can safely access both every local secret and the public internet.
