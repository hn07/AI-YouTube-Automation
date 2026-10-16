@echo off
setlocal
cd /d "%~dp0"
if not exist logs mkdir logs
echo ================================================== > logs\install.log
echo AI YouTube Automation V1 installer >> logs\install.log
echo Started: %DATE% %TIME% >> logs\install.log
echo ==================================================
echo [1/5] Checking Python...
where py >nul 2>nul
if errorlevel 1 (
  echo ERROR: Python launcher not found. Install Python 3.11 or 3.12 and enable Add Python to PATH.
  echo Python launcher not found >> logs\install.log
  pause
  exit /b 1
)
py -3.12 --version >> logs\install.log 2>&1
if errorlevel 1 (
  py -3.11 --version >> logs\install.log 2>&1
  if errorlevel 1 (
    echo ERROR: Python 3.11 or 3.12 not found. Please install one of them.
    echo Python 3.11/3.12 not found >> logs\install.log
    pause
    exit /b 1
  )
  set "PY=py -3.11"
) else (
  set "PY=py -3.12"
)
echo [2/5] Creating isolated virtual environment...
if not exist venv (
  %PY% -m venv venv >> logs\install.log 2>&1
  if errorlevel 1 goto failed
) else (
  echo Existing venv found; reusing it.
)
echo [3/5] Upgrading pip...
venv\Scripts\python.exe -m pip install --upgrade pip >> logs\install.log 2>&1
if errorlevel 1 goto failed
echo [4/5] Installing dependencies (Internet required)...
venv\Scripts\python.exe -m pip install -r requirements.txt >> logs\install.log 2>&1
if errorlevel 1 goto failed
echo [5/5] Creating local folders...
if not exist output mkdir output
if not exist work mkdir work
if not exist logs mkdir logs
if not exist credentials mkdir credentials
echo INSTALL SUCCESS. See logs\install.log
echo Install completed: %DATE% %TIME% >> logs\install.log
pause
exit /b 0
:failed
echo INSTALL FAILED. See logs\install.log
echo Install failed: %DATE% %TIME% >> logs\install.log
pause
exit /b 1
