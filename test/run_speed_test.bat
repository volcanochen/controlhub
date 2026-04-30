@echo off
REM Network Speed Test - Quick Start Script
REM Tests network speed between PC and Android device

echo ============================================================
echo Network Speed Test
echo ============================================================
echo.
echo This script will:
echo 1. Start the test server on your PC
echo 2. Show the IP address for Android app to connect
echo 3. Wait for connection from Android device
echo.
echo IMPORTANT: Make sure your Android phone is on the SAME WiFi network
echo.
pause

cd /d "%~dp0"
echo.
echo Starting server...
echo.

python simple_speed_test.py

echo.
echo Test completed.
pause
