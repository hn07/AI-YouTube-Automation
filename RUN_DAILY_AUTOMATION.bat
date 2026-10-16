@echo off
setlocal
cd /d "%~dp0"
if not exist venv\Scripts\python.exe (
  echo Missing venv. Run INSTALL_V1.bat first.
  pause
  exit /b 1
)
if not exist credentials\client_secret.json (
  echo Missing credentials\client_secret.json. Complete YouTube OAuth setup first.
  pause
  exit /b 1
)
if not exist logs mkdir logs
echo Running daily automation manually at %DATE% %TIME% >> logs\daily_automation.log
venv\Scripts\python.exe daily_runner.py
set RESULT=%ERRORLEVEL%
echo Runner exit code %RESULT% >> logs\daily_automation.log
echo.
echo Finished with exit code %RESULT%. See logs\daily_automation.log
pause
exit /b %RESULT%
