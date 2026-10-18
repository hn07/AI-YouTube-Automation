@echo off
setlocal
cd /d "%~dp0"
if exist "venv\Scripts\python.exe" (
  set "PYTHON=venv\Scripts\python.exe"
) else (
  set "PYTHON=python"
)
"%PYTHON%" -c "import streamlit" >nul 2>&1
if errorlevel 1 (
  echo Streamlit is not installed in this Python environment.
  echo Run INSTALL_V1.bat or install requirements.txt first.
  pause
  exit /b 1
)
echo Starting read-only V1.7 dashboard...
echo Open http://127.0.0.1:8502 in your browser.
"%PYTHON%" -m streamlit run dashboard_v1_7.py --server.address 127.0.0.1 --server.port 8502
pause
