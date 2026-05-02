#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Display Control Server (USB + WiFi)
Controls Windows display via ADB reverse or WiFi network
Supports image casting to Android device
"""

import subprocess
import sys
import time
import socket
import os
import base64
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import threading
from queue import Queue, Empty

# Configuration
PORT = 8765

# Image casting state
class ImageCastingState:
    def __init__(self):
        self.current_image = None  # Base64 encoded image
        self.current_image_name = None
        self.scale_level = 1.0
        self.last_update = None
        self.image_data = None  # Raw binary image data
        self.auto_popup = False  # Flag to trigger auto-popup on phone
        self.close_window = False  # Flag to close phone's cast window
        self.lock = threading.Lock()
        
    def set_image(self, image_data, image_name=None):
        with self.lock:
            self.image_data = image_data
            self.current_image = base64.b64encode(image_data).decode('utf-8')
            self.current_image_name = image_name or 'image.jpg'
            self.scale_level = 1.0
            self.last_update = time.time()
            self.auto_popup = True  # Set flag for auto-popup
            self.close_window = False  # Reset close flag
            print(f"[Image] Image set: {self.current_image_name}, size: {len(image_data)} bytes")
            
    def clear_auto_popup(self):
        with self.lock:
            self.auto_popup = False
            
    def request_close_window(self):
        with self.lock:
            self.close_window = True
            self.last_update = time.time()
            
    def clear_close_window(self):
        with self.lock:
            self.close_window = False
            
    def set_scale(self, scale_level):
        with self.lock:
            self.scale_level = max(0.1, min(5.0, scale_level))
            self.last_update = time.time()
            print(f"[Image] Scale updated: {self.scale_level}x")
            
    def get_state(self):
        with self.lock:
            return {
                'has_image': self.current_image is not None,
                'image_name': self.current_image_name,
                'scale_level': self.scale_level,
                'last_update': self.last_update,
                'image_data': self.current_image,
                'image_size': len(self.image_data) if self.image_data else 0,
                'auto_popup': self.auto_popup,
                'close_window': self.close_window
            }

# Global state
image_state = ImageCastingState()



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
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            # Upload image to device
            if self.path == '/image/upload':
                print("[Image] Receiving image upload...")
                
                # Try to get filename from header
                content_disposition = self.headers.get('Content-Disposition', '')
                filename = None
                if 'filename=' in content_disposition:
                    import re
                    filename_match = re.search(r'filename="([^"]+)"', content_disposition)
                    if filename_match:
                        filename = filename_match.group(1)
                
                if not filename:
                    # Try to detect image type from magic bytes
                    if post_data.startswith(b'\xff\xd8\xff'):
                        filename = 'image.jpg'
                    elif post_data.startswith(b'\x89PNG'):
                        filename = 'image.png'
                    else:
                        filename = 'image.jpg'
                
                image_state.set_image(post_data, filename)
                
                response = {
                    'success': True,
                    'message': f'Image received: {filename}',
                    'size': len(post_data),
                    'filename': filename
                }
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # Update scale level (from either side)
            if self.path == '/image/scale':
                print("[Image] Scale update request")
                data = json.loads(post_data.decode('utf-8'))
                scale = data.get('scale', 1.0)
                
                if isinstance(scale, (int, float)):
                    image_state.set_scale(scale)
                    response = {
                        'success': True,
                        'scale': image_state.scale_level
                    }
                else:
                    response = {
                        'success': False,
                        'message': 'Invalid scale parameter'
                    }
                
                self.send_response(200 if response['success'] else 400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # Zoom in
            if self.path == '/image/zoom-in':
                print("[Image] Zoom in request")
                current_scale = image_state.scale_level
                new_scale = current_scale * 1.25
                image_state.set_scale(new_scale)
                response = {
                    'success': True,
                    'scale': image_state.scale_level
                }
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # Zoom out
            if self.path == '/image/zoom-out':
                print("[Image] Zoom out request")
                current_scale = image_state.scale_level
                new_scale = current_scale * 0.8
                image_state.set_scale(new_scale)
                response = {
                    'success': True,
                    'scale': image_state.scale_level
                }
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # Reset scale
            if self.path == '/image/zoom-reset':
                print("[Image] Zoom reset request")
                image_state.set_scale(1.0)
                response = {
                    'success': True,
                    'scale': 1.0
                }
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # Clear current image
            if self.path == '/image/clear':
                print("[Image] Clear image request")
                with image_state.lock:
                    image_state.current_image = None
                    image_state.current_image_name = None
                    image_state.image_data = None
                    image_state.scale_level = 1.0
                    image_state.last_update = time.time()
                    image_state.auto_popup = False
                    image_state.close_window = True
                
                response = {'success': True, 'message': 'Image cleared'}
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # Acknowledge close window (clear the flag)
            if self.path == '/image/ack-close':
                image_state.clear_close_window()
                response = {'success': True, 'message': 'Close acknowledged'}
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # Acknowledge auto-popup (clear the flag)
            if self.path == '/image/ack-popup':
                image_state.clear_auto_popup()
                response = {'success': True, 'message': 'Auto-popup acknowledged'}
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # Cast image by file path (JSON)
            if self.path == '/image/cast':
                data = json.loads(post_data.decode('utf-8'))
                file_path = data.get('file', data.get('path', data.get('image', '')))
                
                if not file_path:
                    response = {'success': False, 'message': 'Missing "file" parameter. Usage: {"file": "C:/path/to/image.jpg"}'}
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(response).encode('utf-8'))
                    return
                
                file_path = os.path.expandvars(os.path.expanduser(file_path))
                
                if not os.path.exists(file_path):
                    response = {'success': False, 'message': f'File not found: {file_path}'}
                    self.send_response(404)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(response).encode('utf-8'))
                    return
                
                if not os.path.isfile(file_path):
                    response = {'success': False, 'message': f'Not a file: {file_path}'}
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(response).encode('utf-8'))
                    return
                
                with open(file_path, 'rb') as f:
                    image_bytes = f.read()
                
                filename = os.path.basename(file_path)
                image_state.set_image(image_bytes, filename)
                
                response = {
                    'success': True,
                    'message': f'Image casted: {filename}',
                    'filename': filename,
                    'size': len(image_bytes),
                    'path': file_path
                }
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
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
            import traceback
            traceback.print_exc()
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': False, 'message': str(e)}).encode('utf-8'))
    
    def do_GET(self):
        """Handle GET request - support speed test, display status, and image casting"""
        try:
            # API documentation
            if self.path == '/api' or self.path == '/':
                api_doc = {
                    'service': 'USB Display Control Server',
                    'version': '2.0',
                    'endpoints': {
                        'image_cast_get': {
                            'method': 'GET',
                            'path': '/image/cast?file=<path>',
                            'description': 'Cast image by file path (easiest way)',
                            'example': '/image/cast?file=C:/Users/photos/test.jpg'
                        },
                        'image_cast_post': {
                            'method': 'POST',
                            'path': '/image/cast',
                            'body': '{"file": "C:/path/to/image.jpg"}',
                            'description': 'Cast image by file path (JSON)',
                            'example': 'curl -X POST localhost:8765/image/cast -d "{\"file\":\"C:/test.jpg\"}"'
                        },
                        'image_upload': {
                            'method': 'POST',
                            'path': '/image/upload',
                            'body': 'raw binary image data',
                            'description': 'Upload image binary directly',
                            'example': 'curl -X POST localhost:8765/image/upload --data-binary @photo.jpg'
                        },
                        'image_status': {
                            'method': 'GET',
                            'path': '/image/status',
                            'description': 'Get current image status (name, scale, size)'
                        },
                        'image_data': {
                            'method': 'GET',
                            'path': '/image/data',
                            'description': 'Get current image raw binary data'
                        },
                        'image_scale': {
                            'method': 'POST',
                            'path': '/image/scale',
                            'body': '{"scale": 1.5}',
                            'description': 'Set scale level (0.1 to 5.0)'
                        },
                        'image_zoom_in': {
                            'method': 'POST',
                            'path': '/image/zoom-in',
                            'description': 'Zoom in (scale * 1.25)'
                        },
                        'image_zoom_out': {
                            'method': 'POST',
                            'path': '/image/zoom-out',
                            'description': 'Zoom out (scale * 0.8)'
                        },
                        'image_zoom_reset': {
                            'method': 'POST',
                            'path': '/image/zoom-reset',
                            'description': 'Reset zoom to 1.0'
                        },
                        'image_clear': {
                            'method': 'POST',
                            'path': '/image/clear',
                            'description': 'Clear current image'
                        },
                        'image_poll': {
                            'method': 'GET',
                            'path': '/image/poll?t=<timestamp>',
                            'description': 'Poll for updates since timestamp'
                        },
                        'image_list': {
                            'method': 'GET',
                            'path': '/image/list?dir=<path>',
                            'description': 'List image files in a directory'
                        },
                        'ping': {
                            'method': 'GET',
                            'path': '/ping',
                            'description': 'Health check'
                        }
                    }
                }
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(api_doc, indent=2, ensure_ascii=False).encode('utf-8'))
                return
            
            # Cast image by file path (GET - easiest way)
            if self.path.startswith('/image/cast'):
                from urllib.parse import urlparse, parse_qs
                parsed = urlparse(self.path)
                params = parse_qs(parsed.query)
                
                file_path = params.get('file', params.get('path', [None]))[0]
                
                if not file_path:
                    response = {'success': False, 'message': 'Missing "file" parameter. Usage: /image/cast?file=C:/path/to/image.jpg'}
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(response).encode('utf-8'))
                    return
                
                file_path = os.path.expandvars(os.path.expanduser(file_path))
                
                if not os.path.exists(file_path):
                    response = {'success': False, 'message': f'File not found: {file_path}'}
                    self.send_response(404)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(response).encode('utf-8'))
                    return
                
                if not os.path.isfile(file_path):
                    response = {'success': False, 'message': f'Not a file: {file_path}'}
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(response).encode('utf-8'))
                    return
                
                with open(file_path, 'rb') as f:
                    image_bytes = f.read()
                
                filename = os.path.basename(file_path)
                image_state.set_image(image_bytes, filename)
                
                response = {
                    'success': True,
                    'message': f'Image casted: {filename}',
                    'filename': filename,
                    'size': len(image_bytes),
                    'path': file_path
                }
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # List image files in a directory
            if self.path.startswith('/image/list'):
                from urllib.parse import urlparse, parse_qs
                parsed = urlparse(self.path)
                params = parse_qs(parsed.query)
                
                dir_path = params.get('dir', ['.'])[0]
                dir_path = os.path.expandvars(os.path.expanduser(dir_path))
                
                if not os.path.isdir(dir_path):
                    response = {'success': False, 'message': f'Directory not found: {dir_path}'}
                    self.send_response(404)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(response).encode('utf-8'))
                    return
                
                image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.ico'}
                files = []
                try:
                    for entry in sorted(os.listdir(dir_path)):
                        full_path = os.path.join(dir_path, entry)
                        if os.path.isfile(full_path):
                            ext = os.path.splitext(entry)[1].lower()
                            if ext in image_extensions:
                                size = os.path.getsize(full_path)
                                files.append({
                                    'name': entry,
                                    'path': full_path,
                                    'size': size,
                                    'size_mb': round(size / 1024 / 1024, 2)
                                })
                except PermissionError:
                    response = {'success': False, 'message': f'Permission denied: {dir_path}'}
                    self.send_response(403)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(response).encode('utf-8'))
                    return
                
                response = {
                    'success': True,
                    'directory': dir_path,
                    'count': len(files),
                    'files': files
                }
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response, indent=2, ensure_ascii=False).encode('utf-8'))
                return
            
            # Image status - returns current image and scale info
            if self.path == '/image/status':
                state = image_state.get_state()
                response = {
                    'success': True,
                    'has_image': state['has_image'],
                    'image_name': state['image_name'],
                    'scale_level': state['scale_level'],
                    'last_update': state['last_update'],
                    'image_size': state['image_size'],
                    'auto_popup': state['auto_popup'],
                    'close_window': state['close_window']
                }
                
                # Only include image data if requested and available
                if state['has_image'] and 'include_data' in self.path:
                    response['image_data'] = state['image_data']
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # Get current image (raw binary)
            if self.path == '/image/data':
                with image_state.lock:
                    if image_state.image_data:
                        self.send_response(200)
                        
                        # Set content type based on image type
                        if image_state.current_image_name and image_state.current_image_name.lower().endswith('.png'):
                            self.send_header('Content-Type', 'image/png')
                        else:
                            self.send_header('Content-Type', 'image/jpeg')
                        
                        self.send_header('Content-Length', str(len(image_state.image_data)))
                        self.send_header('Content-Disposition', f'inline; filename="{image_state.current_image_name}"')
                        self.end_headers()
                        self.wfile.write(image_state.image_data)
                    else:
                        response = {'success': False, 'message': 'No image available'}
                        self.send_response(404)
                        self.send_header('Content-Type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # Poll for updates (long polling)
            if self.path.startswith('/image/poll'):
                with image_state.lock:
                    last_known = '0'
                    if '?' in self.path:
                        query = self.path.split('?', 1)[1]
                        for param in query.split('&'):
                            if '=' in param:
                                key, val = param.split('=', 1)
                                if key == 't':
                                    last_known = val
                                    break
                            else:
                                last_known = param
                    try:
                        last_known_time = float(last_known)
                    except (ValueError, TypeError):
                        last_known_time = 0
                
                # Check if there's an update
                state = image_state.get_state()
                has_update = state['last_update'] and state['last_update'] > last_known_time
                
                response = {
                    'success': True,
                    'has_update': has_update,
                    'state': state
                }
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
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
