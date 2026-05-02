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
from io import BytesIO
from pathlib import Path

import pystray
from pystray import MenuItem, Menu
from PIL import Image, ImageDraw, ImageFont


SERVER_PORT = 8765
SERVER_URL = f"localhost:{SERVER_PORT}"
SERVER_SCRIPT = Path(__file__).parent.parent / "usb_display_control.py"
LOG_FILE = Path(__file__).parent.parent / "server.log"

ICON_SIZE = (64, 64)
STATUS_CHECK_INTERVAL = 3


class TrayService:
    
    def __init__(self):
        self.server_process = None
        self.server_running = False
        self.current_image_name = None
        self.current_scale = 1.0
        self.last_error = None
        
        self.icon_green = self._create_icon((0, 180, 0), "G")
        self.icon_red = self._create_icon((200, 50, 50), "X")
        self.icon_yellow = self._create_icon((255, 180, 0), "!")
    
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
        return Menu(
            MenuItem(self._build_status_text(), lambda i: None, enabled=False),
            Menu.SEPARATOR,
            MenuItem('Start Server', self._start_server, visible=lambda _: not self.server_running),
            MenuItem('Stop Server', self._stop_server, visible=lambda _: self.server_running),
            Menu.SEPARATOR,
            MenuItem('Cast Image...', self._cast_image),
            MenuItem('Clear Image', self._clear_image),
            Menu.SEPARATOR,
            MenuItem('Open Status Window', self._open_status_window),
            MenuItem('View Server Log', self._view_log),
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
                self.notify("Server Started", f"Listening on port {SERVER_PORT}")
            else:
                self.last_error = "Failed to start server"
                
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
    
    def _clear_image(self, icon, item=None):
        status, result = self._api_post("/image/clear")
        if status == 200:
            self.notify("Image Cleared")
            self.current_image_name = None
        else:
            self.notify("Error", "Failed to clear image")
    
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
    
    def _open_status_window(self, icon=None):
        import tkinter as tk
        from tkinter import ttk, scrolledtext
        
        root = tk.Tk()
        root.withdraw()
        
        window = tk.Toplevel(root)
        window.title("Image Casting Service Status")
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
    
    def notify(self, title, message=""):
        try:
            self.icon.notify(title, message)
        except Exception:
            pass
    
    def _exit(self, icon=None):
        self._stop_server(icon, None)
        if hasattr(self, 'icon'):
            self.icon.stop()
    
    def run(self):
        threading.Thread(target=self._check_status, daemon=True).start()
        
        self.icon = pystray.Icon(
            name="ImageCastingService",
            icon=self.icon_red,
            title="Image Casting Service",
            menu=Menu(lambda *args: self.get_menu(*args))
        )
        self.icon.on_click = self.on_click
        self.icon.run()


def main():
    print("=" * 50)
    print("  Image Casting Tray Service")
    print("=" * 50)
    print(f"  Server script: {SERVER_SCRIPT}")
    print(f"  Port: {SERVER_PORT}")
    print(f"  Log file: {LOG_FILE}")
    print()
    print("  Right-click tray icon for menu")
    print("  Left-click to cast image quickly")
    print("  Double-click to open status window")
    print("=" * 50)
    
    service = TrayService()
    service.run()


if __name__ == "__main__":
    main()
