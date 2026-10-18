@echo off
setlocal
cd /d "%~dp0"
title AI YouTube Production Pipeline V2.0
:menu
cls
echo ==========================================
echo   AI YouTube Production Pipeline V2.0
echo   Local workflow - no auto upload/publish
echo ==========================================
echo 1. Create a new production job
echo 2. List production jobs
echo 3. Check a job's script
echo 4. Record manual approval (does not publish)
echo 5. Exit
echo.
set /p choice=Choose 1-5: 
if "%choice%"=="1" goto newjob
if "%choice%"=="2" goto listjobs
if "%choice%"=="3" goto checkjob
if "%choice%"=="4" goto approvejob
if "%choice%"=="5" exit /b 0
echo Invalid choice.
pause
goto menu
:newjob
set "topic="
set /p topic=Topic: 
if not defined topic (
  echo Topic is required.
  pause
  goto menu
)
set "title="
set /p title=Video title (optional, can edit job later): 
set "seconds=45"
set /p seconds=Target duration in seconds [45]: 
if not defined seconds set "seconds=45"
python src\production_pipeline.py new --topic "%topic%" --title "%title%" --target-seconds %seconds%
echo.
echo Next: open the new JSON under output\pipeline_jobs and set description and script_path.
pause
goto menu
:listjobs
python src\production_pipeline.py list
pause
goto menu
:checkjob
set "jobid="
set /p jobid=Job ID: 
if not defined jobid goto menu
python src\production_pipeline.py check "%jobid%"
pause
goto menu
:approvejob
set "jobid="
set /p jobid=Job ID: 
if not defined jobid goto menu
set "note="
set /p note=Review note (required): 
if not defined note (
  echo Approval note is required.
  pause
  goto menu
)
python src\production_pipeline.py approve "%jobid%" --note "%note%"
pause
goto menu
