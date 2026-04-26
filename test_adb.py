#!/usr/bin/env python3
print("Script starting...")

import subprocess
print("Imported subprocess")

adb_path = r"C:\Program Files (x86)\Android\android-sdk\platform-tools\adb.exe"
print(f"ADB path: {adb_path}")

print("Checking ADB version...")
result = subprocess.run([adb_path, "version"], capture_output=True, text=True, timeout=5)
print(f"ADB version check returned: {result.returncode}")
print(f"Output: {result.stdout[:100] if result.stdout else 'None'}")

print("Waiting for device...")
result = subprocess.run([adb_path, "wait-for-device"], timeout=30, capture_output=True, text=True)
print(f"Wait result: {result.returncode}")

print("Setting up reverse...")
result = subprocess.run([adb_path, "reverse", "tcp:8765", "tcp:8765"], capture_output=True, text=True, timeout=10)
print(f"Reverse result: {result.returncode}")
if result.stderr:
    print(f"Error: {result.stderr}")

print("Done!")
