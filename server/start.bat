@echo off
chcp 65001 >nul
title ControlHub Server

echo ============================================
echo   ControlHub Server - System Tray Service
echo ============================================
echo.

cd /d "%~dp0"

python tray\tray_service.py

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to start. Please check Python environment.
    pause
)
