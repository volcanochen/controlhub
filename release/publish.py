#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发布脚本 - 将项目打包为可分发的 release 目录
用法: python release/publish.py
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
RELEASE_DIR = PROJECT_ROOT / "release"
APK_PATH = PROJECT_ROOT / "app" / "build" / "outputs" / "apk" / "debug" / "app-debug.apk"

SERVER_FILES = {
    "server/core/usb_display_control.py": "server/usb_display_control.py",
    "server/core/windows_display_server.py": "server/windows_display_server.py",
    "server/tray/tray_service.py": "server/tray_service.py",
}

DISPLAY_FILES = {
    "server/display/brightness_control.ps1": "display/brightness_control.ps1",
    "server/display/get_displays.ps1": "display/get_displays.ps1",
}

DOC_FILES = {
    "README.md": "README.md",
    "docs/DESIGN.md": "docs/DESIGN.md",
}


def log(msg):
    print(f"  {msg}")


def build_apk():
    if APK_PATH.exists():
        log(f"APK already exists: {APK_PATH.name} ({APK_PATH.stat().st_size / 1024:.0f} KB)")
        return True
    log("Building APK...")
    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "gradlew.bat"), "assembleDebug"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"[ERROR] APK build failed:\n{result.stderr}")
        return False
    if not APK_PATH.exists():
        print(f"[ERROR] APK not found at {APK_PATH}")
        return False
    log(f"APK built: {APK_PATH.name} ({APK_PATH.stat().st_size / 1024:.0f} KB)")
    return True


def clean_release():
    target = RELEASE_DIR
    target.mkdir(parents=True, exist_ok=True)
    for item in list(target.iterdir()):
        if item.name == "publish.py":
            continue
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()


def copy_file(src_rel, dst_rel):
    src = PROJECT_ROOT / src_rel
    dst = RELEASE_DIR / dst_rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    size_kb = dst.stat().st_size / 1024
    log(f"{dst_rel} ({size_kb:.1f} KB)")


def main():
    print("=" * 60)
    print(" 控制屏 - 发布打包工具")
    print("=" * 60)
    print()

    clean_release()
    log("清理完成")

    print()
    print("--- 构建 ---")
    if not build_apk():
        sys.exit(1)

    print()
    print("--- 复制文件 ---")

    log("复制 APK...")
    dest_apk = RELEASE_DIR / "app-debug.apk"
    shutil.copy2(APK_PATH, dest_apk)
    log(f"app-debug.apk ({dest_apk.stat().st_size / 1024:.0f} KB)")

    log("复制服务器文件...")
    for src, dst in SERVER_FILES.items():
        copy_file(src, dst)

    log("复制显示器脚本...")
    for src, dst in DISPLAY_FILES.items():
        copy_file(src, dst)

    log("复制文档...")
    for src, dst in DOC_FILES.items():
        copy_file(src, dst)

    print()
    print("=" * 60)
    total_size = sum(f.stat().st_size for f in RELEASE_DIR.rglob("*") if f.is_file())
    file_count = len(list(RELEASE_DIR.rglob("*")))
    print(f" 发布完成！")
    print(f" 目录: {RELEASE_DIR}")
    print(f" 文件数: {file_count}")
    print(f" 总大小: {total_size / 1024 / 1024:.1f} MB")
    print("=" * 60)


if __name__ == "__main__":
    main()
