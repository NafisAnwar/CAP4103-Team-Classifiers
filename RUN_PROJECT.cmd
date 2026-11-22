@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    py -3.13 -m venv ".venv"
    if errorlevel 1 goto failed
)
".venv\Scripts\python.exe" -B main.py setup
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -B main.py %*
if errorlevel 1 goto failed
exit /b 0
:failed
echo Project execution failed. Check the messages above and confirm Python 3.13 is installed.
pause
exit /b 1
