@echo off
setlocal
cd /d "%~dp0"
if not exist .venv-auto\Scripts\python.exe (
  echo Run INSTALL_AUTO_PUBLISH.bat first.
  pause
  exit /b 1
)
.venv-auto\Scripts\python.exe -m py_compile auto_publish.py
if errorlevel 1 (
  echo Python syntax test failed.
  pause
  exit /b 1
)
.venv-auto\Scripts\python.exe -c "import requests, PIL, edge_tts, googleapiclient, google_auth_oauthlib; print('Dependencies OK')"
if errorlevel 1 (
  echo Dependency test failed.
  pause
  exit /b 1
)
echo.
echo Syntax and dependency tests passed. No video has been uploaded.
echo To test rendering only, use: .venv-auto\Scripts\python.exe auto_publish.py --slot 09:00 --dry-run
echo Dry-run still calls the AI API and renders a video but never uploads.
pause
