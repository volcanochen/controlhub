#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Image Casting Tray Service
Windows system tray application for image casting control
"""

import os
import sys
import json
import time
import threading
import subprocess
import http.client
import requests
import signal
from io import BytesIO
from pathlib import Path

import pystray
from pystray import MenuItem, Menu
from PIL import Image, ImageDraw, ImageFont


SERVER_PORT = 8765
SERVER_URL = f"localhost:{SERVER_PORT}"
SERVER_SCRIPT = Path(__file__).parent.parent / "core" / "usb_display_control.py"
LOG_FILE = Path(__file__).parent.parent / "server.log"

ICON_SIZE = (64, 64)
STATUS_CHECK_INTERVAL = 3

# 导入统一管理模块
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.network_manager import get_network_manager
from core.app_info import get_app_info, get_changelog_text, APP_NAME, APP_VERSION, APP_COPYRIGHT, APP_AUTHOR, APP_REPO


class TrayService:
    
    _exit_requested = False
    
    def __init__(self):
        self.server_process = None
        self.server_running = False
        self.current_image_name = None
        self.current_scale = 1.0
        self.last_error = None
        self._current_brightness = 100
        
        self.scanning = False
        self._preview_window = None
        self._preview_running = False
        self._virtual_camera = None
        self._virtual_camera_running = False
        self._brightness_window = None
        
        # 使用统一网络管理器
        self._net_manager = get_network_manager()
        
        self.icon_green = self._create_icon((0, 180, 0), "G")
        self.icon_red = self._create_icon((200, 50, 50), "X")
        self.icon_yellow = self._create_icon((255, 180, 0), "!")
    
    @property
    def camera_host(self):
        return self._net_manager.host
    
    @property
    def camera_port(self):
        return self._net_manager.port
    
    @property
    def camera_channel(self):
        return self._net_manager.channel
    
    @property
    def _usb_device_connected(self):
        return self._net_manager.is_usb_connected
    
    @property
    def _adb_forward_active(self):
        return self._net_manager.is_adb_forward_active
    
    def _get_effective_camera_url(self):
        return self._net_manager.get_effective_url()
    
    def _create_icon(self, color, text):
        img = Image.new('RGBA', ICON_SIZE, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse([4, 4, 60, 60], fill=color + (255,), outline=(255, 255, 255, 200), width=2)
        try:
            font = ImageFont.truetype("arial.ttf", 28)
        except:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((ICON_SIZE[0] - tw) / 2, (ICON_SIZE[1] - th) / 2), text, fill=(255, 255, 255, 255), font=font)
        return img
    
    def _build_status_text(self):
        status_text = "Running" if self.server_running else "Stopped"
        lines = [f"Server: {status_text}"]
        if self.current_image_name:
            lines.append(f"Image: {self.current_image_name} ({self.current_scale:.1f}x)")
        if self.last_error:
            lines.append(f"Error: {self.last_error}")
        return "\n".join(lines)
    
    def get_menu(self):
        scan_label = "Stop Scanning" if self.scanning else "Scan QR Code"
        
        channel = self.camera_channel.upper()
        channel_info = f"Channel: {channel}"
        if self._usb_device_connected:
            channel_info += " (USB Connected)"
        
        usb_check = "✓ " if channel == "USB" else ""
        wifi_check = "✓ " if channel == "WIFI" else ""
        auto_check = "✓ " if channel == "AUTO" else ""
        
        vc_label = "Stop Virtual Camera" if self._virtual_camera_running else "Start Virtual Camera"
        
        return Menu(
            MenuItem(self._build_status_text(), lambda i: None, enabled=False),
            Menu.SEPARATOR,
            MenuItem('Start Server', self._start_server, visible=lambda _: not self.server_running),
            MenuItem('Stop Server', self._stop_server, visible=lambda _: self.server_running),
            Menu.SEPARATOR,
            MenuItem('Cast Image...', self._cast_image, enabled=lambda _: self.server_running),
            MenuItem('Clear Image', self._clear_image, enabled=lambda _: self.server_running),
            Menu.SEPARATOR,
            MenuItem('Adjust Brightness', self._show_brightness_dialog),
            Menu.SEPARATOR,
            MenuItem('Open Camera', self._open_camera, enabled=lambda _: self.server_running),
            MenuItem('Close Camera', self._close_camera, enabled=lambda _: self.server_running),
            MenuItem(scan_label, self._toggle_scan, enabled=lambda _: self.server_running),
            MenuItem(vc_label, self._toggle_virtual_camera, enabled=lambda _: self.server_running),
            MenuItem(f"Camera: {self.camera_host}:{self.camera_port}", self._set_camera_ip),
            MenuItem(channel_info, lambda i: None, enabled=False),
            Menu.SEPARATOR,
            MenuItem(usb_check + "USB Channel", self._set_usb_channel),
            MenuItem(wifi_check + "WiFi Channel", self._set_wifi_channel),
            MenuItem(auto_check + "Auto Channel", self._set_auto_channel),
            Menu.SEPARATOR,
            MenuItem('Open Status Window', self._open_status_window),
            MenuItem('View Server Log', self._view_log),
            Menu.SEPARATOR,
            MenuItem('关于 Control Hub', self._show_about),
            Menu.SEPARATOR,
            MenuItem('Exit', self._exit),
        )
    
    def get_icon(self):
        if self.server_running and not self.last_error:
            return self.icon_green
        elif self.last_error:
            return self.icon_yellow
        return self.icon_red
    
    def on_click(self, icon, event):
        if event == pystray.MouseEvent.BUTTON_LEFT:
            threading.Thread(target=self._cast_image_quick, daemon=True).start()
        elif event == pystray.MouseEvent.DOUBLE_CLICK_LEFT:
            self._open_status_window(icon)
    
    def _api_get(self, path, timeout=5):
        try:
            conn = http.client.HTTPConnection(SERVER_URL, timeout=timeout)
            conn.request("GET", path)
            resp = conn.getresponse()
            data = resp.read()
            conn.close()
            try:
                return resp.status, json.loads(data.decode())
            except:
                return resp.status, data
        except Exception as e:
            return -1, str(e)
    
    def _api_post(self, path, body=None, headers=None, timeout=10):
        try:
            conn = http.client.HTTPConnection(SERVER_URL, timeout=timeout)
            conn.request("POST", path, body, headers or {})
            resp = conn.getresponse()
            data = resp.read()
            conn.close()
            try:
                return resp.status, json.loads(data.decode())
            except:
                return resp.status, data
        except Exception as e:
            return -1, str(e)
    
    def _check_status(self):
        while True:
            try:
                status_code, result = self._api_get("/image/status")
                if status_code == 200 and isinstance(result, dict):
                    self.server_running = True
                    self.current_image_name = result.get("image_name")
                    self.current_scale = result.get("scale_level", 1.0)
                    self.last_error = None
                else:
                    self.server_running = False
            except Exception:
                self.server_running = False
            
            try:
                self.update_icon()
            except Exception:
                pass
            
            time.sleep(STATUS_CHECK_INTERVAL)
    
    def _start_server(self, icon, item=None):
        if self.server_process and self.server_process.poll() is None:
            return
        
        self.server_running = False
        self.last_error = None
        
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            self.server_process = subprocess.Popen(
                [sys.executable, str(SERVER_SCRIPT)],
                stdout=open(LOG_FILE, 'a'),
                stderr=subprocess.STDOUT,
                cwd=str(SERVER_SCRIPT.parent),
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            time.sleep(2)
            
            if self.server_process.poll() is None:
                self.server_running = True
                
                for attempt in range(3):
                    if self._check_adb_devices():
                        break
                    print(f"[INFO] ADB reconnect attempt {attempt + 1}/3...")
                    self._reconnect_adb()
                    time.sleep(1)
                
                if self._check_adb_devices():
                    self._setup_adb_forward()
                    self.notify("Server Started", f"Port {SERVER_PORT} + Camera ADB Forward (8766)")
                else:
                    self.notify("Server Started", f"Listening on port {SERVER_PORT} (USB not connected)")
            else:
                self.last_error = "Failed to start server"
            
            self._update_menu()
                
        except Exception as e:
            self.last_error = str(e)
            self.notify("Error", f"Failed to start server: {e}")
    
    def _stop_server(self, icon, item=None):
        if self.server_process and self.server_process.poll() is None:
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
            except:
                self.server_process.kill()
            self.server_process = None
        
        self._remove_adb_forward()
        self.server_running = False
        self.current_image_name = None
        self.notify("Server Stopped")
    
    def _cast_image(self, icon, item=None):
        import tkinter as tk
        from tkinter import filedialog
        
        root = tk.Tk()
        root.withdraw()
        
        file_path = filedialog.askopenfilename(
            title="Select Image to Cast",
            filetypes=[
                ("All Images", "*.jpg *.jpeg *.png *.bmp *.gif *.webp"),
                ("JPEG", "*.jpg *.jpeg"),
                ("PNG", "*.png"),
                ("All Files", "*.*")
            ],
            initialdir=os.path.expanduser("~") if os.path.exists(os.path.expanduser("~")) else "."
        )
        root.destroy()
        
        if file_path:
            self._do_cast(file_path)
    
    def _cast_image_quick(self):
        self._cast_image(None, None)
    
    def _do_cast(self, file_path):
        filename = os.path.basename(file_path)
        self.notify("Casting...", filename)
        
        def do_cast():
            from urllib.parse import quote
            encoded_path = quote(file_path)
            status, result = self._api_get(f"/image/cast?file={encoded_path}", timeout=30)
            
            if status == 200 and isinstance(result, dict) and result.get('success'):
                size_mb = result.get('size', 0) / 1024 / 1024
                self.notify("Image Casted!", f"{filename}\n{size_mb:.1f} MB")
            else:
                error_msg = result if isinstance(result, str) else str(result.get('message', 'Unknown error'))
                self.last_error = error_msg
                self.notify("Cast Failed", error_msg[:100])
        
        threading.Thread(target=do_cast, daemon=True).start()
    
    def _clear_image(self, icon, item=None):
        def do_clear():
            status, result = self._api_post("/image/clear")
            if status == 200:
                self.notify("Image Cleared")
                self.current_image_name = None
            else:
                self.notify("Error", "Failed to clear image")
        
        threading.Thread(target=do_clear, daemon=True).start()
    
    def _show_brightness_dialog(self, icon=None, item=None):
        script_dir = Path(__file__).parent.parent
        brightness_module = script_dir / "display" / "brightness.py"
        
        if not brightness_module.exists():
            self.notify("Error", "Brightness module not found")
            return
        
        try:
            subprocess.Popen(
                [sys.executable, str(brightness_module)],
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
        except Exception as e:
            self.notify("Error", f"Failed to open brightness dialog: {e}")
    
    def _set_brightness(self, brightness):
        sys.path.insert(0, str(Path(__file__).parent.parent / "display"))
        try:
            from brightness import set_brightness
            success, msg = set_brightness(brightness)
            if success:
                self._current_brightness = brightness
                self.notify("Brightness", f"Set to {brightness}%")
            else:
                self.notify("Error", f"Failed: {msg[:50]}")
        except ImportError as e:
            self.notify("Error", f"Brightness module error: {e}")
    
    def _zoom_in(self, icon, item=None):
        status, result = self._api_post("/image/zoom-in")
        if status == 200 and isinstance(result, dict):
            self.notify(f"Zoom: {result.get('scale', '?')}x")
    
    def _zoom_out(self, icon, item=None):
        status, result = self._api_post("/image/zoom-out")
        if status == 200 and isinstance(result, dict):
            self.notify(f"Zoom: {result.get('scale', '?')}x")
    
    def _reset_zoom(self, icon, item=None):
        self._api_post("/image/zoom-reset")
        self.notify("Zoom Reset", "1.0x")
    
    def _open_camera(self, icon, item=None):
        def do_open():
            camera_url = self._get_effective_camera_url()
            if camera_url is None:
                self.notify("Error", "USB device not connected")
                return
            try:
                resp = requests.post(f"{camera_url}/camera/open", timeout=5)
                if resp.status_code == 200:
                    self.notify("Camera Opened", "Starting preview...")
                    time.sleep(2)
                    self._open_preview_window(camera_url)
                else:
                    self.notify("Error", f"Failed to open camera: {resp.status_code}")
            except Exception as e:
                self.notify("Error", f"Cannot connect to camera: {e}")
        
        threading.Thread(target=do_open, daemon=True).start()
    
    def _close_camera(self, icon, item=None):
        def do_close():
            camera_url = self._get_effective_camera_url()
            self._close_preview_window()
            if camera_url is None:
                self.notify("Error", "USB device not connected")
                return
            try:
                resp = requests.post(f"{camera_url}/camera/close", timeout=5)
                if resp.status_code == 200:
                    self.notify("Camera Closed", "Camera activity closed on device")
                else:
                    self.notify("Error", f"Failed to close camera: {resp.status_code}")
            except Exception as e:
                self.notify("Error", f"Cannot connect to camera: {e}")
        
        threading.Thread(target=do_close, daemon=True).start()
    
    def _open_preview_window(self, camera_url):
        if self._preview_running:
            print("[INFO] Preview already running")
            return
        
        host = "localhost"
        port = self.camera_port
        if "localhost" not in camera_url and "127.0.0.1" not in camera_url:
            from urllib.parse import urlparse
            parsed = urlparse(camera_url)
            host = parsed.hostname or host
            port = parsed.port or port
        
        preview_script = Path(__file__).parent.parent / "camera" / "preview.py"
        
        self._preview_running = True
        self._preview_window = subprocess.Popen(
            [sys.executable, str(preview_script), "--host", host, "--port", str(port)],
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        
        def monitor_preview():
            if self._preview_window:
                self._preview_window.wait()
            self._preview_running = False
            self._preview_window = None
        
        threading.Thread(target=monitor_preview, daemon=True).start()
    
    def _close_preview_window(self):
        self._preview_running = False
        
        if self._preview_window and self._preview_window.poll() is None:
            self._preview_window.terminate()
            try:
                self._preview_window.wait(timeout=2)
            except:
                self._preview_window.kill()
        
        self._preview_window = None
    
    def _toggle_virtual_camera(self, icon, item=None):
        if self._virtual_camera_running:
            self._stop_virtual_camera()
        else:
            threading.Thread(target=self._start_virtual_camera, daemon=True).start()
    
    def _start_virtual_camera(self):
        sys.path.insert(0, str(Path(__file__).parent.parent / "camera"))
        from virtual_camera import VirtualCamera, check_virtual_camera_available
        
        available, message = check_virtual_camera_available()
        if not available:
            self.notify("Virtual Camera Error", message)
            return
        
        camera_url = self._get_effective_camera_url()
        if camera_url is None:
            self.notify("Error", "USB device not connected")
            return
        
        self._virtual_camera = VirtualCamera()
        self._virtual_camera.set_callbacks(
            on_error=lambda e: self.notify("Virtual Camera Error", e),
            on_status=lambda s: self.notify("Virtual Camera", s)
        )
        
        if self._virtual_camera.start(camera_url):
            self._virtual_camera_running = True
            self._update_menu()
        else:
            self.notify("Error", "Failed to start virtual camera")
    
    def _stop_virtual_camera(self):
        if self._virtual_camera:
            self._virtual_camera.stop()
            self._virtual_camera = None
        self._virtual_camera_running = False
        self._update_menu()
        self.notify("Virtual Camera", "Stopped")
    
    def _set_camera_ip(self, icon, item=None):
        import tkinter as tk
        from tkinter import simpledialog
        
        root = tk.Tk()
        root.withdraw()
        
        current = f"{self.camera_host}:{self.camera_port}"
        new_value = simpledialog.askstring(
            "Set Camera IP",
            f"Enter camera IP:port (for WiFi channel)\nCurrent: {current}",
            initialvalue=current
        )
        root.destroy()
        
        if new_value:
            try:
                if ':' in new_value:
                    host, port = new_value.split(':')
                    self._net_manager.set_host(host.strip())
                    self._net_manager.set_port(int(port.strip()))
                else:
                    self._net_manager.set_host(new_value.strip())
                    self._net_manager.set_port(8766)
                
                self.notify("Config Saved", f"Camera: {self.camera_host}:{self.camera_port}")
                self._update_menu()
            except Exception as e:
                self.notify("Error", f"Invalid format: {e}")
    
    def _set_usb_channel(self, icon, item=None):
        self._net_manager.set_channel("usb")
        if self._net_manager.check_usb_devices():
            self.notify("Channel Set", "USB Channel (ADB Forward)")
        else:
            self.notify("Warning", "USB Channel set, but no device connected")
        self._update_menu()
    
    def _set_wifi_channel(self, icon, item=None):
        self._net_manager.set_channel("wifi")
        self.notify("Channel Set", f"WiFi Channel: {self.camera_host}:{self.camera_port}")
        self._update_menu()
    
    def _set_auto_channel(self, icon, item=None):
        self._net_manager.set_channel("auto")
        self.notify("Channel Set", "Auto Channel (USB preferred)")
        self._update_menu()
    
    def _toggle_scan(self, icon, item=None):
        if self.scanning:
            self._stop_scan()
        else:
            threading.Thread(target=self._start_scan, daemon=True).start()
    
    def _start_scan(self):
        if self.scanning:
            return
        
        self.scanning = True
        self._update_menu()
        
        camera_url = self._get_effective_camera_url()
        if camera_url is None:
            self.notify("Error", "USB device not connected")
            self.scanning = False
            self._update_menu()
            return
        
        try:
            resp = requests.post(f"{camera_url}/camera/open", timeout=5)
            if resp.status_code != 200:
                self.notify("Error", "Failed to open camera activity")
                self.scanning = False
                self._update_menu()
                return
            time.sleep(1)
        except Exception as e:
            self.notify("Error", f"Cannot connect to camera: {e}")
            self.scanning = False
            self._update_menu()
            return
        
        try:
            resp = requests.post(f"{camera_url}/barcode/start", timeout=5)
            if resp.status_code != 200:
                self.notify("Error", "Failed to start barcode scanner")
                self.scanning = False
                self._update_menu()
                return
        except Exception as e:
            self.notify("Error", f"Failed to start scanner: {e}")
            self.scanning = False
            self._update_menu()
            return
        
        self.notify("Scanning", "Point camera at QR code...")
        
        for i in range(60):
            if not self.scanning:
                break
            
            try:
                resp = requests.get(f"{camera_url}/barcode/result", timeout=2)
                data = resp.json()
                
                if data.get("status") == "ok" and data.get("value"):
                    value = data["value"]
                    fmt = data.get("format", "Unknown")
                    
                    self._copy_to_clipboard(value)
                    
                    display_value = value if len(value) <= 50 else value[:50] + "..."
                    self.notify("Scan Success", f"{fmt}:\n{display_value}\n\nCopied to clipboard!")
                    
                    requests.post(f"{camera_url}/barcode/stop", timeout=2)
                    self.scanning = False
                    self._update_menu()
                    return
                    
            except:
                pass
            
            time.sleep(0.5)
        
        try:
            requests.post(f"{camera_url}/barcode/stop", timeout=2)
        except:
            pass
        
        if self.scanning:
            self.notify("Scan Timeout", "No QR code detected")
        
        self.scanning = False
        self._update_menu()
    
    def _stop_scan(self):
        self.scanning = False
        camera_url = self._get_effective_camera_url()
        if camera_url:
            try:
                requests.post(f"{camera_url}/barcode/stop", timeout=2)
            except:
                pass
        self._update_menu()
        self.notify("Stopped", "Scanning stopped")
    
    def _copy_to_clipboard(self, text):
        try:
            subprocess.run(['clip'], input=text.encode('utf-8'), check=True, capture_output=True)
        except:
            pass
    
    def _update_menu(self):
        try:
            if hasattr(self, 'icon') and self.icon:
                self.icon.menu = Menu(lambda *args: self.get_menu(*args))
        except:
            pass
    
    def _open_status_window(self, icon=None):
        import tkinter as tk
        from tkinter import ttk, scrolledtext
        
        root = tk.Tk()
        root.withdraw()
        
        window = tk.Toplevel(root)
        window.title("Control Hub Server Status")
        window.geometry("520x480")
        window.protocol("WM_DELETE_WINDOW", lambda: [window.destroy(), root.destroy()])
        
        main_frame = ttk.Frame(window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        info_frame = ttk.LabelFrame(main_frame, text="Server Info", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        status_val = tk.StringVar(value="Checking...")
        image_val = tk.StringVar(value="-")
        scale_val = tk.StringVar(value="-")
        
        row = 0
        ttk.Label(info_frame, text="Status:", font=('Segoe UI', 9, 'bold')).grid(row=row, column=0, sticky='w', pady=2)
        ttk.Label(info_frame, textvariable=status_val).grid(row=row, column=1, sticky='w', padx=(10, 0), pady=2); row += 1
        ttk.Label(info_frame, text="Port:", font=('Segoe UI', 9, 'bold')).grid(row=row, column=0, sticky='w', pady=2)
        ttk.Label(info_frame, text=str(SERVER_PORT)).grid(row=row, column=1, sticky='w', padx=(10, 0), pady=2); row += 1
        ttk.Label(info_frame, text="Current Image:", font=('Segoe UI', 9, 'bold')).grid(row=row, column=0, sticky='w', pady=2)
        ttk.Label(info_frame, textvariable=image_val).grid(row=row, column=1, sticky='w', padx=(10, 0), pady=2); row += 1
        ttk.Label(info_frame, text="Scale Level:", font=('Segoe UI', 9, 'bold')).grid(row=row, column=0, sticky='w', pady=2)
        ttk.Label(info_frame, textvariable=scale_val).grid(row=row, column=1, sticky='w', padx=(10, 0), pady=2); row += 1
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(btn_frame, text="Start", command=lambda: [self._start_server(None), refresh()]).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="Stop", command=lambda: [self._stop_server(None), refresh()]).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="Cast...", command=lambda: [self._cast_image(None), refresh()]).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="Clear", command=lambda: [self._clear_image(None), refresh()]).pack(side='left', padx=2)
        
        log_frame = ttk.LabelFrame(main_frame, text="Activity Log", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        log_text = scrolledtext.ScrolledText(log_frame, height=12, wrap=tk.WORD, font=('Consolas', 9))
        log_text.pack(fill=tk.BOTH, expand=True)
        
        def refresh():
            if self.server_running:
                status_val.set("Running")
            else:
                status_val.set("Stopped")
            
            if self.current_image_name:
                image_val.set(self.current_image_name)
                scale_val.set(f"{self.current_scale:.2f}x")
            else:
                image_val.set("(none)")
                scale_val.set("-")
            
            ts = time.strftime("%H:%M:%S")
            state = "RUNNING" if self.server_running else "STOPPED"
            img_info = f" [{self.current_image_name}]" if self.current_image_name else ""
            log_text.insert(tk.END, f"[{ts}] {state}{img_info}\n")
            log_text.see(tk.END)
        
        refresh()
        
        auto_id = None
        def auto_refresh():
            nonlocal auto_id
            try:
                refresh()
                auto_id = window.after(3000, auto_refresh)
            except:
                pass
        
        auto_refresh()
        
        def on_close():
            if auto_id:
                window.after_cancel(auto_id)
            window.destroy()
        
        window.protocol("WM_DELETE_WINDOW", on_close)
        window.mainloop()
    
    def _view_log(self, icon=None):
        if LOG_FILE.exists():
            os.startfile(str(LOG_FILE))
        else:
            self.notify("No Log File", f"Not found: {LOG_FILE}")
    
    def _show_about(self, icon=None):
        import tkinter as tk
        from tkinter import ttk, scrolledtext
        
        root = tk.Tk()
        root.withdraw()
        
        window = tk.Toplevel(root)
        window.title("关于 Control Hub Server")
        window.geometry("540x580")
        window.protocol("WM_DELETE_WINDOW", lambda: [window.destroy(), root.destroy()])
        
        main_frame = ttk.Frame(window, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        title_label = ttk.Label(
            header_frame, 
            text="Control Hub Server", 
            font=('Segoe UI', 16, 'bold')
        )
        title_label.pack()
        
        version_label = ttk.Label(
            header_frame, 
            text=f"v{APP_VERSION}", 
            font=('Segoe UI', 10),
            foreground='#666666'
        )
        version_label.pack(pady=(5, 0))
        
        ttk.Separator(main_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        # Info section
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        info_text = (
            f"开发者：{APP_AUTHOR}\n"
            "🤖 AI 开发：本应用由 AI 助手辅助开发\n"
            f"开源地址：{APP_REPO}"
        )
        info_label = ttk.Label(info_frame, text=info_text)
        info_label.pack(anchor='w')
        
        ttk.Separator(main_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        # Changelog
        changelog_label = ttk.Label(
            main_frame, 
            text="更新日志", 
            font=('Segoe UI', 10, 'bold')
        )
        changelog_label.pack(anchor='w', pady=(0, 5))
        
        changelog_widget = scrolledtext.ScrolledText(
            main_frame, 
            height=15, 
            wrap=tk.WORD, 
            font=('Consolas', 9),
            background='#f5f5f5'
        )
        changelog_widget.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        changelog_widget.insert(tk.END, get_changelog_text())
        changelog_widget.config(state='disabled')
        
        # Copyright
        copyright_label = ttk.Label(
            main_frame, 
            text=APP_COPYRIGHT,
            font=('Segoe UI', 9),
            foreground='#666666'
        )
        copyright_label.pack()
        
        # Close button
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(btn_frame, text="关闭", command=lambda: [window.destroy(), root.destroy()]).pack(side='right')
        
        window.mainloop()
    
    def notify(self, title, message=""):
        try:
            self.icon.notify(message, title)
        except Exception:
            pass
    
    def _exit(self, icon=None):
        TrayService._exit_requested = True
        self._virtual_camera_running = False
        if self._virtual_camera:
            try:
                self._virtual_camera.stop()
            except:
                pass
            self._virtual_camera = None
        
        if self.server_process and self.server_process.poll() is None:
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=2)
            except:
                self.server_process.kill()
            self.server_process = None
        
        # 清理网络资源
        self._net_manager.cleanup()
        
        self._force_close_port(SERVER_PORT)
        
        if hasattr(self, 'icon') and self.icon:
            try:
                self.icon.stop()
            except:
                pass
    
    def _force_close_port(self, port):
        try:
            import subprocess
            result = subprocess.run(
                ['netstat', '-ano'],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            for line in result.stdout.split('\n'):
                if f':{port}' in line and 'LISTENING' in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        pid = parts[-1]
                        if pid.isdigit():
                            subprocess.run(
                                ['taskkill', '/F', '/PID', pid],
                                capture_output=True,
                                timeout=5,
                                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                            )
        except Exception:
            pass
    
    def run(self):
        threading.Thread(target=self._check_status, daemon=True).start()
        
        self.icon = pystray.Icon(
            name="ControlHubServer",
            icon=self.icon_red,
            title="Control Hub Server",
            menu=Menu(lambda *args: self.get_menu(*args))
        )
        self.icon.on_click = self.on_click
        
        def auto_start_server():
            time.sleep(1)
            print("[INFO] Auto-starting server...")
            self._start_server(self.icon)
        
        threading.Thread(target=auto_start_server, daemon=True).start()
        
        self.icon.run()


def main():
    print("=" * 50)
    print(f"  {APP_NAME} Server v{APP_VERSION}")
    print("=" * 50)
    print(f"  Server script: {SERVER_SCRIPT}")
    print(f"  Port: {SERVER_PORT}")
    print(f"  Log file: {LOG_FILE}")
    print()
    print("  Right-click tray icon for menu")
    print("  Left-click to cast image quickly")
    print("  Double-click to open status window")
    print("  Press Ctrl+C to exit")
    print("=" * 50)
    
    service = TrayService()
    
    def signal_handler(sig, frame):
        print("\n[INFO] Exiting...")
        TrayService._exit_requested = True
        service._exit()
        os._exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        service.run()
    except KeyboardInterrupt:
        signal_handler(None, None)


if __name__ == "__main__":
    main()
