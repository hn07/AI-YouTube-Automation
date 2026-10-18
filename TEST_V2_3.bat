@echo off
setlocal
cd /d "%~dp0"
echo ==========================================
echo   V2.3 Offline Rendering Gate Tests
echo ==========================================
python --version
if errorlevel 1 goto FAIL
python -m py_compile src\render_pipeline_v2_3.py src\test_v2_3.py
if errorlevel 1 goto FAIL
python -m unittest src.test_v2_3
if errorlevel 1 goto FAIL
python src\render_pipeline_v2_3.py --help
if errorlevel 1 goto FAIL
echo.
echo V2.3 offline tests passed.
echo Tests used a fake renderer; no TTS, FFmpeg, network, or upload was used.
pause
exit /b 0
:FAIL
echo.
echo V2.3 tests FAILED. Copy the full error output for troubleshooting.
pause
exit /b 1
