@echo off
setlocal
chcp 65001 >nul
title AI YouTube Automation V2.5 - One Click
cd /d "%~dp0"

echo ============================================================
echo AI YouTube Automation V2.5 - ONE-CLICK LOCAL PRODUCTION
echo ============================================================
echo This tool never uploads or publishes.
echo It will not fake human approval or fact verification.
echo.

if exist "venv\Scripts\python.exe" (
  set "PYTHON=venv\Scripts\python.exe"
) else (
  set "PYTHON=python"
)

"%PYTHON%" --version
if errorlevel 1 (
  echo ERROR: Python was not found. Install Python or restore the project venv.
  pause
  exit /b 2
)

set /p JOB_ID=Enter existing Job ID (example 20261018_165128_af84e9): 
if "%JOB_ID%"=="" (
  echo ERROR: Job ID cannot be empty.
  pause
  exit /b 2
)

echo.
echo Running safe preflight and production gates for %JOB_ID%...
"%PYTHON%" "src\one_click_production_v2_5.py" "%JOB_ID%"
set "RESULT=%ERRORLEVEL%"
echo.
if "%RESULT%"=="0" (
  echo Production completed. Watch the entire MP4 before any upload.
) else if "%RESULT%"=="2" (
  echo Production BLOCKED. Read the blocker list and V2.5 run report above.
) else (
  echo Production did not complete successfully. Read the report above.
)
echo No upload or publishing was performed.
echo.
pause
exit /b %RESULT%
