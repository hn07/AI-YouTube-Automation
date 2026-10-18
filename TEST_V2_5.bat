@echo off
setlocal
chcp 65001 >nul
title AI YouTube Automation V2.5 - Test
cd /d "%~dp0"
if exist "venv\Scripts\python.exe" (
  set "PYTHON=venv\Scripts\python.exe"
) else (
  set "PYTHON=python"
)
echo Checking Python syntax for V2.5 and V2.4...
"%PYTHON%" -m py_compile "src\one_click_production_v2_5.py" "src\final_video_quality_v2_4.py" "src\render_pipeline_v2_3.py"
if errorlevel 1 (
  echo TEST FAILED: Python syntax check did not pass.
  pause
  exit /b 1
)
echo PASS: Python syntax checks.
echo This is a syntax smoke test only; it does not prove FFmpeg/TTS or rendering works.
echo No files were deleted and no video was uploaded.
pause
exit /b 0
