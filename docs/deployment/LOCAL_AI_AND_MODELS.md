# Local AI and Model Deployment

Baseline provider: Ollama-compatible API. Default model: `qwen2.5:3b`。

- Git 不存 model weights。
- 有網路時 installer 可拉 local model。
- Air-gapped 時事先將合法可搬遷資產放 `portable_assets/models/` 或使用已安裝 Ollama model store。
- Model 是算力，不是 AERIS 身份。

Sizing guideline：CPU/8–16GB 優先 3B；16GB unified/VRAM 可評估 3B–7B；24GB+ GPU 可評估更大模型但必須實測；Jetson 優先穩定低記憶體模型。

Local provider 可位於 Human-approved trusted LAN node，仍屬 local/private boundary，不是 public cloud。
