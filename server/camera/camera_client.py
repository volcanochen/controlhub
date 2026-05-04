#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ControlHub Camera Client
PC端摄像头客户端，用于接收手机摄像头的MJPEG视频流
"""

import requests
import cv2
import numpy as np
import sys
import os
import argparse
from typing import Optional, Generator, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageTk
from PIL.ExifTags import TAGS


class CameraClient:
    """摄像头客户端"""
    
    _stop_requested = False
    
    def __init__(self, host: str = "localhost", port: int = 8766):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.stream_url = f"{self.base_url}/camera/stream"
        self.timeout = 5
        self.user_rotation = 0
    
    @classmethod
    def request_stop(cls):
        cls._stop_requested = True
    
    @classmethod
    def reset_stop(cls):
        cls._stop_requested = False
    
    def _get_exif_rotation(self, jpg_data: bytes) -> Tuple[int, str]:
        """
        从JPEG数据中读取EXIF方向信息
        返回: (旋转角度, 摄像头方向)
        
        实际测试：
        - 后置摄像头 EXIF=6，不需要旋转
        - 前置摄像头 EXIF=8，不需要旋转
        """
        try:
            import io
            img = Image.open(io.BytesIO(jpg_data))
            exif = img._getexif()
            
            if exif is not None:
                camera_facing = "back"
                exif_value = 0
                
                for tag, value in exif.items():
                    tag_name = TAGS.get(tag, tag)
                    if tag_name == "Orientation":
                        exif_value = value
                
                exif_bytes = img.info.get("exif", b"")
                if b"front" in exif_bytes:
                    camera_facing = "front"
                
                print(f"[DEBUG] EXIF Orientation={exif_value}, facing={camera_facing}")
                return 0, camera_facing
        except Exception as e:
            print(f"[DEBUG] EXIF read error: {e}")
        
        return 0, "back"
    
    def _apply_rotation(self, frame: np.ndarray, rotation: int, camera_facing: str) -> np.ndarray:
        """
        应用旋转和镜像
        
        rotation: 正数表示顺时针，负数表示逆时针
        """
        total_rotation = rotation + self.user_rotation
        
        if total_rotation == 90 or total_rotation == -270:
            frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        elif total_rotation == -90 or total_rotation == 270:
            frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
        elif total_rotation == 180 or total_rotation == -180:
            frame = cv2.rotate(frame, cv2.ROTATE_180)
        elif total_rotation != 0:
            norm_rotation = total_rotation % 360
            if norm_rotation == 90:
                frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
            elif norm_rotation == 180:
                frame = cv2.rotate(frame, cv2.ROTATE_180)
            elif norm_rotation == 270:
                frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
        
        if camera_facing == "front":
            frame = cv2.flip(frame, 1)
        
        return frame
    
    def rotate_cw(self):
        """顺时针旋转90度"""
        self.user_rotation = (self.user_rotation + 90) % 360
        print(f"[INFO] Rotation: {self.user_rotation}°")
    
    def rotate_ccw(self):
        """逆时针旋转90度"""
        self.user_rotation = (self.user_rotation - 90) % 360
        print(f"[INFO] Rotation: {self.user_rotation}°")
    
    def reset_rotation(self):
        """重置旋转"""
        self.user_rotation = 0
        print(f"[INFO] Rotation reset: {self.user_rotation}°")
    
    def get_status(self) -> dict:
        """获取摄像头状态"""
        try:
            response = requests.get(f"{self.base_url}/camera/status", timeout=self.timeout)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"[ERROR] Failed to get status: {e}")
        return {}
    
    def start_camera(self, camera: str = "front") -> bool:
        """启动摄像头"""
        try:
            response = requests.post(
                f"{self.base_url}/camera/start",
                json={"camera": camera},
                timeout=self.timeout
            )
            if response.status_code == 200:
                print(f"[OK] Camera started: {camera}")
                return True
        except Exception as e:
            print(f"[ERROR] Failed to start camera: {e}")
        return False
    
    def stop_camera(self) -> bool:
        """停止摄像头"""
        try:
            response = requests.post(f"{self.base_url}/camera/stop", timeout=self.timeout)
            if response.status_code == 200:
                print("[OK] Camera stopped")
                return True
        except Exception as e:
            print(f"[ERROR] Failed to stop camera: {e}")
        return False
    
    def close_camera(self) -> bool:
        """关闭摄像头Activity"""
        try:
            response = requests.post(f"{self.base_url}/camera/close", timeout=self.timeout)
            if response.status_code == 200:
                print("[OK] Camera closed")
                return True
        except Exception as e:
            print(f"[ERROR] Failed to close camera: {e}")
        return False
    
    def switch_camera(self) -> bool:
        """切换摄像头"""
        try:
            response = requests.post(f"{self.base_url}/camera/switch", timeout=self.timeout)
            if response.status_code == 200:
                result = response.json()
                print(f"[OK] Switched to: {result.get('camera', 'unknown')}")
                print("[INFO] Camera switching, stream will reconnect...")
                return True
        except Exception as e:
            print(f"[ERROR] Failed to switch camera: {e}")
        return False
    
    def get_snapshot(self) -> Optional[bytes]:
        """获取单帧截图"""
        try:
            response = requests.get(f"{self.base_url}/camera/snapshot", timeout=self.timeout)
            if response.status_code == 200:
                return response.content
        except Exception as e:
            print(f"[ERROR] Failed to get snapshot: {e}")
        return None
    
    def _find_adb_path(self):
        """查找ADB路径"""
        adb_path = os.environ.get("ADB_PATH", "adb")
        common_paths = [
            os.path.expanduser("~\\AppData\\Local\\Android\\Sdk\\platform-tools\\adb.exe"),
            "C:\\Users\\volcano\\AppData\\Local\\Android\\Sdk\\platform-tools\\adb.exe",
        ]
        for path in common_paths:
            if os.path.exists(path):
                return path
        return adb_path
    
    def _adb_reconnect(self):
        """尝试ADB重连"""
        import subprocess
        import time
        
        adb_path = self._find_adb_path()
        
        try:
            print("[INFO] Attempting ADB reconnect...")
            result = subprocess.run([adb_path, "reconnect"], capture_output=True, text=True, timeout=10,
                          creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
            if result.returncode == 0:
                print(f"[INFO] ADB reconnect: {result.stdout.strip()}")
            time.sleep(2)
            
            result = subprocess.run([adb_path, "devices"], capture_output=True, text=True, timeout=5,
                          creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
            print(f"[INFO] ADB devices: {result.stdout.strip()}")
            
            print("[INFO] Setting up port forward...")
            subprocess.run([adb_path, "forward", f"tcp:{self.port}", f"tcp:{self.port}"],
                          capture_output=True, timeout=5,
                          creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
            print("[INFO] ADB reconnect completed")
        except Exception as e:
            print(f"[ERROR] ADB reconnect failed: {e}")
    
    def _check_adb_and_reconnect(self):
        """检查ADB设备状态，如果offline则尝试重连"""
        import subprocess
        adb_path = os.environ.get("ADB_PATH", "adb")
        common_paths = [
            os.path.expanduser("~\\AppData\\Local\\Android\\Sdk\\platform-tools\\adb.exe"),
            "C:\\Users\\volcano\\AppData\\Local\\Android\\Sdk\\platform-tools\\adb.exe",
        ]
        for path in common_paths:
            if os.path.exists(path):
                adb_path = path
                break
        
        try:
            result = subprocess.run([adb_path, "devices"], capture_output=True, text=True, timeout=5,
                                   creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
            lines = result.stdout.strip().split('\n')
            has_offline = False
            has_device = False
            
            for line in lines[1:]:
                if line.strip() and 'List' not in line:
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        status = parts[1].strip()
                        if status == 'device':
                            has_device = True
                        elif status == 'offline':
                            has_offline = True
            
            if has_offline or not has_device:
                print(f"[WARN] ADB device offline or not found, attempting reconnect...")
                self._adb_reconnect()
            else:
                print("[INFO] ADB device connected")
                
        except Exception as e:
            print(f"[WARN] Failed to check ADB status: {e}")
    
    def get_stream(self, max_retries: int = 3) -> Generator[bytes, None, None]:
        """获取MJPEG视频流"""
        retry_count = 0
        retry_delay = 1
        adb_reconnect_done = False
        response = None
        total_retries = 0
        max_total_retries = max_retries * 2
        
        while total_retries < max_total_retries and not self._stop_requested:
            try:
                if response is not None:
                    try:
                        response.close()
                    except:
                        pass
                    response = None
                
                response = requests.get(self.stream_url, stream=True, timeout=5)
                if response.status_code != 200:
                    print(f"[ERROR] Stream request failed: {response.status_code}")
                    retry_count += 1
                    total_retries += 1
                    continue
                
                retry_count = 0
                adb_reconnect_done = False
                bytes_data = b''
                for chunk in response.iter_content(chunk_size=1024):
                    if self._stop_requested:
                        response.close()
                        return
                    
                    bytes_data += chunk
                    
                    start = bytes_data.find(b'\xff\xd8')
                    end = bytes_data.find(b'\xff\xd9')
                    
                    if start != -1 and end != -1 and end > start:
                        jpg_data = bytes_data[start:end+2]
                        bytes_data = bytes_data[end+2:]
                        yield jpg_data
                        
            except requests.exceptions.Timeout:
                if self._stop_requested:
                    return
                print(f"[ERROR] Stream timeout")
                retry_count += 1
                total_retries += 1
                if retry_count >= max_retries and not adb_reconnect_done:
                    if response:
                        try:
                            response.close()
                        except:
                            pass
                    self._reconnect_camera()
                    adb_reconnect_done = True
                    retry_count = 0
                if total_retries < max_total_retries:
                    print(f"[INFO] Retrying... ({total_retries}/{max_total_retries})")
                    import time
                    time.sleep(retry_delay)
            except Exception as e:
                if self._stop_requested:
                    return
                error_str = str(e)
                print(f"[ERROR] Stream error: {e}")
                retry_count += 1
                total_retries += 1
                if retry_count >= max_retries and not adb_reconnect_done:
                    if response:
                        try:
                            response.close()
                        except:
                            pass
                    
                    if "prematurely" in error_str.lower():
                        print("[INFO] Response ended prematurely, closing preview...")
                        self._stop_requested = True
                        cv2.destroyAllWindows()
                        self._adb_reconnect()
                        print("[INFO] Preview closed, please reopen manually")
                        return
                    elif "connection" in error_str.lower():
                        self._reconnect_camera()
                    else:
                        self._adb_reconnect()
                    adb_reconnect_done = True
                    retry_count = 0
                if total_retries < max_total_retries:
                    print(f"[INFO] Retrying... ({total_retries}/{max_total_retries})")
                    import time
                    time.sleep(retry_delay)
        
        print(f"[ERROR] Max retries ({max_total_retries}) reached, stopping")
    
    def _reconnect_camera(self):
        """重连摄像头（只做ADB重连，不调用手机端API）"""
        import time
        print("[INFO] Reconnecting camera...")
        self._adb_reconnect()
        time.sleep(1)
        print("[INFO] Reconnect done, retrying stream...")
                    
    def show_preview(self, window_name: str = "ControlHub Camera"):
        """显示预览窗口（使用tkinter）"""
        import tkinter as tk
        from tkinter import font
        import threading
        import queue
        
        self.reset_stop()
        
        if self.host == "localhost":
            self._check_adb_and_reconnect()
        
        print(f"[INFO] Starting preview: {self.stream_url}")
        
        root = tk.Tk()
        root.title(window_name)
        root.protocol("WM_DELETE_WINDOW", lambda: self._close_preview(root))
        root.configure(bg="black")
        
        button_height = 50
        
        button_frame = tk.Frame(root, bg="#3c3c3c", height=button_height)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM)
        button_frame.pack_propagate(False)
        
        btn_font = font.Font(family="Segoe UI", size=11, weight="bold")
        label_font = font.Font(family="Segoe UI", size=11)
        
        rotation_var = tk.StringVar(value="Rotation: 0°")
        rotation_label = tk.Label(button_frame, textvariable=rotation_var, font=label_font, 
                                  bg="#3c3c3c", fg="white")
        rotation_label.pack(side=tk.LEFT, padx=10)
        
        frame_queue = queue.Queue(maxsize=2)
        stream_thread = [None]
        stream_running = [True]
        switch_requested = [False]
        first_frame = [True]
        
        def stream_worker():
            while stream_running[0] and not self._stop_requested:
                try:
                    for jpg_data in self.get_stream():
                        if not stream_running[0] or self._stop_requested:
                            break
                        
                        if switch_requested[0]:
                            switch_requested[0] = False
                            break
                        
                        rotation, camera_facing = self._get_exif_rotation(jpg_data)
                        np_array = np.frombuffer(jpg_data, dtype=np.uint8)
                        frame = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
                        
                        if frame is not None:
                            frame = self._apply_rotation(frame, rotation, camera_facing)
                            
                            try:
                                frame_queue.put_nowait((frame, rotation, camera_facing))
                            except queue.Full:
                                try:
                                    frame_queue.get_nowait()
                                    frame_queue.put_nowait((frame, rotation, camera_facing))
                                except:
                                    pass
                except Exception as e:
                    if stream_running[0] and not self._stop_requested:
                        print(f"[ERROR] Stream worker error: {e}")
                        import time
                        time.sleep(0.5)
        
        def on_rotate_cw():
            self.rotate_cw()
            rotation_var.set(f"Rotation: {self.user_rotation}°")
        
        def on_rotate_ccw():
            self.rotate_ccw()
            rotation_var.set(f"Rotation: {self.user_rotation}°")
        
        def on_reset():
            self.reset_rotation()
            rotation_var.set(f"Rotation: {self.user_rotation}°")
        
        def on_switch():
            print("[INFO] Switching camera...")
            switch_requested[0] = True
            while not frame_queue.empty():
                try:
                    frame_queue.get_nowait()
                except:
                    break
            self.switch_camera()
            print("[INFO] Camera switched")
        
        def on_close():
            self._close_preview(root)
        
        btn_style = {"font": btn_font, "width": 10, "relief": "raised", "bd": 2, "height": 1}
        
        tk.Button(button_frame, text="↻ CW", command=on_rotate_cw, 
                 bg="#4CAF50", fg="white", activebackground="#45a049", **btn_style).pack(side=tk.LEFT, padx=3, pady=8)
        tk.Button(button_frame, text="↺ CCW", command=on_rotate_ccw,
                 bg="#2196F3", fg="white", activebackground="#1976D2", **btn_style).pack(side=tk.LEFT, padx=3, pady=8)
        tk.Button(button_frame, text="Reset", command=on_reset,
                 bg="#FF9800", fg="white", activebackground="#F57C00", **btn_style).pack(side=tk.LEFT, padx=3, pady=8)
        tk.Button(button_frame, text="Switch", command=on_switch,
                 bg="#9C27B0", fg="white", activebackground="#7B1FA2", **btn_style).pack(side=tk.LEFT, padx=3, pady=8)
        tk.Button(button_frame, text="Close", command=on_close,
                 bg="#f44336", fg="white", activebackground="#d32f2f", **btn_style).pack(side=tk.RIGHT, padx=3, pady=8)
        
        video_frame = tk.Frame(root, bg="black")
        video_frame.pack(fill=tk.BOTH, expand=True)
        
        video_label = tk.Label(video_frame, bg="black")
        video_label.place(relx=0.5, rely=0.5, anchor="center")
        
        def resize_image_fit(frame, target_width, target_height):
            frame_h, frame_w = frame.shape[:2]
            scale = min(target_width / frame_w, target_height / frame_h)
            new_w = int(frame_w * scale)
            new_h = int(frame_h * scale)
            return cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
        
        def update_frame():
            if self._stop_requested:
                return
            
            try:
                frame_data = frame_queue.get_nowait()
                frame, rotation, camera_facing = frame_data
                
                frame_h, frame_w = frame.shape[:2]
                
                if first_frame[0]:
                    first_frame[0] = False
                    screen_width = root.winfo_screenwidth()
                    screen_height = root.winfo_screenheight()
                    max_win_width = int(screen_width * 0.9)
                    max_win_height = int(screen_height * 0.9) - button_height
                    scale = min(max_win_width / frame_w, max_win_height / frame_h)
                    win_w = int(frame_w * scale)
                    win_h = int(frame_h * scale) + button_height
                    x = (screen_width - win_w) // 2
                    y = (screen_height - win_h) // 2
                    root.geometry(f"{win_w}x{win_h}+{x}+{y}")
                
                video_frame.update_idletasks()
                avail_w = video_frame.winfo_width()
                avail_h = video_frame.winfo_height()
                
                if avail_w > 1 and avail_h > 1:
                    frame = resize_image_fit(frame, avail_w, avail_h)
                
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                img_tk = ImageTk.PhotoImage(image=img)
                video_label.img_tk = img_tk
                video_label.configure(image=img_tk)
                    
            except queue.Empty:
                pass
            except Exception as e:
                print(f"[ERROR] Update frame error: {e}")
            
            root.after(16, update_frame)
        
        stream_thread[0] = threading.Thread(target=stream_worker, daemon=True)
        stream_thread[0].start()
        
        root.after(100, update_frame)
        root.mainloop()
        
        stream_running[0] = False
    
    def _close_preview(self, root):
        """关闭预览窗口"""
        self._stop_requested = True
        root.destroy()


def main():
    parser = argparse.ArgumentParser(description="ControlHub Camera Client")
    parser.add_argument("--host", default="localhost", help="Camera server host")
    parser.add_argument("--port", type=int, default=8766, help="Camera server port")
    parser.add_argument("--status", action="store_true", help="Get camera status")
    parser.add_argument("--start", choices=["front", "back"], help="Start camera")
    parser.add_argument("--stop", action="store_true", help="Stop camera")
    parser.add_argument("--switch", action="store_true", help="Switch camera")
    parser.add_argument("--preview", action="store_true", help="Show preview window")
    parser.add_argument("--snapshot", type=str, help="Save snapshot to file")
    
    args = parser.parse_args()
    
    client = CameraClient(args.host, args.port)
    
    if args.status:
        status = client.get_status()
        print("Camera Status:")
        for key, value in status.items():
            print(f"  {key}: {value}")
    
    elif args.start:
        client.start_camera(args.start)
    
    elif args.stop:
        client.stop_camera()
    
    elif args.switch:
        client.switch_camera()
    
    elif args.snapshot:
        jpg_data = client.get_snapshot()
        if jpg_data:
            with open(args.snapshot, "wb") as f:
                f.write(jpg_data)
            print(f"[OK] Saved snapshot: {args.snapshot}")
    
    elif args.preview:
        client.show_preview()
    
    else:
        # 默认显示预览
        print(f"Connecting to {args.host}:{args.port}...")
        client.show_preview()


if __name__ == "__main__":
    main()
