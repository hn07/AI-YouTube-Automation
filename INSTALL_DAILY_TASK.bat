@echo off
setlocal
cd /d "%~dp0"
if not exist venv\Scripts\python.exe (
  echo Missing venv. Run INSTALL_V1.bat first.
  pause
  exit /b 1
)
if not exist credentials\client_secret.json (
  echo Missing credentials\client_secret.json.
  echo Add your own YouTube OAuth desktop client first. Do not share it.
  pause
  exit /b 1
)
echo.
echo This creates a Windows Task Scheduler job to run every day at 01:00.
echo It will generate 3 English Shorts, render them, then upload and request
echo YouTube scheduling for 07:00, 11:00, and 18:00 Vietnam time.
echo The task uses this Windows account and requires this PC to be on and awake.
echo Topic generation uses a local bank; it does not use a paid AI API or fact-check claims.
echo.
choice /M "Install the daily auto-upload task"
if errorlevel 2 exit /b 0
schtasks /Create /F /SC DAILY /ST 01:00 /TN "AI YouTube Automation V1.4" /TR "\"%~dp0venv\Scripts\python.exe\" \"%~dp0daily_runner.py\"" /RL LIMITED
if errorlevel 1 (
  echo Task creation failed. Retry from a normal Command Prompt under your Windows account.
  pause
  exit /b 1
)
echo.
echo Task installed. Open Task Scheduler to review or disable "AI YouTube Automation V1.4".
echo To remove it: schtasks /Delete /TN "AI YouTube Automation V1.4" /F
pause
