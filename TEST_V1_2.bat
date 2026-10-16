@echo off
setlocal
cd /d "%~dp0"
if not exist logs mkdir logs
echo AI YouTube Automation V1.2 test - %DATE% %TIME% > logs\v1_2_test.log
if not exist venv\Scripts\python.exe (
  echo FAIL: venv missing. Run INSTALL_V1.bat first.
  echo FAIL: venv missing >> logs\v1_2_test.log
  pause
  exit /b 1
)
echo [1] Python version
venv\Scripts\python.exe --version >> logs\v1_2_test.log 2>&1
echo [2] Dependencies
venv\Scripts\python.exe -c "import streamlit, PIL, edge_tts, googleapiclient, google_auth_oauthlib; print('Imports OK')" >> logs\v1_2_test.log 2>&1
if errorlevel 1 goto failed
echo [3] Compile app and modules
venv\Scripts\python.exe -m compileall -q app.py src >> logs\v1_2_test.log 2>&1
if errorlevel 1 goto failed
echo [4] FFmpeg and ffprobe
where ffmpeg >> logs\v1_2_test.log 2>&1
where ffprobe >> logs\v1_2_test.log 2>&1
echo PASS: dependency and syntax checks completed. FFmpeg availability is recorded in logs\v1_2_test.log.
echo PASS >> logs\v1_2_test.log
type logs\v1_2_test.log
pause
exit /b 0
:failed
echo FAIL: inspect logs\v1_2_test.log
echo FAIL >> logs\v1_2_test.log
type logs\v1_2_test.log
pause
exit /b 1
