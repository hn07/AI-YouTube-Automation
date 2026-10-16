@echo off
setlocal
cd /d "%~dp0"
if not exist logs mkdir logs
echo AI YouTube Automation V1 test - %DATE% %TIME% > logs\test.log
if not exist venv\Scripts\python.exe (
  echo FAIL: venv missing. Run INSTALL_V1.bat first.
  echo FAIL: venv missing >> logs\test.log
  pause
  exit /b 1
)
echo [1] Python version
venv\Scripts\python.exe --version >> logs\test.log 2>&1
echo [2] Dependency imports
venv\Scripts\python.exe -c "import streamlit, PIL, edge_tts, googleapiclient, google_auth_oauthlib; print('Imports OK')" >> logs\test.log 2>&1
if errorlevel 1 goto failed
echo [3] FFmpeg availability
where ffmpeg >> logs\test.log 2>&1
if errorlevel 1 (
  if not exist tools\ffmpeg\bin\ffmpeg.exe (
    echo WARNING: FFmpeg not found on PATH or tools\ffmpeg\bin. Rendering will not work until installed.
    echo WARNING: FFmpeg not found >> logs\test.log
  )
)
echo [4] Project modules compile
venv\Scripts\python.exe -m compileall -q app.py src >> logs\test.log 2>&1
if errorlevel 1 goto failed
echo PASS: dependency and syntax tests completed. Read logs\test.log.
echo PASS >> logs\test.log
pause
exit /b 0
:failed
echo FAIL: inspect logs\test.log
echo FAIL >> logs\test.log
pause
exit /b 1
