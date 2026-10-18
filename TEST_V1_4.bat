@echo off
setlocal
cd /d "%~dp0"
if not exist logs mkdir logs
set LOG=logs\v1_4_test.log
echo AI YouTube Automation V1.4 test - %DATE% %TIME% > "%LOG%"
if not exist venv\Scripts\python.exe (
  echo FAIL: venv missing. Run INSTALL_V1.bat first.
  echo FAIL: venv missing >> "%LOG%"
  type "%LOG%"
  pause
  exit /b 1
)
echo [1] Python version
venv\Scripts\python.exe --version >> "%LOG%" 2>&1
if errorlevel 1 goto failed
echo [2] Compile project
venv\Scripts\python.exe -m compileall -q app.py daily_runner.py src >> "%LOG%" 2>&1
if errorlevel 1 goto failed
echo [3] Imports and topic bank
venv\Scripts\python.exe -c "from src.run_guard import single_instance_lock; from src.topic_generator import TOPICS; assert len(TOPICS)>=30 and len(TOPICS)==len(set(TOPICS)); print('Imports OK; topics:',len(TOPICS))" >> "%LOG%" 2>&1
if errorlevel 1 goto failed
echo [4] Slot planning logic (no network or upload)
venv\Scripts\python.exe -c "from datetime import datetime; from zoneinfo import ZoneInfo; from daily_runner import next_distinct_slots; z=ZoneInfo('Asia/Ho_Chi_Minh'); s=next_distinct_slots(3,datetime(2026,10,18,6,0,tzinfo=z)); assert [x.strftime('%%H:%%M') for x in s]==['07:00','11:00','18:00']; assert all(x>datetime(2026,10,18,6,0,tzinfo=z) for x in s); print('Slot logic OK')" >> "%LOG%" 2>&1
if errorlevel 1 goto failed
echo [5] FFmpeg and FFprobe
where ffmpeg >> "%LOG%" 2>&1
where ffprobe >> "%LOG%" 2>&1
echo PASS: static checks completed. No upload was performed.
echo PASS >> "%LOG%"
type "%LOG%"
pause
exit /b 0
:failed
echo FAIL: inspect %LOG%
echo FAIL >> "%LOG%"
type "%LOG%"
pause
exit /b 1
