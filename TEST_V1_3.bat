@echo off
setlocal
cd /d "%~dp0"
if not exist logs mkdir logs
echo AI YouTube Automation V1.3 test - %DATE% %TIME% > logs\v1_3_test.log
if not exist venv\Scripts\python.exe (
  echo FAIL: venv missing. Run INSTALL_V1.bat first.
  echo FAIL: venv missing >> logs\v1_3_test.log
  pause
  exit /b 1
)
echo [1] Python version
venv\Scripts\python.exe --version >> logs\v1_3_test.log 2>&1
echo [2] Dependencies
venv\Scripts\python.exe -c "import streamlit, PIL, edge_tts, googleapiclient, google_auth_oauthlib; print('Imports OK')" >> logs\v1_3_test.log 2>&1
if errorlevel 1 goto failed
echo [3] Compile dashboard, daily runner, and modules
venv\Scripts\python.exe -m compileall -q app.py daily_runner.py src >> logs\v1_3_test.log 2>&1
if errorlevel 1 goto failed
echo [4] Topic generator smoke test (no network / no upload)
venv\Scripts\python.exe -c "from src.topic_generator import TOPICS; assert len(TOPICS)>=30; assert len(TOPICS)==len(set(TOPICS)); print('Topic bank OK:',len(TOPICS))" >> logs\v1_3_test.log 2>&1
if errorlevel 1 goto failed
echo [5] FFmpeg and ffprobe
where ffmpeg >> logs\v1_3_test.log 2>&1
where ffprobe >> logs\v1_3_test.log 2>&1
echo [6] OAuth client presence (not required for syntax check)
if exist credentials\client_secret.json (echo OAuth client found >> logs\v1_3_test.log) else (echo WARNING: OAuth client missing >> logs\v1_3_test.log)
echo PASS: syntax/dependency/topic-bank checks completed. Review logs\v1_3_test.log for FFmpeg/OAuth warnings.
echo PASS >> logs\v1_3_test.log
type logs\v1_3_test.log
pause
exit /b 0
:failed
echo FAIL: inspect logs\v1_3_test.log
echo FAIL >> logs\v1_3_test.log
type logs\v1_3_test.log
pause
exit /b 1
