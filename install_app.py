#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Install and launch Android app
"""

import os
import sys
import subprocess
import shutil

def find_adb_path():
    """Find ADB executable path"""
    # Try PATH first
    adb_path = shutil.which("adb")
    if adb_path:
        print(f"[OK] Found ADB in PATH: {adb_path}")
        return "adb"
    
    # Common installation paths
    common_paths = [
        r"C:\Program Files (x86)\Android\android-sdk\platform-tools\adb.exe",
        r"C:\Program Files\Android\Android Studio\platform-tools\adb.exe",
        r"C:\Android\sdk\platform-tools\adb.exe",
        r"C:\Users\%USERNAME%\AppData\Local\Android\Sdk\platform-tools\adb.exe",
    ]
    
    # Check environment variables
    android_home = os.environ.get('ANDROID_HOME')
    if android_home:
        common_paths.insert(0, os.path.join(android_home, 'platform-tools', 'adb.exe'))
    
    program_files_x86 = os.environ.get('PROGRAMFILES(X86)')
    if program_files_x86:
        common_paths.append(os.path.join(program_files_x86, 'Android', 'android-sdk', 'platform-tools', 'adb.exe'))
    
    # Search for existing path
    for path in common_paths:
        try:
            path = os.path.expandvars(os.path.expanduser(path))
            if os.path.exists(path):
                print(f"[OK] Found ADB: {path}")
                return path
        except:
            pass
    
    return None

def main():
    print("=" * 60)
    print("  Install and Launch Android App")
    print("=" * 60)
    print()
    
    # Find ADB
    adb = find_adb_path()
    if not adb:
        print("[ERROR] ADB not found!")
        print()
        print("Please install Android SDK Platform Tools:")
        print("  https://developer.android.com/studio/releases/platform-tools")
        print()
        print("Or install Android Studio:")
        print("  https://developer.android.com/studio")
        print()
        return 1
    
    # Check devices
    print()
    print("[1] Checking connected devices...")
    try:
        result = subprocess.run([adb, "devices"], capture_output=True, text=True, timeout=10)
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
    except Exception as e:
        print(f"[ERROR] {e}")
        return 1
    
    # Get APK path
    apk_path = os.path.join(os.path.dirname(__file__), "app", "build", "outputs", "apk", "debug", "app-debug.apk")
    if not os.path.exists(apk_path):
        print(f"[ERROR] APK not found: {apk_path}")
        return 1
    print(f"[OK] APK found: {apk_path}")
    
    # Install APK
    print()
    print("[2] Installing APK...")
    try:
        result = subprocess.run([adb, "install", "-r", apk_path], capture_output=True, text=True, timeout=60)
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        if result.returncode == 0:
            print("[OK] Install successful!")
        else:
            print("[ERROR] Install failed!")
            return 1
    except Exception as e:
        print(f"[ERROR] {e}")
        return 1
    
    # Launch app
    print()
    print("[3] Launching app...")
    try:
        result = subprocess.run([adb, "shell", "am", "start", "-n", "com.volcano.screen/.ui.MainActivity"], 
                               capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("[OK] App launched!")
        else:
            print("[ERROR] Launch failed, trying alternative...")
            # Try generic launch
            result = subprocess.run([adb, "shell", "monkey", "-p", "com.volcano.screen", "-c", "android.intent.category.LAUNCHER", "1"], 
                                   capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print("[OK] App launched!")
            else:
                print("[ERROR] Launch failed!")
                print(result.stdout)
                print(result.stderr)
    except Exception as e:
        print(f"[ERROR] {e}")
    
    print()
    print("=" * 60)
    print("  Done!")
    print("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())
