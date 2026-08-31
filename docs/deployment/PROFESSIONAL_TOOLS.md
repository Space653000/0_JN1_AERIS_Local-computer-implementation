# Professional Tool Deployment Guides

AERIS 不重新散佈商用軟體或 license。Installer 只做偵測、adapter 設定與 preflight。

## MATLAB / Simulink
合法安裝與啟用 license；確認 CLI/path；adapter 記錄 release、toolbox、script hash。

## COMSOL
合法 installer + license manager；確認 batch/API；adapter 記錄 version、model hash、boundary conditions、solver settings。

## Audio Precision APx
安裝 APx software/driver；驗證硬體；software installed 不等於 instrument calibrated。

## KLIPPEL
安裝合法 software/module/license；硬體 self-test/calibration；Evidence 記錄 module/version/calibration/fixture。

## SoundCheck / HEAD ACQUA / Ansys / Simcenter
合法安裝 → license → CLI/API capability → adapter preflight → version/calibration provenance。

未具備工具時只能顯示 `NOT_CONFIGURED` / `REMOTE_ONLY` / `UNAVAILABLE`，不得假 HEALTHY。
