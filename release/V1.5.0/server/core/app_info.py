#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ControlHub应用信息 - 统一信息源
Tray和Android端的公共信息都从这里读取
"""

APP_NAME = "ControlHub"
APP_VERSION = "1.5.0"
APP_COPYRIGHT = "Copyright © 2026 Volcano Chen"
APP_DESCRIPTION = "功能强大的 Android 控制台应用，支持通过 USB 和 WiFi 连接控制 Windows 电脑"
APP_AUTHOR = "Volcano Chen"
APP_REPO = "https://github.com/volcanochen/controlhub"

VERSION_CHANGELOG = [
    {
        "version": "1.5.0",
        "date": "2026-05-05",
        "changes": [
            "新增完整的摄像头模块",
            "支持前置/后置摄像头切换",
            "MJPEG视频流实时传输",
            "支持USB和WiFi双通道",
            "二维码扫描功能",
            "Tkinter预览窗口，彩色控制按钮",
            "统一的网络通道管理"
        ]
    },
    {
        "version": "1.4.0",
        "date": "2026-05-03",
        "changes": [
            "USB和WiFi通信支持",
            "设置界面优化",
            "网络连接状态显示"
        ]
    },
    {
        "version": "1.3.0",
        "date": "",
        "changes": [
            "图像投射功能",
            "自动弹窗和关闭"
        ]
    },
    {
        "version": "1.2.0",
        "date": "",
        "changes": [
            "WiFi通信支持",
            "设置界面完善"
        ]
    },
    {
        "version": "1.1.0",
        "date": "",
        "changes": [
            "显示控制功能",
            "单屏/双屏模式切换"
        ]
    },
    {
        "version": "1.0.0",
        "date": "",
        "changes": [
            "初始版本发布",
            "USB显示器控制功能"
        ]
    }
]


def get_changelog_text():
    """获取格式化的更新日志文本"""
    text_lines = []
    for ver_info in VERSION_CHANGELOG:
        line = f"v{ver_info['version']}"
        if ver_info['date']:
            line += f" ({ver_info['date']})"
        text_lines.append(line)
        for change in ver_info['changes']:
            text_lines.append(f"• {change}")
        text_lines.append("")
    return "\n".join(text_lines).rstrip()


def get_app_info():
    """获取完整的应用信息"""
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "copyright": APP_COPYRIGHT,
        "description": APP_DESCRIPTION,
        "author": APP_AUTHOR,
        "repo": APP_REPO,
        "changelog": VERSION_CHANGELOG
    }
