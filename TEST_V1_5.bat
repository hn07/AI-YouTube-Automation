@echo off
setlocal
cd /d "%~dp0"
if not exist venv\Scripts\python.exe (
  echo FAIL: venv missing. Run INSTALL_V1.bat first.
  pause
  exit /b 1
)
if not exist logs mkdir logs
set LOG=logs\v1_5_test.log
echo AI YouTube Automation V1.5 test - %DATE% %TIME% > "%LOG%"
echo [1] Compile Python files
venv\Scripts\python.exe -m compileall -q app.py daily_runner.py src >> "%LOG%" 2>&1
if errorlevel 1 goto failed
echo [2] Local fallback generation without API key
venv\Scripts\python.exe -c "import os; [os.environ.pop(k,None) for k in ('AI_API_BASE_URL','AI_API_KEY','AI_MODEL')]; from src.script_writer import generate_script; from src.ai_script_provider import generate; s=generate_script('Why is the ocean salty?'); assert isinstance(s,str) and len(s)>100; assert generate('Why is the ocean salty?') is None; print('Fallback OK; words:',len(s.split()))" >> "%LOG%" 2>&1
if errorlevel 1 goto failed
echo [3] Topic bank
venv\Scripts\python.exe -c "from src.topic_generator import TOPICS; assert len(TOPICS)==len(set(TOPICS)); print('Topic bank OK:',len(TOPICS))" >> "%LOG%" 2>&1
if errorlevel 1 goto failed
echo PASS: local smoke tests completed. No network call or upload was performed.
echo PASS >> "%LOG%"
type "%LOG%"
pause
exit /b 0
:failed
echo FAIL: inspect %LOG%
echo FAIL >> "%LOG%"
type "%LOG%"
pause
exit /b 1
