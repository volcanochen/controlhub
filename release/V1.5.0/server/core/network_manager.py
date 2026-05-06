#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一网络通道管理模块
管理USB和WiFi通道，提供统一接口
"""

import os
import sys
import json
import subprocess
import threading
from pathlib import Path


class NetworkManager:
    """统一网络通道管理类"""
    
    # 默认配置
    DEFAULT_HOST = "192.168.50.132"
    DEFAULT_PORT = 8766
    DEFAULT_CHANNEL = "auto"
    
    def __init__(self, config_path=None):
        self._lock = threading.RLock()
        
        # 配置文件路径
        if config_path is None:
            config_path = Path(__file__).parent.parent / "camera" / "config.json"
        self.config_path = Path(config_path)
        
        # 内部状态
        self._host = None
        self._port = None
        self._channel = None
        self._config_mtime = 0
        
        # ADB状态
        self._adb_path = None
        self._adb_forward_active = False
        self._usb_device_connected = False
        
        # 初始化ADB路径
        self._init_adb_path()
    
    def _init_adb_path(self):
        """初始化ADB路径"""
        if sys.platform == 'win32':
            local_app_data = os.environ.get('LOCALAPPDATA', '')
            if local_app_data:
                adb_path = Path(local_app_data) / "Android" / "Sdk" / "platform-tools" / "adb.exe"
                if adb_path.exists():
                    self._adb_path = str(adb_path)
        if self._adb_path is None:
            self._adb_path = "adb"
    
    def _reload_config_if_changed(self):
        """检查配置文件并重新加载"""
        try:
            if self.config_path.exists():
                mtime = self.config_path.stat().st_mtime
                if mtime != self._config_mtime:
                    self._config_mtime = mtime
                    with open(self.config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        self._host = config.get("host")
                        self._port = config.get("port")
                        self._channel = config.get("channel", self.DEFAULT_CHANNEL)
        except Exception as e:
            print(f"[WARN] Failed to reload config: {e}")
    
    def _save_config(self):
        """保存当前配置到文件"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            config = {
                "host": self._host or self.DEFAULT_HOST,
                "port": self._port or self.DEFAULT_PORT,
                "channel": self._channel or self.DEFAULT_CHANNEL
            }
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            self._config_mtime = self.config_path.stat().st_mtime
        except Exception as e:
            print(f"[WARN] Failed to save config: {e}")
    
    @property
    def host(self):
        with self._lock:
            self._reload_config_if_changed()
            return self._host or self.DEFAULT_HOST
    
    @property
    def port(self):
        with self._lock:
            self._reload_config_if_changed()
            return self._port or self.DEFAULT_PORT
    
    @property
    def channel(self):
        with self._lock:
            self._reload_config_if_changed()
            return self._channel or self.DEFAULT_CHANNEL
    
    @property
    def is_usb_connected(self):
        with self._lock:
            return self._usb_device_connected
    
    @property
    def is_adb_forward_active(self):
        with self._lock:
            return self._adb_forward_active
    
    def set_host(self, host):
        """设置摄像头主机地址"""
        with self._lock:
            self._host = host
            self._save_config()
    
    def set_port(self, port):
        """设置摄像头端口"""
        with self._lock:
            self._port = int(port)
            self._save_config()
    
    def set_channel(self, channel):
        """设置通道类型"""
        with self._lock:
            if channel not in ["usb", "wifi", "auto"]:
                raise ValueError("Invalid channel type. Must be 'usb', 'wifi', or 'auto'")
            self._channel = channel
            self._save_config()
            
            if channel == "usb":
                self._setup_usb_channel()
            elif channel == "wifi":
                self._cleanup_usb_channel()
    
    def check_usb_devices(self):
        """检查USB设备连接状态"""
        with self._lock:
            try:
                result = subprocess.run(
                    [self._adb_path, 'devices'],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                )
                lines = result.stdout.strip().split('\n')
                valid_devices = []
                offline_devices = []
                
                for line in lines[1:]:
                    if line.strip() and 'List' not in line:
                        parts = line.split('\t')
                        if len(parts) >= 2:
                            status = parts[1].strip()
                            if status == 'device':
                                valid_devices.append(parts[0])
                            elif status == 'offline':
                                offline_devices.append(parts[0])
                
                if offline_devices:
                    print(f"[WARN] Device(s) offline: {offline_devices}, attempting reconnect...")
                    self._reconnect_adb()
                
                self._usb_device_connected = len(valid_devices) > 0
                return self._usb_device_connected
            except Exception as e:
                print(f"[WARN] Failed to check USB devices: {e}")
                self._usb_device_connected = False
                return False
    
    def _reconnect_adb(self):
        """重新连接ADB"""
        try:
            print("[INFO] Attempting ADB reconnect...")
            result = subprocess.run(
                [self._adb_path, 'reconnect'],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            if result.returncode == 0:
                print(f"[INFO] ADB reconnect: {result.stdout.strip()}")
            
            import time
            time.sleep(2)
            
            result = subprocess.run(
                [self._adb_path, 'devices'],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            print(f"[INFO] ADB devices: {result.stdout.strip()}")
        except Exception as e:
            print(f"[WARN] ADB reconnect failed: {e}")
    
    def _setup_usb_channel(self):
        """设置USB通道（ADB转发）"""
        try:
            subprocess.run(
                [self._adb_path, 'forward', f'tcp:{self.port}', f'tcp:{self.port}'],
                capture_output=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            self._adb_forward_active = True
            return True
        except Exception as e:
            print(f"[WARN] Failed to setup USB channel: {e}")
            self._adb_forward_active = False
            return False
    
    def _cleanup_usb_channel(self):
        """清理USB通道"""
        try:
            subprocess.run(
                [self._adb_path, 'forward', '--remove', f'tcp:{self.port}'],
                capture_output=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            self._adb_forward_active = False
        except Exception as e:
            print(f"[WARN] Failed to cleanup USB channel: {e}")
    
    def get_effective_url(self, path=""):
        """获取当前有效的URL"""
        with self._lock:
            channel = self.channel.lower()
            
            if channel == "usb":
                if self.check_usb_devices():
                    self._setup_usb_channel()
                    return f"http://localhost:{self.port}{path}"
                return None
            elif channel == "wifi":
                return f"http://{self.host}:{self.port}{path}"
            else:  # auto
                if self.check_usb_devices():
                    self._setup_usb_channel()
                    return f"http://localhost:{self.port}{path}"
                return f"http://{self.host}:{self.port}{path}"
    
    def cleanup(self):
        """清理所有资源"""
        with self._lock:
            self._cleanup_usb_channel()


# 全局单例
_network_manager = None
_network_manager_lock = threading.Lock()


def get_network_manager(config_path=None):
    """获取网络管理器单例"""
    global _network_manager
    with _network_manager_lock:
        if _network_manager is None:
            _network_manager = NetworkManager(config_path)
        return _network_manager


def reset_network_manager():
    """重置网络管理器（用于测试）"""
    global _network_manager
    with _network_manager_lock:
        if _network_manager:
            _network_manager.cleanup()
        _network_manager = None
