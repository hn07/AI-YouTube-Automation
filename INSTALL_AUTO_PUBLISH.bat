@echo off
setlocal
cd /d "%~dp0"
echo ================================================
echo AI-YouTube-Automation - Auto Publish Setup
echo ================================================
where py >nul 2>nul
if errorlevel 1 (
  echo Python launcher not found. Install Python 3.11 or 3.12 and enable PATH.
  pause
  exit /b 1
)
py -3.12 -m venv .venv-auto
if errorlevel 1 py -3.11 -m venv .venv-auto
if errorlevel 1 (
  echo Could not create venv. Install Python 3.11 or 3.12.
  pause
  exit /b 1
)
call .venv-auto\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements-local.txt
if errorlevel 1 (
  echo Dependency installation failed.
  pause
  exit /b 1
)
if not exist .env copy .env.example .env
if not exist auto-publish-state.sqlite3 echo Database will be created on first run.
echo.
echo Next: edit .env with your OpenRouter key, then run TEST_AUTO_PUBLISH.bat.
pause
