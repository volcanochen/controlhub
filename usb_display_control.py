#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
USB Display Control Server
Controls Windows display via ADB reverse channel
"""

import subprocess
import sys
import time
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

# Configuration
PORT = 8765

def find_adb_path():
    """Find ADB executable path"""
    import os
    import shutil
    
    # Try PATH first
    adb_path = shutil.which("adb")
    if adb_path:
        print(f"[OK] Found ADB in PATH: {adb_path}")
        return "adb"
    
    # Common installation paths
    common_paths = [
        r"C:\Program Files (x86)\Android\android-sdk\platform-tools\adb.exe",
        r"C:\Program Files\Android\Android Studio\platform-tools\adb.exe",
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
        path = os.path.expandvars(os.path.expanduser(path))
        if os.path.exists(path):
            print(f"[OK] Found ADB: {path}")
            return path
    
    return None

def switch_display(mode):
    """Execute Windows display switch and wait for it to complete"""
    try:
        cmd_map = {
            'internal': '/internal',
            'external': '/external',
            'extend': '/extend',
            'clone': '/clone'
        }
        
        if mode not in cmd_map:
            return False, f"Invalid mode: {mode}"
        
        cmd = f"DisplaySwitch.exe {cmd_map[mode]}"
        print(f"Executing: {cmd}")
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            msg = f"[OK] Display switched to: {mode}"
            print(msg)
            
            # Wait for display switch to complete
            # Windows needs time to reconfigure displays
            print("Waiting for display switch to complete...")
            import time
            time.sleep(5)  # Wait 5 seconds for the switch to take effect
            
            return True, msg
        else:
            msg = f"[ERROR] Switch failed"
            print(msg)
            return False, msg
            
    except Exception as e:
        msg = f"[ERROR] Execution failed: {e}"
        print(msg)
        return False, msg

def get_current_display_mode():
    """Get current display mode using PowerShell for accurate detection
    Returns:
        int: 0 = unknown, 1 = primary only, 2 = secondary only, 3 = extended, 4 = duplicate
    """
    try:
        import subprocess
        
        # Use PowerShell with DisplayConfig API via .NET
        ps_cmd = r"""
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms

# Get all screens
$screens = [System.Windows.Forms.Screen]::AllScreens

# Count active screens
$count = $screens.Count
Write-Host "ACTIVE_COUNT:$count"

# Get primary screen info
$primary = $screens | Where-Object { $_.Primary }
if ($primary) {
    Write-Host "PRIMARY_EXISTS:True"
} else {
    Write-Host "PRIMARY_EXISTS:False"
}

# Get working area of first screen
if ($count -gt 0) {
    $first = $screens[0]
    Write-Host "FIRST_BOUNDS:$($first.Bounds.X),$($first.Bounds.Y)"
    Write-Host "FIRST_WORKING:$($first.WorkingArea.Width)x$($first.WorkingArea.Height)"
}
"""
        
        result = subprocess.run(
            ['powershell', '-Command', ps_cmd],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            output = result.stdout
            print(f"PowerShell output:\n{output}")
            
            # Parse active count
            import re
            count_match = re.search(r'ACTIVE_COUNT:(\d+)', output)
            if count_match:
                count = int(count_match.group(1))
                print(f"Active displays: {count}")
                
                if count == 0:
                    return 0  # Unknown
                elif count == 1:
                    # Single display - check if it's the primary
                    primary_match = re.search(r'PRIMARY_EXISTS:(True|False)', output)
                    if primary_match and primary_match.group(1) == 'True':
                        print("-> Primary only")
                        return 1  # MODE_PRIMARY_ONLY
                    else:
                        print("-> Secondary only")
                        return 2  # MODE_SECONDARY_ONLY
                else:
                    # Multiple displays
                    print("-> Extended mode")
                    return 3  # MODE_EXTENDED
        
        # Fallback
        print("PowerShell detection failed")
        return 3
        
    except Exception as e:
        print(f"Error getting display mode: {e}")
        import traceback
        traceback.print_exc()
        return 3  # Default to extended

class DisplayHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            command = data.get('command', '')
            
            print(f"Received: {command}")
            success, message = switch_display(command)
            
            response = {'success': success, 'message': message}
            self.send_response(200 if success else 500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            print(f"Error: {e}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': False, 'message': str(e)}).encode('utf-8'))
    
    def do_GET(self):
        """Handle GET request - return display status (real-time detection)"""
        print("=" * 50)
        print(f"GET /status requested!")
        print("=" * 50)
        try:
            if self.path == '/status' or self.path.startswith('/status'):
                # Real-time detection - always get current state
                mode_int = get_current_display_mode()
                
                # Map integer mode to name for logging
                mode_names = {1: 'internal', 2: 'external', 3: 'extend', 4: 'clone'}
                mode_name = mode_names.get(mode_int, 'unknown')
                
                print(f"Real-time detection: mode={mode_int} ({mode_name})")
                
                response = {
                    'status': 'ok',
                    'mode': mode_int,
                    'mode_name': mode_name,
                    'server': 'running',
                    'realtime': True
                }
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
            else:
                # Health check
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'running'}).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'error', 'message': str(e)}).encode('utf-8'))
    
    def log_message(self, format, *args):
        pass

def setup_adb_reverse():
    """Setup ADB reverse port forwarding"""
    print("Setting up ADB reverse...")
    
    try:
        adb_cmd = find_adb_path()
        
        if not adb_cmd:
            print("[ERROR] ADB not found")
            print("Please install Android SDK Platform Tools")
            return False
        
        # Check ADB
        result = subprocess.run([adb_cmd, "version"], capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            print("[ERROR] ADB execution failed")
            return False
        
        print("[OK] ADB ready")
        
        # Wait for device
        print("Waiting for device...")
        result = subprocess.run([adb_cmd, "wait-for-device"], timeout=30, capture_output=True, text=True)
        if result.returncode != 0:
            print("[ERROR] No device detected")
            return False
        
        print("[OK] Device connected")
        
        # Setup reverse
        print(f"Setting up reverse: tcp:{PORT} -> tcp:{PORT}")
        result = subprocess.run([adb_cmd, "reverse", f"tcp:{PORT}", f"tcp:{PORT}"], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("[OK] Reverse setup successful")
            return True
        else:
            print(f"[ERROR] Reverse failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Setup failed: {e}")
        return False

def main():
    print("=" * 60)
    print("USB Display Control Server")
    print("=" * 60)
    print()
    
    if not setup_adb_reverse():
        print()
        print("[ERROR] Failed to setup ADB reverse")
        print("Please check:")
        print("1. USB cable is connected")
        print("2. USB debugging is enabled")
        input("Press Enter to exit...")
        return
    
    print()
    print("=" * 60)
    print("Starting server...")
    print("=" * 60)
    print()
    
    try:
        server = HTTPServer(('localhost', PORT), DisplayHandler)
        print(f"[OK] Server started on port {PORT}")
        print("Listening for requests...")
        print()
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[STOP] Stopping...")
        try:
            subprocess.run(["adb", "reverse", "--remove-all"], capture_output=True, timeout=5)
        except:
            pass
        print("Bye!")
    except Exception as e:
        print(f"\n[ERROR] Server crashed: {e}")
        input("Press Enter to exit...")

if __name__ == '__main__':
    main()
