# Machine Deployment Profiles

AERIS Company Image 相同；每台電腦只改 Machine Profile 與 Private Asset Pack。

| Profile | Local AI | 典型用途 | 專業工具 |
|---|---|---|---|
| Windows CPU | small model / CPU | 文件、知識、輕量工作 | 依安裝狀態 |
| Windows NVIDIA | Ollama + GPU model | 主力聲學工作站 | MATLAB/COMSOL/APx/KLIPPEL 可本機 |
| Linux x86 NVIDIA | Ollama + GPU | Server / batch / automation | 多數透過 adapter |
| Jetson Orin / J4012 | ARM64 local model | Edge/robot/always-on | 重型 CAE 多採遠端工具節點 |
| Trusted LAN AI Server | local AI service | 多台 AERIS 共用本地大腦 | Human-approved LAN only |

部署固定流程：detect → profile → prerequisites → local model → knowledge build → adapters → tests → deployment report。

另見 `PROFESSIONAL_TOOLS.md`、`LOCAL_AI_AND_MODELS.md`、`PRIVATE_ASSETS.md`。
