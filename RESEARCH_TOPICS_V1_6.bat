@echo off
setlocal
cd /d "%~dp0"
echo ==========================================
echo AI YouTube Automation V1.6 - Topic Research
echo ==========================================
if exist "venv\Scripts\python.exe" (
  set "PYTHON=venv\Scripts\python.exe"
) else (
  set "PYTHON=python"
)
"%PYTHON%" -c "import sys; print('Python:', sys.version)"
if errorlevel 1 goto :fail
"%PYTHON%" -c "from src.topic_research import discover_topics; items=discover_topics(); print('New candidates:', len(items)); [print(str(i+1)+'. '+x['topic']+'\n   '+x['source_url']) for i,x in enumerate(items)]; print('Saved to output\\researched_topic_candidates.json'); print('Review sources before using any claim.')"
if errorlevel 1 goto :fail
echo.
echo Done. This task only reads RSS feeds and writes a local review queue.
echo It does NOT render videos or upload to YouTube.
exit /b 0
:fail
echo.
echo FAILED. Check Python/dependencies and internet connection.
exit /b 1
