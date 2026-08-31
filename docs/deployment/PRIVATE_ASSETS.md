# Private Asset Pack

不進 public GitHub：model weights、API keys、商用 license material、受限 installer、customer data、raw WAV/HDF5/Parquet/CAE archives、instrument credentials、private calibration packages。

Air-gapped 搬遷時可在本機建立：

```text
portable_assets/
├─ models/
├─ installers/
├─ drivers/
├─ licenses/
├─ calibration/
└─ private-seed-data/
```

`portable_assets/` 預設 gitignored，只在 Human-controlled packaging 加入離線 bundle。每個 private asset 應有本地 manifest：名稱、版本、來源、license/redistribution status、SHA-256、適用 machine profile。
