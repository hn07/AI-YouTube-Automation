@echo off
setlocal
cd /d "%~dp0"
set "PYTHON=python"
if exist "venv\Scripts\python.exe" set "PYTHON=venv\Scripts\python.exe"
echo ==========================================
echo   V2.4 Offline Final Quality Gate Tests
echo ==========================================
"%PYTHON%" --version
if errorlevel 1 goto FAIL
"%PYTHON%" -m py_compile src\final_video_quality_v2_4.py src\test_v2_4.py
if errorlevel 1 goto FAIL
"%PYTHON%" -m unittest src.test_v2_4
if errorlevel 1 goto FAIL
"%PYTHON%" src\final_video_quality_v2_4.py --help
if errorlevel 1 goto FAIL
echo.
echo V2.4 offline tests passed.
echo Tests use mocked ffprobe data; no real render, network, or upload was performed.
pause
exit /b 0
:FAIL
echo.
echo V2.4 tests FAILED. Copy the full error output for troubleshooting.
pause
exit /b 1
