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
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
RELEASE_DIR = PROJECT_ROOT / "release"
APK_PATH = PROJECT_ROOT / "app" / "build" / "outputs" / "apk" / "debug" / "app-debug.apk"
TEST_DIR = PROJECT_ROOT / "test" / "integration"

SERVER_EXCLUDE = [
    "imagecast",
    "scripts",
    "static",
    "tools",
]

DOC_FILES = {
    "README.md": "README.md",
    "docs/DESIGN.md": "docs/DESIGN.md",
    "docs/CAMERA_MODULE_SPEC.md": "docs/CAMERA_MODULE_SPEC.md",
}


def log(msg):
    print(f"  {msg}")


def get_version():
    """从app_info.py读取版本号"""
    app_info_path = PROJECT_ROOT / "server" / "core" / "app_info.py"
    if not app_info_path.exists():
        return "1.5.0"
    with open(app_info_path, "r", encoding="utf-8") as f:
        content = f.read()
        match = re.search(r'APP_VERSION\s*=\s*"([^"]+)"', content)
        if match:
            return match.group(1)
    return "1.5.0"


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


def clean_version_dir(target_dir):
    """只清理目标版本目录，保留其他版本"""
    if not target_dir.exists():
        return
    log(f"清理旧版本: {target_dir.name}")
    for item in list(target_dir.iterdir()):
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()


def copy_server_dir(src_dir, dst_dir):
    dst_dir.mkdir(parents=True, exist_ok=True)
    for item in src_dir.iterdir():
        if item.is_dir() and item.name in SERVER_EXCLUDE:
            continue
        if item.is_dir() and item.name == "__pycache__":
            continue
        if item.is_file() and item.suffix == ".pyc":
            continue
        if item.is_file() and item.name in ["server.log"]:
            continue
        dst_item = dst_dir / item.name
        if item.is_dir():
            copy_server_dir(item, dst_item)
        else:
            shutil.copy2(item, dst_item)
            size_kb = dst_item.stat().st_size / 1024
            log(f"  {dst_item.relative_to(RELEASE_DIR)} ({size_kb:.1f} KB)")


def copy_file(src_rel, dst_rel, target_dir):
    src = PROJECT_ROOT / src_rel
    dst = target_dir / dst_rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    size_kb = dst.stat().st_size / 1024
    log(f"{dst_rel} ({size_kb:.1f} KB)")


def generate_app_info():
    script_path = PROJECT_ROOT / "tools" / "generate_app_info.py"
    if script_path.exists():
        log("更新应用信息...")
        subprocess.run(
            [sys.executable, str(script_path)],
            cwd=PROJECT_ROOT,
            capture_output=True
        )


def run_tests(target_dir):
    test_script = PROJECT_ROOT / "test" / "run_all_tests.py"
    if not test_script.exists():
        return True
    log("运行测试...")
    subprocess.run(
        [sys.executable, str(test_script)],
        cwd=str(PROJECT_ROOT / "test"),
        capture_output=True,
        text=True
    )
    report_src = PROJECT_ROOT / "test" / "test_report_detailed.html"
    if report_src.exists():
        version = get_version()
        report_dst = target_dir / f"test_report_v{version}.html"
        shutil.copy2(report_src, report_dst)
        log(f"测试报告已保存: {report_dst.name}")
    return True


def main():
    version = get_version()
    version_dir = RELEASE_DIR / f"V{version}"
    
    print("=" * 60)
    print(f" ControlHub v{version} - 发布打包工具")
    print("=" * 60)
    print()
    
    generate_app_info()
    clean_version_dir(version_dir)
    
    print()
    print("--- 构建 ---")
    if not build_apk():
        sys.exit(1)
    
    print()
    print("--- 测试 ---")
    run_tests(version_dir)
    
    print()
    print("--- 复制文件 ---")
    
    log("复制 APK...")
    shutil.copy2(APK_PATH, version_dir / "app-debug.apk")
    log(f"app-debug.apk ({APK_PATH.stat().st_size / 1024:.0f} KB)")
    
    log("复制服务器目录...")
    copy_server_dir(PROJECT_ROOT / "server", version_dir / "server")
    
    log("复制文档...")
    for src, dst in DOC_FILES.items():
        copy_file(src, dst, version_dir)
    
    print()
    print("=" * 60)
    total_size = sum(f.stat().st_size for f in version_dir.rglob("*") if f.is_file())
    file_count = len(list(version_dir.rglob("*")))
    print(f" 发布完成！")
    print(f" 版本: v{version}")
    print(f" 目录: {version_dir}")
    print(f" 文件数: {file_count}")
    print(f" 总大小: {total_size / 1024 / 1024:.1f} MB")
    print("=" * 60)


if __name__ == "__main__":
    main()
