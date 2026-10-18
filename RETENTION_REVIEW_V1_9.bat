@echo off
setlocal
cd /d "%~dp0"
echo AI YouTube Automation - V1.9 RETENTION REVIEW
set /p SCRIPT_PATH=Enter full path to UTF-8 .txt script: 
if "%SCRIPT_PATH%"=="" exit /b 2
set /p TARGET_SECONDS=Target narration duration in seconds (default 45): 
if "%TARGET_SECONDS%"=="" set TARGET_SECONDS=45
if not exist output\retention_reports mkdir output\retention_reports
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss_fff"') do set STAMP=%%i
set REPORT_PATH=output\retention_reports\retention_%STAMP%.json
python src\retention_review.py "%SCRIPT_PATH%" --target-seconds %TARGET_SECONDS% --report "%REPORT_PATH%"
set RESULT=%ERRORLEVEL%
echo This tool does not rewrite scripts, render videos, or upload videos.
pause
exit /b %RESULT%
