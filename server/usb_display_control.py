#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Display Control Server (USB + WiFi)
Controls Windows display via ADB reverse or WiFi network
"""

import subprocess
import sys
import time
import socket
import os
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


def set_brightness(brightness):
    """Set monitor brightness using PowerShell script
    
    Args:
        brightness: int 0-100
    
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        brightness = int(brightness)
        if brightness < 0 or brightness > 100:
            return False, f"Invalid brightness value: {brightness} (must be 0-100)"
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        ps_script = os.path.join(script_dir, 'brightness_control.ps1')
        
        if not os.path.exists(ps_script):
            print(f"Warning: {ps_script} not found")
            return False, "Brightness control script not found"
        
        cmd = [
            'powershell',
            '-ExecutionPolicy', 'Bypass',
            '-File', ps_script,
            '-Brightness', str(brightness)
        ]
        
        print(f"Setting brightness to {brightness}%")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        print(f"Brightness script stdout: {stdout}")
        if stderr:
            print(f"Brightness script stderr: {stderr}")
        
        if 'OK:' in stdout:
            msg = f"[OK] Brightness set to {brightness}%"
            print(msg)
            return True, msg
        else:
            error_msg = stdout if stdout else stderr
            msg = f"[ERROR] Brightness control failed (exit={result.returncode}): {error_msg}"
            print(msg)
            return False, msg
            
    except subprocess.TimeoutExpired:
        msg = "[ERROR] Brightness control timed out"
        print(msg)
        return False, msg
    except Exception as e:
        msg = f"[ERROR] Brightness control failed: {e}"
        print(msg)
        return False, msg

def get_current_display_mode():
    """Get current display mode using external PowerShell script
    Returns:
        int: 0 = unknown, 1 = primary only, 2 = secondary only, 3 = extended, 4 = duplicate
    """
    try:
        import subprocess
        import os
        import re
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        ps_script = os.path.join(script_dir, 'get_displays.ps1')
        
        if not os.path.exists(ps_script):
            print(f"Warning: {ps_script} not found, using fallback")
            return 3
        
        result = subprocess.run(
            ['powershell', '-ExecutionPolicy', 'Bypass', '-File', ps_script],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            output = result.stdout
            print(f"PowerShell output:\n{output}")
            
            count_match = re.search(r'ACTIVE_COUNT:(\d+)', output)
            if count_match:
                count = int(count_match.group(1))
                print(f"Active displays: {count}")
                
                if count == 0:
                    return 0
                elif count == 1:
                    id_matches = re.findall(r'DISPLAY_ID:(\d+)', output)
                    if id_matches:
                        display_id = int(id_matches[0])
                        print(f"Single display ID: {display_id}")
                        if display_id == 1:
                            print("-> Primary only (mode=1) - DISPLAY1")
                            return 1
                        else:
                            print(f"-> Secondary only (mode=2) - DISPLAY{display_id}")
                            return 2
                    else:
                        all_ids_match = re.search(r'ALL_IDS:(.+)', output)
                        if all_ids_match:
                            ids = [int(x.strip()) for x in all_ids_match.group(1).split(',')]
                            if ids and len(ids) == 1:
                                return 1 if ids[0] == 1 else 2
                        print("-> Primary only (mode=1) [default]")
                        return 1
                else:
                    print("-> Extended mode (mode=3)")
                    return 3
        
        print("PowerShell detection failed, default to extended")
        return 3
        
    except Exception as e:
        print(f"Error getting display mode: {e}")
        import traceback
        traceback.print_exc()
        return 3

class DisplayHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # Check if this is an upload test
            if self.path == '/upload':
                start = time.time()
                response = {
                    'received': len(post_data),
                    'elapsed': time.time() - start,
                    'speed_mbps': (len(post_data) / (time.time() - start) * 8 / 1024 / 1024) if (time.time() - start) > 0 else 0
                }
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # Brightness control
            if self.path == '/brightness':
                data = json.loads(post_data.decode('utf-8'))
                brightness = data.get('brightness', -1)
                
                print(f"Received brightness: {brightness}")
                success, message = set_brightness(brightness)
                
                response = {'success': success, 'message': message}
                self.send_response(200 if success else 500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # Normal display switch command
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
        """Handle GET request - support speed test and display status"""
        try:
            # Speed test: Ping
            if self.path == '/ping':
                response = {'status': 'pong', 'time': time.time()}
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # Speed test: Download (send 10MB data)
            if self.path == '/download':
                data_size = 10 * 1024 * 1024  # 10MB
                data = b'x' * data_size
                self.send_response(200)
                self.send_header('Content-Type', 'application/octet-stream')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            
            # Display status
            if self.path == '/status' or self.path.startswith('/status'):
                print("=" * 50)
                print(f"GET /status requested!")
                print("=" * 50)
                
                mode_int = get_current_display_mode()
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
                return
            
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
    print("Display Control Server (USB + WiFi)")
    print("=" * 60)
    print()
    
    # Try to setup ADB reverse (optional, for USB connection)
    try:
        if setup_adb_reverse():
            print("[OK] USB connection ready")
        else:
            print("[INFO] USB connection not available, but WiFi may still work")
    except Exception as e:
        print(f"[INFO] USB setup skipped: {e}")
    
    print()
    print("=" * 60)
    print("Starting server...")
    print("=" * 60)
    print()
    
    try:
        # Listen on all network interfaces to support WiFi connection
        server = HTTPServer(('0.0.0.0', PORT), DisplayHandler)
        print(f"[OK] Server started on port {PORT}")
        print(f"[INFO] Listening on all network interfaces")
        
        # Display local IP address for WiFi connection
        hostname = socket.gethostname()
        try:
            local_ip = socket.gethostbyname(hostname)
            print(f"[INFO] Local IP address: {local_ip}")
            print(f"[INFO] Connect via WiFi using: http://{local_ip}:{PORT}")
        except Exception:
            print(f"[INFO] Could not determine local IP address")
        
        print()
        print("Listening for requests...")
        print("(Server is running normally, waiting for phone to connect)")
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
