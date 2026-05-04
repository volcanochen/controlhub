#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Virtual Camera Module
将手机摄像头视频流输出为虚拟摄像头，供 Teams/Zoom 等应用使用
"""

import threading
import time
import requests
import numpy as np
import cv2
from typing import Optional, Callable
from PIL import Image
from PIL.ExifTags import TAGS


class VirtualCamera:
    """虚拟摄像头管理器"""
    
    def __init__(self):
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._camera_url: Optional[str] = None
        self._cam = None
        self._frame_width = 1280
        self._frame_height = 720
        self._fps = 20
        self._on_error: Optional[Callable] = None
        self._on_status: Optional[Callable] = None
        
    @property
    def is_running(self) -> bool:
        return self._running
    
    @property
    def device_name(self) -> str:
        if self._cam:
            return self._cam.device
        return "OBS Virtual Camera"
    
    def set_callbacks(self, on_error: Callable = None, on_status: Callable = None):
        self._on_error = on_error
        self._on_status = on_status
    
    def _get_exif_rotation(self, jpg_data: bytes):
        """
        从JPEG数据中读取EXIF方向信息
        
        EXIF Orientation值:
        1 = Normal
        3 = Rotate 180
        6 = Rotate 90 CW (需要顺时针90度)
        8 = Rotate 270 CW / 90 CCW (需要逆时针90度)
        """
        try:
            import io
            img = Image.open(io.BytesIO(jpg_data))
            exif = img._getexif()
            
            if exif is not None:
                orientation = 0
                camera_facing = "back"
                
                for tag, value in exif.items():
                    tag_name = TAGS.get(tag, tag)
                    if tag_name == "Orientation":
                        if value == 3:
                            orientation = 180
                        elif value == 6:
                            orientation = 90
                        elif value == 8:
                            orientation = -90
                
                exif_bytes = img.info.get("exif", b"")
                if b"front" in exif_bytes:
                    camera_facing = "front"
                
                return orientation, camera_facing
        except:
            pass
        return 0, "back"
    
    def _apply_rotation(self, frame, rotation: int, camera_facing: str):
        """
        应用旋转和镜像
        
        rotation: 正数表示顺时针，负数表示逆时针
        """
        if rotation == 90:
            frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        elif rotation == -90:
            frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
        elif rotation == 180:
            frame = cv2.rotate(frame, cv2.ROTATE_180)
        
        if camera_facing == "front":
            frame = cv2.flip(frame, 1)
        
        return frame
    
    def start(self, camera_url: str, width: int = 1280, height: int = 720, fps: int = 20) -> bool:
        if self._running:
            return True
        
        self._camera_url = camera_url
        self._frame_width = width
        self._frame_height = height
        self._fps = fps
        
        try:
            import pyvirtualcam
        except ImportError:
            if self._on_error:
                self._on_error("pyvirtualcam not installed. Run: pip install pyvirtualcam")
            return False
        
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        return True
    
    def stop(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1)
        self._thread = None
        self._cam = None
    
    def _run_loop(self):
        import pyvirtualcam
        
        try:
            self._cam = pyvirtualcam.Camera(
                width=self._frame_width,
                height=self._frame_height,
                fps=self._fps,
                fmt=pyvirtualcam.PixelFormat.BGR
            )
            
            if self._on_status:
                self._on_status(f"Virtual camera started: {self._cam.device}")
            
            stream_url = f"{self._camera_url}/camera/stream"
            
            while self._running:
                try:
                    resp = requests.get(stream_url, stream=True, timeout=10)
                    
                    if resp.status_code != 200:
                        if self._on_error:
                            self._on_error(f"Stream failed: {resp.status_code}")
                        time.sleep(1)
                        continue
                    
                    buffer = b""
                    for chunk in resp.iter_content(chunk_size=4096):
                        if not self._running:
                            break
                        
                        buffer += chunk
                        
                        while b'\xff\xd8' in buffer and b'\xff\xd9' in buffer:
                            start = buffer.find(b'\xff\xd8')
                            end = buffer.find(b'\xff\xd9', start) + 2
                            
                            if end > start:
                                jpg_data = buffer[start:end]
                                buffer = buffer[end:]
                                
                                try:
                                    rotation, camera_facing = self._get_exif_rotation(jpg_data)
                                    
                                    np_array = np.frombuffer(jpg_data, dtype=np.uint8)
                                    frame = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
                                    
                                    if frame is not None:
                                        frame = self._apply_rotation(frame, rotation, camera_facing)
                                        frame = cv2.resize(frame, (self._frame_width, self._frame_height))
                                        self._cam.send(frame)
                                        self._cam.sleep_until_next_frame()
                                except Exception:
                                    pass
                            else:
                                break
                                
                except requests.exceptions.RequestException as e:
                    if self._on_error and self._running:
                        self._on_error(f"Connection error: {e}")
                    time.sleep(2)
                except Exception as e:
                    if self._on_error and self._running:
                        self._on_error(f"Error: {e}")
                    time.sleep(1)
                    
        except Exception as e:
            if self._on_error:
                self._on_error(f"Failed to start virtual camera: {e}\nMake sure OBS Studio is installed.")
        finally:
            self._cam = None
            self._running = False
            if self._on_status:
                self._on_status("Virtual camera stopped")


_virtual_camera: Optional[VirtualCamera] = None


def get_virtual_camera() -> VirtualCamera:
    global _virtual_camera
    if _virtual_camera is None:
        _virtual_camera = VirtualCamera()
    return _virtual_camera


def check_obs_installed() -> bool:
    """检查 OBS Studio 是否已安装"""
    import os
    paths = [
        os.path.expandvars(r"%ProgramFiles%\obs-studio\bin\64bit\obs64.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\obs-studio\bin\64bit\obs64.exe"),
    ]
    return any(os.path.exists(p) for p in paths)


def check_virtual_camera_available() -> tuple:
    """
    检查虚拟摄像头是否可用
    返回: (available: bool, message: str)
    """
    try:
        import pyvirtualcam
    except ImportError:
        return False, "pyvirtualcam not installed. Run: pip install pyvirtualcam"
    
    if not check_obs_installed():
        return False, "OBS Studio not installed. Download from: https://obsproject.com/download"
    
    return True, "Virtual camera available"


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Virtual Camera")
    parser.add_argument("--check", action="store_true", help="Check if virtual camera is available")
    parser.add_argument("--host", default="localhost", help="Camera server host")
    parser.add_argument("--port", type=int, default=8766, help="Camera server port")
    parser.add_argument("--width", type=int, default=1280, help="Virtual camera width")
    parser.add_argument("--height", type=int, default=720, help="Virtual camera height")
    parser.add_argument("--fps", type=int, default=20, help="Virtual camera fps")
    
    args = parser.parse_args()
    
    if args.check:
        available, message = check_virtual_camera_available()
        print(f"Available: {available}")
        print(f"Message: {message}")
        exit(0 if available else 1)
    
    print("Starting virtual camera...")
    print(f"Source: http://{args.host}:{args.port}/camera/stream")
    print(f"Output: OBS Virtual Camera ({args.width}x{args.height} @ {args.fps}fps)")
    print("Press Ctrl+C to stop")
    
    vc = VirtualCamera()
    vc.set_callbacks(
        on_error=lambda e: print(f"[ERROR] {e}"),
        on_status=lambda s: print(f"[STATUS] {s}")
    )
    
    try:
        vc.start(
            camera_url=f"http://{args.host}:{args.port}",
            width=args.width,
            height=args.height,
            fps=args.fps
        )
        
        while vc.is_running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping...")
        vc.stop()
