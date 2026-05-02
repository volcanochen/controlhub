#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup ADB reverse port forwarding
"""

import os
import sys
import subprocess
import shutil

def find_adb_path():
    """Find ADB executable path"""
    adb_path = shutil.which("adb")
    if adb_path:
        print(f"[OK] Found ADB in PATH: {adb_path}")
        return "adb"
    
    common_paths = [
        r"C:\Program Files (x86)\Android\android-sdk\platform-tools\adb.exe",
        r"C:\Program Files\Android\Android Studio\platform-tools\adb.exe",
    ]
    
    android_home = os.environ.get('ANDROID_HOME')
    if android_home:
        common_paths.insert(0, os.path.join(android_home, 'platform-tools', 'adb.exe'))
    
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
    print("  Setup ADB Reverse Port Forwarding")
    print("=" * 60)
    print()
    
    adb = find_adb_path()
    if not adb:
        print("[ERROR] ADB not found!")
        return 1
    
    print("[1] Checking devices...")
    try:
        result = subprocess.run([adb, "devices"], capture_output=True, text=True, timeout=10)
        print(result.stdout)
    except Exception as e:
        print(f"[ERROR] {e}")
        return 1
    
    print()
    print("[2] Setting up ADB reverse...")
    try:
        result = subprocess.run([adb, "reverse", "--remove-all"], capture_output=True, text=True, timeout=10)
        print("  - Cleared existing reverse")
        
        result = subprocess.run([adb, "reverse", "tcp:8765", "tcp:8765"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("  [OK] Reverse port forwarding setup: tcp:8765 -> tcp:8765")
        else:
            print(f"  [ERROR] Failed: {result.stderr}")
            return 1
    except Exception as e:
        print(f"  [ERROR] {e}")
        return 1
    
    print()
    print("[3] Verifying reverse...")
    try:
        result = subprocess.run([adb, "reverse", "--list"], capture_output=True, text=True, timeout=10)
        if "8765" in result.stdout:
            print("  [OK] Reverse is active!")
            print("  " + result.stdout.strip())
        else:
            print("  [WARNING] Reverse not listed, but should be working")
            print("  " + result.stdout)
    except Exception as e:
        print(f"  [ERROR] {e}")
    
    print()
    print("=" * 60)
    print("  Done! Now try clicking the image button in the APP!")
    print("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())
