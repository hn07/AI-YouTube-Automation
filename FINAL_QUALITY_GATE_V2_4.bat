@echo off
setlocal
cd /d "%~dp0"
set "PYTHON=python"
if exist "venv\Scripts\python.exe" set "PYTHON=venv\Scripts\python.exe"
:MENU
cls
echo ==========================================
echo   AI YouTube Final Quality Gate V2.4
echo   Checks metadata only - no upload
echo ==========================================
echo 1. Check a rendered MP4
echo 2. Check a V2.3 render_manifest.json
echo 3. Exit
echo.
set "CHOICE="
set /p "CHOICE=Choose 1-3: "
if "%CHOICE%"=="1" goto VIDEO
if "%CHOICE%"=="2" goto MANIFEST
if "%CHOICE%"=="3" goto END
echo Invalid choice.
pause
goto MENU

:VIDEO
set "INPUT="
set /p "INPUT=Full path to MP4: "
if not defined INPUT goto MENU
"%PYTHON%" src\final_video_quality_v2_4.py "%INPUT%"
pause
goto MENU

:MANIFEST
set "INPUT="
set /p "INPUT=Full path to render_manifest.json: "
if not defined INPUT goto MENU
"%PYTHON%" src\final_video_quality_v2_4.py "%INPUT%"
pause
goto MENU

:END
endlocal
exit /b 0
