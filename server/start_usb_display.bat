@echo off
echo ============================================================
echo USB Display Control Server
echo ============================================================
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python 3 not found
    echo.
    echo Please install Python 3: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo [OK] Python found
echo.

REM Note: ADB will be auto-detected by the Python script
REM If ADB is not in PATH, common installation paths will be checked
echo Checking ADB (will be auto-detected)...
echo.

echo ============================================================
echo Starting USB Display Control Service...
echo ============================================================
echo.

REM Run Python script with unbuffered output
cd /d "%~dp0"
python -u "%~dp0usb_display_control.py"

pause
