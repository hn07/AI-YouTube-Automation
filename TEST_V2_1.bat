@echo off
setlocal
cd /d "%~dp0"
echo ==========================================
echo   V2.1 Offline Smoke Tests
echo ==========================================
python --version
if errorlevel 1 goto FAIL
python -m py_compile src\ai_research_integration.py src\test_v2_1.py
if errorlevel 1 goto FAIL
python -m unittest src.test_v2_1
if errorlevel 1 goto FAIL
python src\ai_research_integration.py --help
if errorlevel 1 goto FAIL
echo.
echo V2.1 offline tests passed.
echo No AI API, RSS network, rendering, or upload was used.
pause
exit /b 0
:FAIL
echo.
echo V2.1 tests FAILED. Copy the full error output for troubleshooting.
pause
exit /b 1
