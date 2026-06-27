@echo off
REM Double-click to run. main.py builds the environment itself on the first run.
cd /d "%~dp0"
python main.py
echo.
echo Finished. Close the results window to exit.
pause
