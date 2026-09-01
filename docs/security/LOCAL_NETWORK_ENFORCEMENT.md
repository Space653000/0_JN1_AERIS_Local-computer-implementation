# AERIS Local Network / Data-Egress Enforcement

AERIS distinguishes **application policy**, **machine enforcement**, and **physical isolation**. They are different assurance levels and must never be collapsed into one privacy claim.

## Level P1 — AERIS application privacy boundary

Implemented/tested baseline:

- private engineering chat hard-routes to the local provider;
- public research never auto-attaches Memory/Evidence/local files/customer data;
- DLP heuristics block obvious secrets/confidential markers but are not proof of absence;
- public URL ingress validates public DNS/IP, pins the actual connection to a validated IP, validates HTTPS hostname/certificate, revalidates redirects, and stores content in quarantine;
- quarantined content is hashed and locally scanned when a supported scanner exists;
- downloaded content does **not** auto-index into Knowledge and needs explicit Human promotion;
- `offline` mode blocks AERIS public URL ingress and cloud model routing.

P1 protects normal AERIS behavior. It cannot control unrelated software, malware, a compromised OS, privileged administrators, firmware, or an independently configured third-party tool.

## Level P2 — Dedicated-machine outbound control

For machines containing customer/measurement/private engineering data:

1. use a dedicated OS account for AERIS;
2. enable full-disk encryption (BitLocker on Windows, LUKS or equivalent on Linux);
3. keep OS firewall enabled and maintain a reviewed outbound policy appropriate to the deployment;
4. disable unsolicited inbound services not required by AERIS;
5. do not expose Ollama/local inference endpoints to untrusted networks;
6. bind local provider to loopback unless a separately approved trusted-LAN inference node is used;
7. disable automatic cloud sync for `.aeris/`, `data/`, `evidence/`, `memory/`, `logs/`, `portable_assets/`, `private-backups/`, secret files and customer data;
8. keep private backups encrypted; never upload them to the public GitHub repository;
9. use endpoint protection and OS patching appropriate to the organization;
10. remove unnecessary developer/admin credentials from the runtime account;
11. separate public-research credentials from private-engineering data access;
12. preserve network/firewall configuration as local evidence when claiming an elevated privacy profile.

AERIS does not automatically change machine-wide firewall rules because doing so is an R3 operational/security action that can disconnect a machine or disrupt other services. The Human must deliberately apply/review the local network policy.

## Level P3 — Separate public gateway and private engineering zone

For the strongest practical interpretation of "cloud can bring public information in, but cannot read AERIS private state", run Public Research / Ingress in a separate security boundary:

```text
Internet / Cloud AI
        │
        ▼
NETWORKED PUBLIC GATEWAY
(container / VM / separate machine / constrained account)
        │
        │ PUBLIC artifacts only
        ▼
QUARANTINE
hash + scanner + content-risk markers
        │
        │ Human promotion
        ▼
LOCAL AERIS PRIVATE ZONE
(no gateway read permission to Memory/Evidence/customer/raw measurement stores)
```

Possible implementations:

- Windows: dedicated Hyper-V VM or separate low-privilege machine/account with filesystem ACLs and constrained network policy;
- Linux: dedicated VM, system user/network namespace, or rootless container with no mount/read permission to AERIS private directories;
- high-security lab: separate internet research computer, then transfer Human-approved public artifacts by controlled removable media with hash/manifest verification.

Do **not** call P3 implemented until the exact isolation mechanism is deployed and adversarially tested on the actual machine.

## Level P4 — Physical / true air-gap profile

For highly sensitive workflows:

- no network interface with a route to the public internet;
- no cloud AI/public ingress during the private workflow;
- local models/tools/data/Skills/Methods are staged before isolation;
- removable-media ingress follows quarantine/hash/scanner/Human-review policy;
- any temporary reconnection is a separate controlled operation.

P4 is operationally expensive but has the clearest security boundary.

## HARD OFFLINE verification

Software `mode=offline` is necessary but insufficient.

Recommended procedure:

1. physically disconnect Ethernet and Wi-Fi, or apply a Human-reviewed deny-all external-egress network profile;
2. confirm all required local model/tool/data dependencies are already available;
3. run Windows:

```powershell
.\scripts\local-acceptance.ps1 -HardOffline
```

or Linux/Jetson:

```bash
AERIS_HARD_OFFLINE=1 bash scripts/local-acceptance.sh
```

4. confirm real local inference and offline-mode inference both succeed;
5. preserve `.aeris/state/LOCAL_ACCEPTANCE.json`;
6. inspect the report's proxy environment and outbound probe results;
7. reconnect only after the workflow/security policy allows it.

Current hard-offline acceptance probes multiple IPv4 targets, DNS+TCP and IPv6. If **any** probe succeeds, acceptance fails.

If every probe is blocked, the recorded state is intentionally:

```text
OUTBOUND_PROBES_BLOCKED_NOT_GLOBAL_PROOF
```

This wording is deliberate. A finite set of probes is evidence about tested network paths, not a mathematical proof that every process/protocol/firmware path on the computer can never egress.

## Public ingress limitations

Public content remains untrusted even after HTTPS succeeds. Risks include:

- malware;
- prompt injection;
- misinformation/staleness;
- licensing restrictions;
- hostile instructions attempting local-file access/exfiltration.

Therefore TLS/download success does not make content trusted. AERIS keeps downloads quarantined until an explicit Human promotion decision.

## Important limitation

Firewalls cannot determine engineering truth and simple DLP cannot prove confidentiality. The strongest reliable pattern is **separation of duties and security zones**, not a promise that one unrestricted process can safely possess every local secret and unrestricted internet access simultaneously.
