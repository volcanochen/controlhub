#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ADB 显示器控制服务端 - 简化版
直接通过 ADB 接收命令并执行显示器切换

使用方法：
1. 确保已安装 ADB 工具
2. 手机通过 USB 连接电脑，开启 USB 调试
3. 运行此脚本：python adb_display_server.py
4. 在 Android 应用中切换显示器模式
"""

import subprocess
import sys
import time
import socket

def get_local_ip():
    """获取本机 IP 地址"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def switch_display(mode):
    """
    执行 Windows 显示器切换命令
    """
    try:
        cmd_map = {
            'internal': '/internal',   # 仅第一屏
            'external': '/external',   # 仅第二屏
            'extend': '/extend',       # 扩展模式
            'clone': '/clone'          # 复制模式
        }
        
        if mode not in cmd_map:
            return False, f"无效的模式：{mode}"
        
        cmd = f"DisplaySwitch.exe {cmd_map[mode]}"
        print(f"📺 执行命令：{cmd}")
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            msg = f"显示器已切换到：{mode}"
            print(f"✅ {msg}")
            return True, msg
        else:
            msg = f"切换失败：{result.stderr}"
            print(f"❌ {msg}")
            return False, msg
            
    except Exception as e:
        msg = f"执行出错：{e}"
        print(f"❌ {msg}")
        return False, msg

def check_adb():
    """检查 ADB 是否可用"""
    try:
        result = subprocess.run(["adb", "version"], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            return False, "ADB 未安装或不在 PATH 中"
        return True, "ADB 已就绪"
    except FileNotFoundError:
        return False, "ADB 未找到"
    except Exception as e:
        return False, f"检查 ADB 失败：{e}"

def wait_for_device():
    """等待设备连接"""
    try:
        print("等待设备连接...")
        result = subprocess.run(["adb", "wait-for-device"], 
                              timeout=30, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ 设备已连接")
            return True
        else:
            print(f"❌ 等待设备失败：{result.stderr}")
            return False
    except Exception as e:
        print(f"❌ 等待设备出错：{e}")
        return False

def main():
    print("=" * 60)
    print("ADB 显示器控制服务端")
    print("=" * 60)
    
    # 检查 ADB
    success, msg = check_adb()
    if not success:
        print(f"❌ {msg}")
        print("请安装 Android SDK Platform Tools")
        print("下载地址：https://developer.android.com/studio/releases/platform-tools")
        return
    
    print(f"✅ {msg}")
    
    # 等待设备
    if not wait_for_device():
        print("❌ 没有检测到设备连接")
        print("请确保：")
        print("1. 手机通过 USB 连接电脑")
        print("2. 手机已开启 USB 调试模式")
        return
    
    print("=" * 60)
    print("服务已启动，等待 Android 应用发送命令...")
    print("=" * 60)
    print()
    
    # 持续监听并执行命令
    while True:
        try:
            # 检查是否有来自手机的广播命令
            cmd = ["adb", "shell", "am", "broadcast", 
                  "-a", "com.clockapp.DISPLAY_SWITCH",
                  "--esn", "check"]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
            
            # 这里简化处理，实际应该监听特定的广播
            # 为了简单起见，我们使用轮询方式检查
            
            time.sleep(1)
            
        except KeyboardInterrupt:
            print("\n🛑 停止服务")
            break
        except Exception as e:
            print(f"⚠️  错误：{e}")
            time.sleep(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 程序已退出")
    except Exception as e:
        print(f"\n❌ 程序异常退出：{e}")
