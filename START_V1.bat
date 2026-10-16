@echo off
setlocal
cd /d "%~dp0"
if not exist venv\Scripts\python.exe (
  echo Please run INSTALL_V1.bat first.
  pause
  exit /b 1
)
if not exist logs mkdir logs
if not exist output mkdir output
if not exist work mkdir work
venv\Scripts\python.exe -m streamlit run app.py
pause
