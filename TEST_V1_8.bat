@echo off
setlocal
cd /d "%~dp0"
echo AI YouTube Automation - V1.8 QUALITY TEST
python --version
if errorlevel 1 exit /b 2
python -m py_compile src\content_quality.py
if errorlevel 1 exit /b 1
python -c "from src.content_quality import check_content; assert check_content('', 'Ocean Facts', 'A description with enough useful context.')['status']=='BLOCK'; s=' '.join(['Ocean']*80)+'.'; assert check_content(s, 'Ocean Facts', 'A description with enough useful context.')['word_count']==80; assert any(f['code']=='TITLE_MISSING' for f in check_content(s, '', 'A description with enough useful context.')['findings']); print('PASS: empty script, word count, missing title')"
if errorlevel 1 exit /b 1
echo PASS: offline tests completed. No uploads performed.
exit /b 0
