@echo off
setlocal
cd /d "%~dp0"
if exist "venv\Scripts\python.exe" (set "PYTHON=venv\Scripts\python.exe") else (set "PYTHON=python")
echo AI YouTube Automation V1.6 offline tests
"%PYTHON%" -m compileall -q src
if errorlevel 1 goto :fail
"%PYTHON%" -c "from src.topic_research import _parse_feed; x=_parse_feed(b'<rss><channel><item><title>Test science topic</title><link>https://example.org/story</link><description>Demo</description></item></channel></rss>', 'https://example.org/feed.xml'); assert len(x)==1 and x[0]['topic']=='Test science topic'; print('RSS parser PASS')"
if errorlevel 1 goto :fail
"%PYTHON%" -c "from src.topic_research import _parse_feed; x=_parse_feed(b'<rss><channel><item><title>Bad link</title><link>javascript:alert(1)</link></item></channel></rss>', 'https://example.org/feed.xml'); assert x==[]; print('Unsafe-link rejection PASS')"
if errorlevel 1 goto :fail
echo PASS - offline tests only; no internet, rendering, or upload performed.
exit /b 0
:fail
echo FAIL
exit /b 1
