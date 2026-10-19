@echo off
REM Windows Command Prompt Launcher for Xenon Hotel Management
SETLOCAL

cd /d "%~dp0"

where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    python run.py
    goto :eof
)

where py >nul 2>&1
if %ERRORLEVEL% equ 0 (
    py -3 run.py
    goto :eof
)

echo [ERROR] Python was not found in PATH. Please install Python 3.10+ from python.org
pause
