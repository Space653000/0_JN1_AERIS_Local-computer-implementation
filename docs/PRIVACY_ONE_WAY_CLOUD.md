# AERIS One-Way Cloud Privacy Contract

## 不可妥協的方向

```text
PUBLIC CLOUD / INTERNET
        │ public query / public download
        ▼
LOCAL AERIS
        ├─ knowledge DB
        ├─ private memory
        ├─ customer/project data
        ├─ measurement/evidence
        └─ local AI

LOCAL PRIVATE DATA ─────X─────► CLOUD
```

AERIS 預設所有本機資料為 `LOCAL_ONLY`。Cloud AI 不得自動收到 local files、Memory、Evidence、客戶資料、量測資料、CAE result、private history 或 instrument logs。

## Cloud AI

```bash
python -m aeris_runtime research "公開領域問題"
```

只送當下 public query，不載入本機 Knowledge DB/Memory/Evidence；回應保存到 `.aeris/ingress/cloud/`。

## 公開資訊下載

```bash
python -m aeris_runtime ingress "https://example.com/public-document"
```

保存 payload、URL、content type、bytes、SHA-256 manifest 到 `.aeris/ingress/web/`。

## 私人工程工作

```bash
python -m aeris_runtime chat "分析我的本機專案"
```

硬性 local-only。即使 mode=`cloud` 也不把本機工程內容送到 cloud。

若 Cloud AI 必須看到本地專案資料才能回答，這與 no-egress 直接衝突；AERIS 保密優先，改用 Local AI。
