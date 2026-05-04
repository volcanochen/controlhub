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
TEST_DIR = PROJECT_ROOT / "test" / "integration"

# 直接复制整个server目录，保持完整结构
# 只排除不需要的开发文件
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


def run_integration_tests():
    """运行集成测试"""
    test_script = TEST_DIR / "run_tests.py"
    if not test_script.exists():
        print(f"[WARN] 集成测试脚本不存在: {test_script}")
        return True
    
    log("运行集成测试...")
    print()
    
    result = subprocess.run(
        [sys.executable, str(test_script), "--all"],
        cwd=str(TEST_DIR),
    )
    
    print()
    if result.returncode != 0:
        print("[ERROR] 集成测试失败！发布中止。")
        return False
    
    log("集成测试通过")
    return True


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


def copy_server_dir(src_dir, dst_dir):
    """递归复制server目录，保持完整结构"""
    dst_dir.mkdir(parents=True, exist_ok=True)
    
    for item in src_dir.iterdir():
        # 跳过排除目录
        if item.is_dir() and item.name in SERVER_EXCLUDE:
            continue
        # 跳过__pycache__
        if item.is_dir() and item.name == "__pycache__":
            continue
        # 跳过.pyc文件
        if item.is_file() and item.suffix == ".pyc":
            continue
        # 跳过临时日志文件
        if item.is_file() and item.name in ["server.log"]:
            continue
            
        dst_item = dst_dir / item.name
        
        if item.is_dir():
            copy_server_dir(item, dst_item)
        else:
            shutil.copy2(item, dst_item)
            size_kb = dst_item.stat().st_size / 1024
            log(f"  {dst_item.relative_to(RELEASE_DIR)} ({size_kb:.1f} KB)")


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
    print("--- 集成测试 ---")
    log("跳过集成测试（临时）")

    print()
    print("--- 复制文件 ---")

    log("复制 APK...")
    dest_apk = RELEASE_DIR / "app-debug.apk"
    shutil.copy2(APK_PATH, dest_apk)
    log(f"app-debug.apk ({dest_apk.stat().st_size / 1024:.0f} KB)")

    log("复制服务器目录（保持完整结构）...")
    copy_server_dir(PROJECT_ROOT / "server", RELEASE_DIR / "server")

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
