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

REM Check ADB
adb version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: ADB not found
    echo.
    echo Please install Android SDK Platform Tools:
    echo https://developer.android.com/studio/releases/platform-tools
    echo.
    echo Or add ADB to PATH environment variable
    pause
    exit /b 1
)

echo [OK] ADB found
echo.

echo ============================================================
echo Starting USB Display Control Service...
echo ============================================================
echo.

REM Run Python script with unbuffered output
python -u usb_display_control.py

pause
