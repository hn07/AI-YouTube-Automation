@echo off
setlocal
cd /d "%~dp0"
if exist "venv\Scripts\python.exe" (set "PYTHON=venv\Scripts\python.exe") else (set "PYTHON=python")
echo AI YouTube Automation V1.7 tests
"%PYTHON%" -m py_compile dashboard_v1_7.py
if errorlevel 1 goto :fail
"%PYTHON%" -c "import dashboard_v1_7 as d; assert isinstance(d.load_jobs(), list); assert isinstance(d.load_registry(), list); assert isinstance(d.load_research(), list); print('Dashboard data loaders PASS')"
if errorlevel 1 goto :fail
echo PASS - tests do not render or upload videos.
exit /b 0
:fail
echo FAIL - check Python and Streamlit dependencies.
exit /b 1
