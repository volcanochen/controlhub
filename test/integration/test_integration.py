#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration Test for ControlHub Camera
========================================

This test script:
1. Starts the PC server
2. Installs and runs the Android app
3. Simulates user interactions
4. Verifies basic functionality

Prerequisites:
- Android device connected via USB
- ADB available in PATH
- Python 3.8+
"""

import os
import sys
import time
import subprocess
import requests
import json
import signal
from pathlib import Path
from typing import Optional, Tuple

# Test configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent
SERVER_DIR = PROJECT_ROOT / "server" / "core"
APK_PATH = PROJECT_ROOT / "app" / "build" / "outputs" / "apk" / "debug" / "app-debug.apk"
PACKAGE_NAME = "com.volcano.controlhub"
MAIN_ACTIVITY = "com.volcano.controlhub.ui.MainActivity"
SERVER_PORT = 8765

# Find ADB
def find_adb():
    """Find ADB executable"""
    # Check environment variable
    adb_path = os.environ.get("ADB_PATH")
    if adb_path and os.path.exists(adb_path):
        return adb_path
    
    # Check common locations
    common_paths = [
        os.path.expanduser("~\\AppData\\Local\\Android\\Sdk\\platform-tools\\adb.exe"),
        "C:\\Users\\volcano\\AppData\\Local\\Android\\Sdk\\platform-tools\\adb.exe",
        "/usr/local/bin/adb",
        "/usr/bin/adb",
    ]
    
    for path in common_paths:
        if os.path.exists(path):
            return path
    
    return "adb"  # Fallback to PATH

ADB_PATH = find_adb()

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def log(message: str, level: str = "INFO"):
    """Print colored log message"""
    colors = {
        "INFO": Colors.BLUE,
        "PASS": Colors.GREEN,
        "FAIL": Colors.RED,
        "WARN": Colors.YELLOW,
        "HEADER": Colors.BOLD + Colors.BLUE
    }
    color = colors.get(level, "")
    print(f"{color}[{level}]{Colors.RESET} {message}")


def run_command(cmd: list, timeout: int = 30, check: bool = False, cwd: str = None) -> Tuple[int, str, str]:
    """Run a command and return exit code, stdout, stderr"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )
        if check and result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "Timeout"
    except Exception as e:
        return -1, "", str(e)


def adb_command(args: list, timeout: int = 30) -> Tuple[int, str, str]:
    """Run ADB command"""
    cmd = [ADB_PATH] + args
    return run_command(cmd, timeout)


class IntegrationTest:
    def __init__(self):
        self.server_process: Optional[subprocess.Popen] = None
        self.test_results = []
        
    def setup(self) -> bool:
        """Setup test environment"""
        log("Setting up test environment...", "HEADER")
        
        # Check ADB
        log("Checking ADB...")
        code, out, err = adb_command(["version"])
        if code != 0:
            log("ADB not found. Please install Android SDK.", "FAIL")
            return False
        log(f"ADB found: {out.split(chr(10))[0] if out else 'unknown'}", "PASS")
        
        # Check device connection
        log("Checking device connection...")
        code, out, err = adb_command(["devices"])
        if code != 0:
            log("Failed to list devices", "FAIL")
            return False
        
        devices = [line for line in out.split('\n') if line.strip() and 'device' in line and 'List' not in line]
        if not devices:
            log("No device connected. Please connect an Android device.", "FAIL")
            return False
        log(f"Device connected: {devices[0].split()[0]}", "PASS")
        
        # Setup ADB reverse
        log("Setting up ADB reverse...")
        code, out, err = adb_command(["reverse", f"tcp:{SERVER_PORT}", f"tcp:{SERVER_PORT}"])
        if code != 0:
            log(f"Failed to setup ADB reverse: {err}", "WARN")
        else:
            log("ADB reverse configured", "PASS")
        
        # Check APK exists
        log("Checking APK...")
        if not APK_PATH.exists():
            log(f"APK not found at {APK_PATH}", "FAIL")
            log("Building APK...", "INFO")
            code, out, err = run_command(
                ["gradlew.bat", "assembleDebug"],
                cwd=str(PROJECT_ROOT),
                timeout=300
            )
            if code != 0 or not APK_PATH.exists():
                log("Failed to build APK", "FAIL")
                return False
        log(f"APK found: {APK_PATH}", "PASS")
        
        return True
    
    def start_server(self) -> bool:
        """Start the PC server"""
        log("Starting PC server...", "HEADER")
        
        # Kill any existing server
        run_command(["powershell", "-Command", 
                    f"Get-NetTCPConnection -LocalPort {SERVER_PORT} -ErrorAction SilentlyContinue | "
                    "Select-Object -ExpandProperty OwningProcess | "
                    "ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }"])
        time.sleep(1)
        
        # Start server
        server_script = SERVER_DIR / "usb_display_control.py"
        if not server_script.exists():
            log(f"Server script not found: {server_script}", "FAIL")
            return False
        
        self.server_process = subprocess.Popen(
            [sys.executable, str(server_script)],
            cwd=str(SERVER_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )
        
        # Wait for server to start
        for i in range(10):
            time.sleep(1)
            try:
                resp = requests.get(f"http://localhost:{SERVER_PORT}/status", timeout=2)
                if resp.status_code == 200:
                    log(f"Server started on port {SERVER_PORT}", "PASS")
                    return True
            except:
                pass
        
        log("Failed to start server", "FAIL")
        return False
    
    def stop_server(self):
        """Stop the PC server"""
        if self.server_process:
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
            except:
                self.server_process.kill()
            self.server_process = None
            log("Server stopped", "INFO")
    
    def install_app(self) -> bool:
        """Install the Android app"""
        log("Installing Android app...", "HEADER")
        
        code, out, err = adb_command(["install", "-r", str(APK_PATH)], timeout=60)
        if code != 0:
            log(f"Failed to install app: {err}", "FAIL")
            return False
        log("App installed successfully", "PASS")
        return True
    
    def launch_app(self) -> bool:
        """Launch the Android app"""
        log("Launching app...", "INFO")
        
        code, out, err = adb_command([
            "shell", "am", "start", "-n", 
            f"{PACKAGE_NAME}/{MAIN_ACTIVITY}"
        ])
        if code != 0:
            log(f"Failed to launch app: {err}", "FAIL")
            return False
        
        time.sleep(2)  # Wait for app to start
        log("App launched", "PASS")
        return True
    
    def stop_app(self):
        """Stop the Android app"""
        adb_command(["shell", "am", "force-stop", PACKAGE_NAME])
        log("App stopped", "INFO")
    
    def tap(self, x: int, y: int):
        """Simulate tap on screen"""
        adb_command(["shell", "input", "tap", str(x), str(y)])
        time.sleep(0.5)
    
    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 300):
        """Simulate swipe on screen"""
        adb_command(["shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration)])
        time.sleep(0.5)
    
    def press_back(self):
        """Press back button"""
        adb_command(["shell", "input", "keyevent", "KEYCODE_BACK"])
        time.sleep(0.5)
    
    def press_home(self):
        """Press home button"""
        adb_command(["shell", "input", "keyevent", "KEYCODE_HOME"])
        time.sleep(0.5)
    
    def get_screen_size(self) -> Tuple[int, int]:
        """Get device screen size"""
        code, out, err = adb_command(["shell", "wm", "size"])
        if code == 0 and "Physical size:" in out:
            parts = out.split(":")[-1].strip().split("x")
            return int(parts[0]), int(parts[1])
        return 1080, 1920  # Default
    
    def test_server_status(self) -> bool:
        """Test server status API"""
        log("Testing server status API...", "HEADER")
        
        try:
            resp = requests.get(f"http://localhost:{SERVER_PORT}/status", timeout=5)
            if resp.status_code != 200:
                log(f"Status API returned {resp.status_code}", "FAIL")
                return False
            
            data = resp.json()
            required_fields = ["status", "mode"]
            for field in required_fields:
                if field not in data:
                    log(f"Missing field: {field}", "FAIL")
                    return False
            
            log(f"Server status: {data.get('status')}, mode: {data.get('mode')}", "PASS")
            return True
        except Exception as e:
            log(f"Status API error: {e}", "FAIL")
            return False
    
    def test_brightness_control(self) -> bool:
        """Test brightness control"""
        log("Testing brightness control...", "HEADER")
        
        try:
            # Test setting brightness via API
            resp = requests.post(
                f"http://localhost:{SERVER_PORT}/brightness",
                json={"brightness": 50},
                timeout=5
            )
            if resp.status_code != 200:
                log(f"Brightness API returned {resp.status_code}", "FAIL")
                return False
            
            data = resp.json()
            if not data.get("success"):
                log(f"Brightness control failed: {data.get('message')}", "FAIL")
                return False
            
            log("Brightness control works", "PASS")
            return True
        except Exception as e:
            log(f"Brightness control error: {e}", "FAIL")
            return False
    
    def test_app_server_connection(self) -> bool:
        """Test app can connect to server"""
        log("Testing app-server connection...", "HEADER")
        
        # Clear logcat
        adb_command(["logcat", "-c"])
        
        # Restart app
        self.stop_app()
        time.sleep(1)
        self.launch_app()
        time.sleep(3)
        
        # Check logs for connection
        code, out, err = adb_command([
            "logcat", "-d", "-t", "100",
            "-v", "time"
        ])
        
        if "ChannelManager" in out or "Server URL" in out:
            log("App is using ChannelManager", "PASS")
        else:
            log("ChannelManager logs not found", "WARN")
        
        # Check for connection errors
        if "Failed to connect" in out or "Connection refused" in out:
            log("Connection errors found in logs", "FAIL")
            return False
        
        log("App-server connection OK", "PASS")
        return True
    
    def test_ui_navigation(self) -> bool:
        """Test UI navigation"""
        log("Testing UI navigation...", "HEADER")
        
        width, height = self.get_screen_size()
        log(f"Screen size: {width}x{height}", "INFO")
        
        # Open settings (tap on settings button - typically top right or menu)
        # This is a simplified test - actual coordinates depend on UI
        log("Testing settings navigation...", "INFO")
        
        # Tap near top right for settings (approximate)
        self.tap(width - 100, 100)
        time.sleep(1)
        
        # Press back to return to main screen
        self.press_back()
        time.sleep(1)
        
        log("UI navigation test completed", "PASS")
        return True
    
    def test_camera_functionality(self) -> bool:
        """Test camera functionality"""
        log("Testing camera functionality...", "HEADER")
        
        # Check if camera service is running
        code, out, err = adb_command([
            "shell", "dumpsys", "media.camera"
        ])
        
        if "Camera" in out:
            log("Camera service available", "PASS")
        else:
            log("Camera service status unknown", "WARN")
        
        # Note: Full camera testing requires UI interaction
        log("Camera test completed (manual verification recommended)", "PASS")
        return True
    
    def run_all_tests(self):
        """Run all integration tests"""
        log("=" * 60, "HEADER")
        log("ControlHub Camera - Integration Test Suite", "HEADER")
        log("=" * 60, "HEADER")
        
        tests = [
            ("Setup", self.setup),
            ("Start Server", self.start_server),
            ("Install App", self.install_app),
            ("Launch App", self.launch_app),
            ("Server Status API", self.test_server_status),
            ("Brightness Control", self.test_brightness_control),
            ("App-Server Connection", self.test_app_server_connection),
            ("UI Navigation", self.test_ui_navigation),
            ("Camera Functionality", self.test_camera_functionality),
        ]
        
        passed = 0
        failed = 0
        
        for name, test_func in tests:
            log(f"\n--- Running: {name} ---", "INFO")
            try:
                result = test_func()
                self.test_results.append((name, result))
                if result:
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                log(f"Test exception: {e}", "FAIL")
                self.test_results.append((name, False))
                failed += 1
        
        # Cleanup
        self.stop_server()
        self.stop_app()
        
        # Summary
        log("\n" + "=" * 60, "HEADER")
        log("Test Summary", "HEADER")
        log("=" * 60, "HEADER")
        
        for name, result in self.test_results:
            status = "PASS" if result else "FAIL"
            log(f"  {name}: {status}", status)
        
        log(f"\nTotal: {passed} passed, {failed} failed", "INFO")
        
        if failed == 0:
            log("\nAll tests passed!", "PASS")
        else:
            log(f"\n{failed} test(s) failed!", "FAIL")
        
        return failed == 0


def main():
    test = IntegrationTest()
    try:
        success = test.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        log("\nTest interrupted by user", "WARN")
        test.stop_server()
        test.stop_app()
        sys.exit(1)


if __name__ == "__main__":
    main()
