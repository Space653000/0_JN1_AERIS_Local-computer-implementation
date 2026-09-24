# AERIS ACCEPTANCE — 驗收標準

> 本文件定義「什麼才算真的完成」。它引用 Core 的 GATE-04/05（見 `.ai/BLUEPRINT.md` §1），
> 並記錄本 repo 實際使用的驗收機制。沒有寫在這裡、也沒有真實 Evidence 的完成宣稱一律視為
> **NOT VERIFIED**。

## 1. 最上層原則（來自 Core constitution.md，未刪減，只摘錄）

- **GATE-04 Evidence Before DONE**：每個 DONE 必須同時有實際執行、可重現測試、Expected
  Result、Actual Result、PASS/FAIL、Log/Screenshot/Output/Report、對應 Requirement ID。
  缺任一項 → `STATUS = NOT VERIFIED`。文件存在不是完成的證據；CI 不證明本機模型、量測或
  公司完成。
- **GATE-05 禁止自我證明**：AI 宣稱完成不算驗收。關鍵架構、重大功能、Release Gate 須隔離
  審查者或獨立重新執行驗證；作者不得同一 context 自行核准。
- `NO EVIDENCE = NOT DONE`。

## 2. 本 repo 的自動化驗收機制（P0–P6 Progress Truth，54 項）

真值來源：`aeris_runtime/progress_verify.py`（`CHECKS` 字典，54 個 P0.x–P6.x 項目）+
`.aeris/evidence/progress/PROGRESS_TRUTH.json`。**這是本 repo 目前最接近「機器可重新驗證的
驗收清單」的東西**，不是文件宣稱。

重新驗證指令：

```powershell
.venv\Scripts\python.exe -m aeris_runtime.progress_verify
```

每一項的判定方式已寫死在程式碼裡（多數是「跑對應單元測試 + 檢查特定檔案/欄位存在」），
不是主觀評分。輸出的 JSON 每項都有 `result: PASS|FAIL` 與 `detail`，可重新產生、可稽核。

## 3. 「100 席位」的驗收分級（避免灌水）

Core 的 GATE-01 明確警告「100 capability seats 不等於 100 成熟工程師」。本 repo 用以下
成熟度分級（`aeris_runtime/engineering/factory.py` 的 `verification_rubric`）：

| 等級 | 意義 |
| --- | --- |
| L0 | 只在角色登記表，沒有契約框架 |
| L1 | 有完整契約框架，尚未執行 |
| L2 | 所有對應的本機技能已執行並封存證據（`RoleAcceptanceFactory`） |
| L3 | 個別角色有獨立領域驗收（獨立決策 oracle + 合格複查） |
| L4 | 真實儀器／校正／人工專家核准 — **這個工廠本身不能自己發出 L4** |

「技能深度」（每個角色的第二、第三個真實技能）是 L2 之上的**額外**維度，不是取代 L2 計數，
見 `docs/AERIS_P5_ENGINEER_FACTORY.md` 的「Addendum (2026-09-19)」段落。

## 4. 本 session 對「新增技能」訂出的具體驗收步驟（可重複套用）

這不是憑空的流程，是這個 session 實際走過、且被驗證有效的順序：

1. **手算驗證公式**——用獨立 Python 腳本，不看程式碼實作，先算出正確數值。任何無法在
   合理時間內查證係數來源的模型（例如 Zwikker-Kosten 熱黏滯窄管模型、Ingard-Rayleigh 網
   目阻抗模型）**主動放棄**，不用記憶猜測係數。
2. **讀既有技能的原始碼**，確認要新增的東西不是既有技能已經在算的東西（本 session 至少
   兩次因為沒做這步而重工：R009/R011/R040 的物理量已經被 `sealed_alignment.py` /
   `ported_alignment.py` / `array_doa_review.py` 算過；R089/R090/R094 的邏輯已經被
   `standard_metadata.py` / `faca.py` 算過）。
3. **建立四件套**：`skills/<id>/{manifest.json, input.schema.json, output.schema.json,
   SKILL.md}` + `methods/roles/<id>.json` + `golden/roles/R0XX/<name>.json`（黃金測試套件
   必須涵蓋 `positive` / `boundary` / `negative` / `counter_hypothesis` 四種案例）。
4. **`run_skill()` 直接呼叫**驗證數值與手算完全吻合，再驗證邊界/錯誤輸入確實被拒絕。
5. **`professional_profiles.py` 註冊**（`ROLE_DOMAIN_CONTRACTS[role].append(...)`），並確認
   該角色的 list 在這行程式碼執行時已經存在（曾經因為插入點在 list 建立之前而 `KeyError`）。
6. `tests/test_<name>_domain.py` 透過 `run_skill()`（不是直接呼叫函式）驗證。
7. `factory.materialize()` + `scripts/run_capability_factory.py --workers 8` + 對每個新
   contract 呼叫 `RoleAcceptanceFactory().evaluate(role_id, skill_id)` 重新封存全部 100
   角色的證據。
8. 跑 `tests.test_capability_factory` + 完整 `test_role*.py` 系列確認沒有連帶壞掉。
9. 更新 `total_role_golden_suites` / `total_role_golden_cases` 兩個寫死在
   `tests/test_role_acceptance.py` 的數字（用 `factory.matrix()` 的即時值，不是心算）。
10. Commit + push；不 squash、不 force push、不改 main（見 `.ai/BLUEPRINT.md` GATE-02/03）。

## 5. 更高一層的「真的能用」驗收（本 session 額外做的，比上面更嚴格）

單元測試通過 ≠ 真的能用。本 session 額外做了兩層更嚴格的驗證：

- **透過 `run_role()` 正式生產流程執行**（不是 `run_skill()` 單元測試捷徑），確認會產生
  真實 `task_id` / `workflow_id` / `evidence_run_id`，`state == "EVIDENCED"`。
- **獨立重新計算證據封存包裡每個檔案的 SHA-256**，跟 `checksums.sha256` 比對，證明資料
  沒有被竄改、確實是這次執行產生的（不是預先塞好的假資料）。

`scripts/exam_100_engineers.py` 把這兩層驗證自動化，對全部有領域技能的角色（現況見
`.ai/STATUS.md`）重放黃金測試套件裡的每一種案例。**這支腳本本身就是「驗收標準」的一部分，
不是一次性腳本**，之後每次擴充技能都應該重跑一次確認沒有連帶壞掉既有技能。

## 6. 人類專屬關卡（AI 不能自己核准）

以下項目**依設計**必須由人類 Chief Engineer 執行/核准，AI 不能代勞、也不應該假裝已完成：

- G5 正式簽核（`aeris_runtime/engineering/l3_award.py` 的 `human_decide()`，需要具名核准者）。
- 真正的 Hard Offline 測試（斷網後重開機驗證）。
- Windows Task Scheduler / 開機自啟排程複查。
- R3/R4 風險等級的正式發布決策（`config/risk_authority.json`：`ai_may_self_approve_r3_or_r4`
  必須是 `false`）。

## 7. 「STATUS.md 怎麼寫」的規則

`.ai/STATUS.md` 的每一條「已完成」都必須能對應到上面某一種驗收方式，並附上可重新執行的
指令或檔案路徑；不能只寫「應該做完了」。找不到對應驗收方式的一律寫 `NOT VERIFIED` 或
`UNKNOWN`，不能省略。
