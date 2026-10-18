@echo off
setlocal
cd /d "%~dp0"
echo AI YouTube Automation - V1.9 RETENTION TEST
python --version
if errorlevel 1 exit /b 2
python -m py_compile src\retention_review.py
if errorlevel 1 exit /b 1
python -c "from src.retention_review import analyze_retention; assert analyze_retention('')['status']=='BLOCK'; sample='At exactly midnight, the lighthouse went dark. But something was still shining beneath the waves. What would you do if you saw it?'; result=analyze_retention(sample, 20); assert result['word_count'] > 0; assert result['sentence_count'] == 3; assert 'findings' in result; print('PASS: empty script and structure analysis')"
if errorlevel 1 exit /b 1
echo PASS: offline V1.9 tests completed. No uploads performed.
exit /b 0
