@echo off
setlocal
cd /d "%~dp0"
if not exist logs mkdir logs
echo Local Studio test - %DATE% %TIME% > logs\test-local.log
if not exist venv\Scripts\python.exe (
 echo FAIL: Chay INSTALL_LOCAL.bat truoc.
 pause
 exit /b 1
)
venv\Scripts\python.exe -c "import streamlit, PIL, requests, edge_tts; print('Imports OK')" >> logs\test-local.log 2>&1
if errorlevel 1 goto failed
venv\Scripts\python.exe -m compileall -q local_studio.py src >> logs\test-local.log 2>&1
if errorlevel 1 goto failed
echo PASS: Python va syntax OK. >> logs\test-local.log
where ffmpeg >> logs\test-local.log 2>&1
if errorlevel 1 if not exist tools\ffmpeg\bin\ffmpeg.exe echo WARNING: FFmpeg missing. >> logs\test-local.log
echo PASS. Xem logs\test-local.log
pause
exit /b 0
:failed
echo FAIL. Xem logs\test-local.log
pause
exit /b 1
