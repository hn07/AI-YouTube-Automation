@echo off
setlocal
cd /d "%~dp0"
if not exist venv\Scripts\python.exe (
  echo Hay chay INSTALL_LOCAL.bat truoc.
  pause
  exit /b 1
)
if not exist local-output mkdir local-output
start "" http://localhost:8501
venv\Scripts\python.exe -m streamlit run local_studio.py --server.address 127.0.0.1 --server.port 8501
pause
