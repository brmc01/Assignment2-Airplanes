@echo off
REM ============================================================
REM  Where are the Airplanes? - one-click launcher
REM  Double-click this file to run the whole assignment.
REM  (It sets up the environment automatically the first time.)
REM ============================================================
cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo [setup] Creating virtual environment ^(first run only^)...
    python -m venv venv
    echo [setup] Installing libraries ^(first run only, ~1 min^)...
    venv\Scripts\python.exe -m pip install --upgrade pip
    venv\Scripts\python.exe -m pip install -r requirements.txt
)

echo.
echo [run] Starting the airplane finder...
echo.
venv\Scripts\python.exe main.py

echo.
echo Finished. Close the results window to exit.
pause
