# Portable Company Image

`portable/` 定義「整棟公司搬家」的邊界。

A Git checkout/ZIP contains the redistributable company image. To create a **true air-gapped deployment bundle**, optionally stage local-only assets under `portable_assets/` before packaging:

```text
portable_assets/
├── models/          local model weights / Ollama export or equivalent
├── installers/      pre-approved inference/runtime installers
├── drivers/         redistributable hardware drivers
└── licenses/        only when license terms permit local packaging
```

`portable_assets/` should not be committed by default. The packaging script includes it only when present.

A deployment is not offline-complete until `doctor` confirms a reachable local provider/model.