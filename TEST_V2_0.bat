@echo off
setlocal
cd /d "%~dp0"
title Test AI YouTube Production Pipeline V2.0
echo [1/3] Syntax check...
python -m py_compile src\production_pipeline.py src\content_quality.py src\retention_review.py
if errorlevel 1 goto failed
echo [2/3] CLI help check...
python src\production_pipeline.py --help
if errorlevel 1 goto failed
echo [3/3] Unit smoke tests...
python -c "import tempfile; from pathlib import Path; from src.production_pipeline import create_job, load_job, safe_job_path; d=Path(tempfile.mkdtemp()); j=create_job('Test topic', target_seconds=45, jobs_dir=d); assert load_job(j['job_id'], d)['stage']=='topic_selected'; assert safe_job_path(j['job_id'], d).is_file(); ok=False; exec(\"try:\\n safe_job_path('../bad', d)\\nexcept ValueError:\\n ok=True\"); assert ok; print('V2.0 smoke tests PASSED')"
if errorlevel 1 goto failed
echo.
echo PASS - offline tests completed. No network, rendering, or upload was performed.
pause
exit /b 0
:failed
echo.
echo FAIL - inspect the error above.
pause
exit /b 1
