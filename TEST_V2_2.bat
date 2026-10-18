@echo off
setlocal
cd /d "%~dp0"
echo ==========================================
echo   V2.2 Offline Tests
echo ==========================================
python --version
if errorlevel 1 goto FAIL
python -m py_compile src\fact_check_v2_2.py src\test_v2_2.py
if errorlevel 1 goto FAIL
python -m unittest src.test_v2_2
if errorlevel 1 goto FAIL
python src\fact_check_v2_2.py --help
if errorlevel 1 goto FAIL
echo.
echo V2.2 offline tests passed.
echo No source URLs were fetched; no video was rendered or published.
pause
exit /b 0
:FAIL
echo.
echo V2.2 tests FAILED. Copy the full error output for troubleshooting.
pause
exit /b 1
