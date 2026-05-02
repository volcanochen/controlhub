#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ADB 广播监听器 - Windows 显示器控制
监听来自 Android 手机的 ADB 广播并执行显示器切换命令

使用方法：
1. 确保已安装 ADB 工具（Android SDK Platform Tools）
2. 手机通过 USB 连接电脑，并开启 USB 调试
3. 运行此脚本：python adb_listener.py
4. 在 Android 应用中切换显示器模式
"""

import subprocess
import sys
import time

# ADB 广播 Action
ACTION_DISPLAY_SWITCH = "com.windows.DISPLAY_SWITCH"
EXTRA_MODE = "mode"

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
            print(f"❌ 无效的模式：{mode}")
            return False
        
        cmd = f"DisplaySwitch.exe {cmd_map[mode]}"
        print(f"📺 执行命令：{cmd}")
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ 显示器已切换到：{mode}")
            return True
        else:
            print(f"❌ 切换失败：{result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 执行出错：{e}")
        return False

def listen_for_broadcast():
    """
    监听 ADB 广播
    """
    print("=" * 60)
    print("ADB 显示器控制监听器")
    print("=" * 60)
    print(f"监听 Action: {ACTION_DISPLAY_SWITCH}")
    print("=" * 60)
    print("步骤：")
    print("1. 确保手机通过 USB 连接电脑")
    print("2. 手机已开启 USB 调试模式")
    print("3. 在手机上运行 Clock 应用")
    print("4. 切换显示器模式开关")
    print("=" * 60)
    print("等待 ADB 广播...")
    print()
    
    # 检查 ADB 是否可用
    try:
        result = subprocess.run(["adb", "version"], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            print("❌ ADB 未安装或不在 PATH 中")
            print("请安装 Android SDK Platform Tools")
            return
        print("✅ ADB 已就绪")
    except FileNotFoundError:
        print("❌ ADB 未找到，请安装 Android SDK Platform Tools")
        print("下载地址：https://developer.android.com/studio/releases/platform-tools")
        return
    except Exception as e:
        print(f"❌ 检查 ADB 失败：{e}")
        return
    
    # 等待设备连接
    print("等待设备连接...")
    subprocess.run(["adb", "wait-for-device"], timeout=30)
    print("✅ 设备已连接")
    print()
    
    # 持续监听广播
    last_broadcast_time = 0
    
    while True:
        try:
            # 使用 logcat 监听广播
            cmd = ["adb", "logcat", "-s", "ActivityManager:I", "BroadcastQueue:I"]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE, text=True)
            
            print("📡 开始监听广播...")
            print("按 Ctrl+C 停止")
            print()
            
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                
                # 检查是否包含我们的广播 Action
                if ACTION_DISPLAY_SWITCH in line:
                    current_time = time.time()
                    # 避免重复处理（1 秒内的重复广播）
                    if current_time - last_broadcast_time < 1:
                        continue
                    
                    last_broadcast_time = current_time
                    
                    # 提取 mode 参数
                    mode = None
                    if EXTRA_MODE + "=" in line:
                        parts = line.split(EXTRA_MODE + "=")
                        if len(parts) > 1:
                            mode_part = parts[1].split()[0].strip()
                            mode = mode_part
                    
                    if mode:
                        print(f"📨 收到广播：mode={mode}")
                        switch_display(mode)
                    else:
                        print(f"⚠️  收到广播但未找到 mode 参数：{line}")
                
        except KeyboardInterrupt:
            print("\n🛑 停止监听")
            if process:
                process.terminate()
            break
        except Exception as e:
            print(f"❌ 监听出错：{e}")
            print("5 秒后重试...")
            time.sleep(5)

if __name__ == '__main__':
    try:
        listen_for_broadcast()
    except KeyboardInterrupt:
        print("\n👋 程序已退出")
    except Exception as e:
        print(f"\n❌ 程序异常退出：{e}")
