@echo off
cd /d %~dp0
where python >nul 2>nul
if errorlevel 1 (
    echo Python was not found in PATH.
    echo Please install Python or add it to PATH, then try again.
    pause
    exit /b 1
)

python desktop_qt.py
if errorlevel 1 (
    echo.
    echo Desktop app exited with an error.
    echo Review the message above, then fix the issue and run again.
    pause
    exit /b %errorlevel%
)
