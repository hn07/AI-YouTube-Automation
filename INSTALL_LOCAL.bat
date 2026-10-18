@echo off
setlocal
cd /d "%~dp0"
if not exist logs mkdir logs
echo Nham YouTube Studio Local installer - %DATE% %TIME% > logs\install-local.log
set "PY="
py -3.12 --version >> logs\install-local.log 2>&1
if not errorlevel 1 set "PY=py -3.12"
if not defined PY (
  py -3.11 --version >> logs\install-local.log 2>&1
  if not errorlevel 1 set "PY=py -3.11"
)
if not defined PY (
  echo Chua tim thay Python 3.11/3.12.
  echo Cai Python tu https://www.python.org/downloads/ va chon Add Python to PATH.
  pause
  exit /b 1
)
if not exist venv (
  %PY% -m venv venv >> logs\install-local.log 2>&1
  if errorlevel 1 goto failed
)
venv\Scripts\python.exe -m pip install --upgrade pip >> logs\install-local.log 2>&1
if errorlevel 1 goto failed
venv\Scripts\python.exe -m pip install -r requirements-local.txt >> logs\install-local.log 2>&1
if errorlevel 1 goto failed
if not exist local-output mkdir local-output
where ffmpeg >nul 2>nul
if errorlevel 1 if not exist tools\ffmpeg\bin\ffmpeg.exe echo CAN CAI FFmpeg. Xem LOCAL_STUDIO_GUIDE.md.
echo Cai dat Python hoan tat. Log: logs\install-local.log
pause
exit /b 0
:failed
echo Cai dat that bai. Mo logs\install-local.log
pause
exit /b 1
