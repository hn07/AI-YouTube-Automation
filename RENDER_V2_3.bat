@echo off
setlocal
cd /d "%~dp0"
:MENU
cls
echo ==========================================
echo   AI YouTube Rendering Pipeline V2.3
echo   Local render only - no upload/publish
echo ==========================================
echo 1. Render an approved production job
echo 2. Exit
echo.
set "CHOICE="
set /p "CHOICE=Choose 1-2: "
if "%CHOICE%"=="1" goto RENDER
if "%CHOICE%"=="2" goto END
echo Invalid choice.
pause
goto MENU

:RENDER
set "JOB_ID="
set /p "JOB_ID=Job ID: "
if not defined JOB_ID (
  echo Job ID is required.
  pause
  goto MENU
)
echo.
echo IMPORTANT: Rendering uses FFmpeg and online Edge TTS.
echo It creates a local MP4 only; it will not upload or publish.
set "CONFIRM="
set /p "CONFIRM=Type RENDER to authorize rendering: "
if /I not "%CONFIRM%"=="RENDER" (
  echo Cancelled. No rendering started.
  pause
  goto MENU
)
set "VOICE=en-US-AriaNeural"
echo Choose voice: 1=Aria, 2=Guy, 3=Jenny
set "VOICE_CHOICE="
set /p "VOICE_CHOICE=Voice [1]: "
if "%VOICE_CHOICE%"=="2" set "VOICE=en-US-GuyNeural"
if "%VOICE_CHOICE%"=="3" set "VOICE=en-US-JennyNeural"
python src\render_pipeline_v2_3.py "%JOB_ID%" --confirm-render --voice "%VOICE%"
pause
goto MENU

:END
endlocal
exit /b 0
