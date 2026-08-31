# AERIS Machine Profiles — Deployment / Verification Matrix

同一份 Portable Company Image 可以部署到不同機器，但 **公司身份相同 ≠ 每台機器能力相同**。Machine Profile 只描述候選能力；真正狀態必須由該機器上的 acceptance evidence 決定。

## Windows CPU-only

適合：文件/知識檢索、輕量 local AI、Python 分析、無 GPU 的一般 PC。

必驗：

- Windows 支援狀態與更新；
- Python >= 3.10；
- 可用 RAM / disk；
- Ollama-compatible runtime；
- configured model 實際存在；
- real local inference latency / RAM；
- reboot 後 runtime 是否恢復；
- hard-offline acceptance（若宣稱 offline ready）。

CPU-only 可能很慢；installer 成功不等於性能合格。

## Windows NVIDIA Workstation

適合：主要工程 workstation、較大 local model、MATLAB/COMSOL/APx/KLIPPEL 等 Windows 工具（若合法安裝）。

除一般驗收外必驗：

- GPU model / driver / VRAM；
- sustained inference memory/latency；
- local model 與其他工程程式同時運行的資源 headroom；
- 每個 proprietary tool 的 version/license/API/preflight；
- APx/KLIPPEL 等硬體實際連線與 calibration（適用時）。

## Linux x86 + NVIDIA

適合：local AI server、batch Python、automation、部分 CAE/engineering workloads。

必驗：

- distro / kernel；
- NVIDIA driver/runtime；
- local model real inference；
- service auto-start / reboot recovery；
- filesystem permissions；
- firewall / bind address；
- intended proprietary tool 是否真的支援該 Linux distribution。

## Jetson Orin family / J4012 class

適合：edge/robotics/local always-on node；不是重型桌面 CAE workstation 的直接替代品。

必驗：

- JetPack / L4T / kernel / CUDA-related inventory；
- RAM/SSD 可用空間；
- local model 實際載入；
- sustained latency / memory headroom；
- 長時間 thermal / power stability；
- reboot recovery；
- USB/LAN/I2C/CAN/robot peripherals（實際需求才測）；
- hard-offline acceptance。

Baseline model 只是起點；若 4B 對實際工作過慢/過重，需以 benchmark 改模型，不能為了統一名稱犧牲可靠性。

## Trusted-LAN AI Server

適合：多台 AERIS client 共用一台較強的本地 inference node。

只有在以下都驗證後才能視為 local/private boundary：

- server 不暴露 public internet；
- firewall/ACL 限定 Human-approved clients；
- bind address 審查；
- authentication/network identity；
- audit/logging；
- client→server real inference；
- server failure 時的 fallback；
- LAN 本身符合資料分類要求。

RFC1918/private IP 本身不是安全保證。

## Professional tool capability

Machine detection 看到 `matlab` 或軟體已安裝，不代表工具能力 `VERIFIED`。每個工具必須依 `PROFESSIONAL_TOOLS.md` 完成：

```text
legal install/license
→ version/module inventory
→ API/CLI adapter
→ known-good fixture/project
→ real execution
→ expected artifact
→ provenance
→ calibration evidence if applicable
→ independent acceptance
```

## Promotion rule

```text
Detected
→ Configured
→ Implemented
→ Tested
→ Real-machine Verified
```

任何一步缺失就不能跳級。驗收結果保存於 `.aeris/state/`，屬本機 evidence，不應自動上傳 public GitHub。
