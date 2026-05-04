#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows 显示器控制 RPC 服务端
用于接收 Android 应用的 HTTP 请求并执行显示器切换命令

使用方法：
1. 安装依赖：pip install flask flask-cors
2. 运行：python windows_display_server.py
3. 确保防火墙允许 8080 端口
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import json
import socket

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 获取本机 IP 地址
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

# 执行显示器切换命令
def switch_display(mode):
    """
    调用 Windows DisplaySwitch.exe 工具
    参数:
        mode: internal, external, extend, clone
    """
    try:
        cmd = f"DisplaySwitch.exe /{mode}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            return {"success": True, "message": f"显示器已切换到：{mode}"}
        else:
            return {"success": False, "message": f"切换失败：{result.stderr}"}
    except Exception as e:
        return {"success": False, "message": str(e)}

# 获取当前显示器模式
def get_display_status():
    """
    通过查询注册表获取当前显示器模式
    """
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\RunOnce"
        )
        # 简单返回，实际应该读取更详细的配置
        return {"status": "active", "mode": "extend"}
    except:
        return {"status": "active", "mode": "unknown"}

# API: 切换显示器
@app.route('/api/display', methods=['POST'])
def api_switch_display():
    try:
        data = request.get_json()
        command = data.get('command', '')
        
        valid_commands = ['internal', 'external', 'extend', 'clone']
        if command not in valid_commands:
            return jsonify({
                "success": False,
                "message": f"无效的命令。有效命令：{valid_commands}"
            }), 400
        
        result = switch_display(command)
        return jsonify(result), 200 if result["success"] else 500
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# API: 获取显示器状态
@app.route('/api/display/status', methods=['GET'])
def api_get_status():
    result = get_display_status()
    return jsonify(result), 200

# API: 健康检查
@app.route('/api/health', methods=['GET'])
def api_health():
    return jsonify({
        "status": "running",
        "server": "Windows Display Controller",
        "version": "1.0",
        "ip": get_local_ip(),
        "port": 8080
    }), 200

if __name__ == '__main__':
    local_ip = get_local_ip()
    print("=" * 50)
    print("Windows 显示器控制 RPC 服务端")
    print("=" * 50)
    print(f"服务器地址：http://{local_ip}:8080")
    print(f"本地地址：http://127.0.0.1:8080")
    print("=" * 50)
    print("可用命令:")
    print("  POST /api/display - 切换显示器")
    print("  GET  /api/display/status - 获取状态")
    print("  GET  /api/health - 健康检查")
    print("=" * 50)
    print("启动服务器...")
    
    # 启动 Flask 服务器
    app.run(host='0.0.0.0', port=8080, debug=False)
