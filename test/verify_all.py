#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整功能验证脚本 - 确保所有模块正常工作
"""

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "server"))

TEST_RESULTS = []


def log_test(name, passed, details=""):
    status = "[PASS]" if passed else "[FAIL]"
    print(f"  {status} - {name}")
    if details:
        print(f"      {details}")
    TEST_RESULTS.append((name, passed, details))


def verify_core_modules():
    print("\n" + "="*60)
    print("  验证核心模块 - Core Modules")
    print("="*60)
    
    # 1. Verify app_info.py
    print("\n  [1/6] 验证 app_info.py...")
    try:
        from core.app_info import (
            APP_NAME, APP_VERSION, APP_COPYRIGHT,
            APP_DESCRIPTION, APP_AUTHOR, APP_REPO,
            get_app_info, get_changelog_text
        )
        
        assert APP_NAME == "ControlHub"
        assert APP_VERSION == "1.5.0"
        assert len(APP_COPYRIGHT) > 0
        
        info = get_app_info()
        assert "name" in info
        assert "version" in info
        assert info["version"] == "1.5.0"
        
        changelog = get_changelog_text()
        assert "v1.5.0" in changelog
        
        log_test("app_info.py", True, f"APP_VERSION={APP_VERSION}, 所有变量正常")
    except Exception as e:
        log_test("app_info.py", False, str(e))
    
    # 2. Verify network_manager.py
    print("\n  [2/6] 验证 network_manager.py...")
    try:
        from core.network_manager import NetworkManager
        
        nm = NetworkManager()
        assert nm is not None
        assert hasattr(nm, "host")
        assert hasattr(nm, "port")
        assert hasattr(nm, "channel")
        
        host = nm.host
        port = nm.port
        channel = nm.channel
        
        log_test("network_manager.py", True, f"host={host}, port={port}, channel={channel}")
    except Exception as e:
        log_test("network_manager.py", False, str(e))


def verify_tray_imports():
    print("\n" + "="*60)
    print("  验证托盘服务导入 - Tray Service Imports")
    print("="*60)
    
    print("\n  [3/6] 验证 tray_service.py 导入...")
    try:
        # 只是验证导入，不运行GUI
        import importlib.util
        
        tray_path = PROJECT_ROOT / "server" / "tray" / "tray_service.py"
        
        spec = importlib.util.spec_from_file_location("tray_service", tray_path)
        tray_module = importlib.util.module_from_spec(spec)
        
        # 执行模块，但不运行 main()
        sys.modules["tray_service"] = tray_module
        
        # 重写 main() 避免执行
        original_main = getattr(tray_module, "main", None)
        
        def dummy_main():
            pass
        
        if original_main:
            tray_module.main = dummy_main
        
        spec.loader.exec_module(tray_module)
        
        # 验证关键变量被导入
        assert hasattr(tray_module, "APP_NAME")
        assert hasattr(tray_module, "APP_VERSION")
        assert hasattr(tray_module, "TrayService")
        
        assert tray_module.APP_NAME == "ControlHub"
        assert tray_module.APP_VERSION == "1.5.0"
        
        log_test("tray_service.py 导入", True, "所有导入正常，APP_NAME/APP_VERSION 可用")
    except Exception as e:
        log_test("tray_service.py 导入", False, str(e))


def verify_camera_module():
    print("\n" + "="*60)
    print("  验证相机模块 - Camera Module")
    print("="*60)
    
    print("\n  [4/6] 验证 camera_client.py...")
    try:
        from camera.camera_client import CameraClient
        
        client = CameraClient()
        assert client is not None
        assert hasattr(client, "host")
        assert hasattr(client, "port")
        
        log_test("camera_client.py", True, f"client初始化成功, host={client.host}")
    except Exception as e:
        log_test("camera_client.py", False, str(e))
    
    print("\n  [5/6] 验证 preview.py...")
    try:
        import importlib.util
        
        preview_path = PROJECT_ROOT / "server" / "camera" / "preview.py"
        spec = importlib.util.spec_from_file_location("preview", preview_path)
        preview_module = importlib.util.module_from_spec(spec)
        
        # 不执行 main()
        sys.modules["preview"] = preview_module
        preview_module.main = lambda: None
        
        spec.loader.exec_module(preview_module)
        
        log_test("preview.py", True, "预览模块导入成功")
    except Exception as e:
        log_test("preview.py", False, str(e))


def verify_release_package():
    print("\n" + "="*60)
    print("  验证发布包 - Release Package")
    print("="*60)
    
    print("\n  [6/6] 验证发布目录结构...")
    release_dir = PROJECT_ROOT / "release" / "V1.5.0"
    
    try:
        assert release_dir.exists(), "V1.5.0 目录不存在"
        
        required_files = [
            "app-debug.apk",
            "README.md",
            "server/tray/tray_service.py",
            "server/core/app_info.py",
            "server/core/network_manager.py",
            "server/camera/camera_client.py",
            "docs/DESIGN.md",
            "test_report_v1.5.0.html"
        ]
        
        missing = []
        for f in required_files:
            if not (release_dir / f).exists():
                missing.append(f)
        
        if missing:
            log_test("发布包结构", False, f"缺少文件: {missing}")
        else:
            log_test("发布包结构", True, f"所有核心文件存在")
            
    except Exception as e:
        log_test("发布包结构", False, str(e))


def print_summary():
    print("\n" + "="*60)
    print("  验证结果总结 - Summary")
    print("="*60)
    
    total = len(TEST_RESULTS)
    passed = sum(1 for _, p, _ in TEST_RESULTS if p)
    failed = sum(1 for _, p, _ in TEST_RESULTS if not p)
    
    print(f"\n  总数: {total}")
    print(f"  通过: {passed}")
    print(f"  失败: {failed}")
    
    if failed == 0:
        print("\n  [SUCCESS] 所有验证通过！")
    else:
        print("\n  [WARNING] 有验证失败，请检查！")
        print("\n  失败项:")
        for name, passed, details in TEST_RESULTS:
            if not passed:
                print(f"    [FAIL] {name}: {details}")
    
    return failed == 0


def main():
    print("="*60)
    print("  ControlHub v1.5.0 - 完整功能验证")
    print("="*60)
    
    verify_core_modules()
    verify_tray_imports()
    verify_camera_module()
    verify_release_package()
    
    success = print_summary()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
