@echo off
setlocal
cd /d "%~dp0"
echo AI YouTube Automation - V1.8 QUALITY CHECK
set /p SCRIPT_PATH=Enter full path to UTF-8 .txt script: 
if "%SCRIPT_PATH%"=="" exit /b 2
set /p VIDEO_TITLE=Enter video title (optional): 
set /p VIDEO_DESC=Enter description (optional): 
if not exist output\quality_reports mkdir output\quality_reports
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss_fff"') do set STAMP=%%i
set REPORT_PATH=output\quality_reports\quality_%STAMP%.json
python src\content_quality.py "%SCRIPT_PATH%" --title "%VIDEO_TITLE%" --description "%VIDEO_DESC%" --report "%REPORT_PATH%"
set RESULT=%ERRORLEVEL%
echo This tool does not rewrite source files or upload videos.
pause
exit /b %RESULT%
