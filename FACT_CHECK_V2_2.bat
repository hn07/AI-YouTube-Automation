@echo off
setlocal
cd /d "%~dp0"
:MENU
cls
echo ==========================================
echo   AI YouTube Fact-Check V2.2
echo   Human evidence register - no publishing
echo ==========================================
echo 1. Prepare claim checklist from a job script
echo 2. Evaluate edited claim checklist
echo 3. Exit
echo.
set "CHOICE="
set /p "CHOICE=Choose 1-3: "
if "%CHOICE%"=="1" goto PREPARE
if "%CHOICE%"=="2" goto EVALUATE
if "%CHOICE%"=="3" goto END
echo Invalid choice.
pause
goto MENU

:PREPARE
set "JOB_ID="
set /p "JOB_ID=Job ID: "
if not defined JOB_ID (
  echo Job ID is required.
  pause
  goto MENU
)
set "SCRIPT="
set /p "SCRIPT=Optional script path [blank uses job script_path]: "
python src\fact_check_v2_2.py prepare "%JOB_ID%" --script "%SCRIPT%"
pause
goto MENU

:EVALUATE
set "JOB_ID="
set /p "JOB_ID=Job ID: "
if not defined JOB_ID (
  echo Job ID is required.
  pause
  goto MENU
)
set "REGISTER="
set /p "REGISTER=Register JSON path [blank uses default register]: "
if defined REGISTER (
  python src\fact_check_v2_2.py evaluate "%JOB_ID%" --register "%REGISTER%"
) else (
  python src\fact_check_v2_2.py evaluate "%JOB_ID%"
)
pause
goto MENU

:END
endlocal
exit /b 0
