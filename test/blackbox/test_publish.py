#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
黑盒测试 - 测试发布包完整性
"""

import sys
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
RELEASE_DIR = PROJECT_ROOT / "release" / "V1.5.0"

# 测试用例元数据
TEST_CASES = [
    {
        "id": "BB-PUB-001",
        "name": "test_publish_structure",
        "purpose": "验证发布包的目录结构是否完整",
        "steps": [
            "1. 检查release目录是否存在",
            "2. 检查server子目录是否存在",
            "3. 检查server/core子目录是否存在",
            "4. 检查server/tray子目录是否存在",
            "5. 检查server/camera子目录是否存在",
            "6. 检查docs子目录是否存在"
        ],
        "expected": "所有必需的目录都存在，结构完整",
        "actual": "",
        "status": "pending"
    },
    {
        "id": "BB-PUB-002",
        "name": "test_publish_core_files",
        "purpose": "验证发布包包含所有核心文件",
        "steps": [
            "1. 检查app_info.py是否存在",
            "2. 检查network_manager.py是否存在",
            "3. 检查tray_service.py是否存在",
            "4. 检查camera_client.py是否存在",
            "5. 检查其他必需文件是否存在"
        ],
        "expected": "所有核心文件都已正确发布",
        "actual": "",
        "status": "pending"
    },
    {
        "id": "BB-PUB-003",
        "name": "test_publish_version",
        "purpose": "验证发布包中的版本信息是否正确",
        "steps": [
            "1. 读取app_info.py文件",
            "2. 检查APP_VERSION是否为'1.5.0'",
            "3. 验证其他版本相关信息"
        ],
        "expected": "版本信息为1.5.0，与当前发布版本一致",
        "actual": "",
        "status": "pending"
    },
    {
        "id": "BB-PUB-004",
        "name": "test_publish_camera_config",
        "purpose": "验证相机配置文件是否已正确发布",
        "steps": [
            "1. 检查server/camera/config.json是否存在",
            "2. 验证文件可以正常读取"
        ],
        "expected": "相机配置文件存在且可以正常读取",
        "actual": "",
        "status": "pending"
    }
]


def test_publish_structure():
    """测试发布包目录结构"""
    test_case = TEST_CASES[0]
    print(f"  [TEST] {test_case['id']}: {test_case['name']}")
    
    try:
        assert RELEASE_DIR.exists()
        assert (RELEASE_DIR / "server").exists()
        assert (RELEASE_DIR / "server" / "core").exists()
        assert (RELEASE_DIR / "server" / "tray").exists()
        assert (RELEASE_DIR / "server" / "camera").exists()
        assert (RELEASE_DIR / "docs").exists()
        
        test_case["status"] = "passed"
        test_case["actual"] = "目录结构验证通过"
        print("  [PASS]")
        return True
    except Exception as e:
        test_case["status"] = "failed"
        test_case["actual"] = str(e)
        print(f"  [FAIL] {e}")
        return False


def test_publish_core_files():
    """测试核心文件存在"""
    test_case = TEST_CASES[1]
    print(f"  [TEST] {test_case['id']}: {test_case['name']}")
    
    try:
        core_files = [
            "server/core/app_info.py",
            "server/core/network_manager.py",
            "server/core/usb_display_control.py",
            "server/core/windows_display_server.py",
            "server/tray/tray_service.py",
            "server/camera/camera_client.py",
            "server/camera/preview.py",
            "server/camera/virtual_camera.py",
            "server/start.bat",
            "README.md"
        ]
        
        missing_files = []
        for f in core_files:
            file_path = RELEASE_DIR / f
            if not file_path.exists():
                missing_files.append(f)
        
        assert len(missing_files) == 0, f"缺少文件: {missing_files}"
        
        test_case["status"] = "passed"
        test_case["actual"] = f"所有{len(core_files)}个核心文件存在"
        print("  [PASS]")
        return True
    except Exception as e:
        test_case["status"] = "failed"
        test_case["actual"] = str(e)
        print(f"  [FAIL] {e}")
        return False


def test_publish_version():
    """测试版本信息是否正确"""
    test_case = TEST_CASES[2]
    print(f"  [TEST] {test_case['id']}: {test_case['name']}")
    
    try:
        app_info_path = RELEASE_DIR / "server" / "core" / "app_info.py"
        assert app_info_path.exists()
        
        with open(app_info_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert 'APP_VERSION = "1.5.0"' in content
        
        test_case["status"] = "passed"
        test_case["actual"] = "版本信息验证通过 (1.5.0)"
        print("  [PASS]")
        return True
    except Exception as e:
        test_case["status"] = "failed"
        test_case["actual"] = str(e)
        print(f"  [FAIL] {e}")
        return False


def test_publish_camera_config():
    """测试相机配置"""
    test_case = TEST_CASES[3]
    print(f"  [TEST] {test_case['id']}: {test_case['name']}")
    
    try:
        config_path = RELEASE_DIR / "server" / "camera" / "config.json"
        assert config_path.exists()
        
        with open(config_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert len(content) > 0
        
        test_case["status"] = "passed"
        test_case["actual"] = "相机配置文件验证通过"
        print("  [PASS]")
        return True
    except Exception as e:
        test_case["status"] = "failed"
        test_case["actual"] = str(e)
        print(f"  [FAIL] {e}")
        return False


def run_all():
    """运行所有黑盒测试"""
    tests = [
        test_publish_structure,
        test_publish_core_files,
        test_publish_version,
        test_publish_camera_config
    ]
    
    print("=" * 60)
    print("  BLACK BOX TESTS - Publish Package")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1
    
    print()
    print(f"  Results: {passed} passed, {failed} failed")
    return passed, failed, TEST_CASES


if __name__ == "__main__":
    run_all()
