@echo off
setlocal
cd /d "%~dp0"
:MENU
cls
echo ==========================================
echo   AI YouTube Production Pipeline V2.1
echo   Research leads + script drafts
echo   No render / upload / publish
echo ==========================================
echo 1. Discover topics from RSS feeds (internet required)
echo 2. Create script draft for an existing job
echo 3. List production jobs
echo 4. Exit
echo.
set "CHOICE="
set /p "CHOICE=Choose 1-4: "
if "%CHOICE%"=="1" goto RESEARCH
if "%CHOICE%"=="2" goto DRAFT
if "%CHOICE%"=="3" goto LIST
if "%CHOICE%"=="4" goto END
echo Invalid choice.
pause
goto MENU

:RESEARCH
set "LIMIT=10"
set /p "LIMIT=Maximum topic leads to fetch [10]: "
if not defined LIMIT set "LIMIT=10"
python src\ai_research_integration.py research --limit %LIMIT%
pause
goto MENU

:DRAFT
set "JOB_ID="
set /p "JOB_ID=Existing Job ID: "
if not defined JOB_ID (
  echo Job ID is required.
  pause
  goto MENU
)
set "TOPIC="
set /p "TOPIC=Topic [leave blank to use job topic]: "
set "TITLE="
set /p "TITLE=Video title [leave blank to keep job title]: "
set "DESCRIPTION="
set /p "DESCRIPTION=Video description [leave blank to keep current]: "
echo.
echo Provider:
echo 1. Local template (free, offline)
echo 2. Configured AI API (may cost money)
set "PROVIDER_CHOICE="
set /p "PROVIDER_CHOICE=Choose 1-2 [1]: "
set "PROVIDER=local"
if "%PROVIDER_CHOICE%"=="2" set "PROVIDER=ai"
set "STYLE=curiosity"
set /p "STYLE=Style curiosity/story [curiosity]: "
if not defined STYLE set "STYLE=curiosity"
python src\ai_research_integration.py draft "%JOB_ID%" --provider "%PROVIDER%" --style "%STYLE%" --topic "%TOPIC%" --title "%TITLE%" --description "%DESCRIPTION%"
pause
goto MENU

:LIST
python src\production_pipeline.py list
pause
goto MENU

:END
endlocal
exit /b 0
