@echo off
setlocal
set SCRIPT_DIR=%~dp0
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%AERIS_START.ps1" %*
set EXITCODE=%ERRORLEVEL%
echo.
if %EXITCODE% NEQ 0 (
  echo 啟動點檢有項目未通過，請往上捲動檢查詳細訊息 / Some startup checks failed -- scroll up for details.
) else (
  echo 系統已啟動並通過全部點檢 / System started and passed all checks.
)
echo.
pause
exit /b %EXITCODE%
