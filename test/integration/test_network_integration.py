#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成测试 - 测试模块间协作
"""

import sys
from pathlib import Path
import time

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "server"))

# 测试用例元数据
TEST_CASES = [
    {
        "id": "IT-MOD-001",
        "name": "test_tray_imports",
        "purpose": "验证Tray服务能够正确导入和使用核心模块",
        "steps": [
            "1. 从core.app_info导入APP_VERSION",
            "2. 从core.network_manager导入NetworkManager",
            "3. 验证APP_VERSION值为'1.5.0'",
            "4. 验证NetworkManager可以初始化"
        ],
        "expected": "所有模块能够正确导入，版本信息正确，NetworkManager可以正常实例化",
        "actual": "",
        "status": "pending"
    },
    {
        "id": "IT-MOD-002",
        "name": "test_camera_module_imports",
        "purpose": "验证相机模块能够正常导入和初始化",
        "steps": [
            "1. 从camera.camera_client导入CameraClient",
            "2. 验证CameraClient类可以正常实例化"
        ],
        "expected": "CameraClient可以正常导入和实例化",
        "actual": "",
        "status": "pending"
    },
    {
        "id": "IT-MOD-003",
        "name": "test_tray_integration_with_network_manager",
        "purpose": "验证Tray服务与NetworkManager之间的集成",
        "steps": [
            "1. 创建NetworkManager实例",
            "2. 通过属性访问获取host、port、channel信息",
            "3. 验证返回值的类型和内容"
        ],
        "expected": "能够正确获取所有网络配置信息，类型正确",
        "actual": "",
        "status": "pending"
    },
    {
        "id": "IT-MOD-004",
        "name": "test_about_info_source",
        "purpose": "验证About信息来自统一的app_info模块",
        "steps": [
            "1. 导入get_app_info和get_changelog_text函数",
            "2. 验证get_app_info返回的信息正确性",
            "3. 验证get_changelog_text返回的内容正确性"
        ],
        "expected": "About信息全部来自app_info模块，且与预期一致",
        "actual": "",
        "status": "pending"
    }
]


def test_tray_imports():
    """测试Tray服务的导入链"""
    test_case = TEST_CASES[0]
    print(f"  [TEST] {test_case['id']}: {test_case['name']}")
    
    try:
        from core.app_info import APP_VERSION
        from core.network_manager import NetworkManager
        
        assert APP_VERSION == "1.5.0"
        
        nm = NetworkManager()
        assert nm is not None
        
        test_case["status"] = "passed"
        test_case["actual"] = "模块导入成功，NetworkManager实例化成功"
        print("  [PASS]")
        return True
    except Exception as e:
        test_case["status"] = "failed"
        test_case["actual"] = str(e)
        print(f"  [FAIL] {e}")
        return False


def test_camera_module_imports():
    """测试相机模块的导入"""
    test_case = TEST_CASES[1]
    print(f"  [TEST] {test_case['id']}: {test_case['name']}")
    
    try:
        from camera.camera_client import CameraClient
        
        client = CameraClient()
        assert client is not None
        
        test_case["status"] = "passed"
        test_case["actual"] = "CameraClient模块导入和实例化成功"
        print("  [PASS]")
        return True
    except Exception as e:
        test_case["status"] = "failed"
        test_case["actual"] = str(e)
        print(f"  [FAIL] {e}")
        return False


def test_tray_integration_with_network_manager():
    """测试Tray和NetworkManager的集成"""
    test_case = TEST_CASES[2]
    print(f"  [TEST] {test_case['id']}: {test_case['name']}")
    
    try:
        from core.network_manager import NetworkManager
        
        nm = NetworkManager()
        assert nm is not None
        
        info = {
            "host": nm.host,
            "port": nm.port,
            "channel": nm.channel
        }
        assert isinstance(info, dict)
        assert "host" in info
        assert "port" in info
        assert "channel" in info
        
        test_case["status"] = "passed"
        test_case["actual"] = f"成功获取网络信息: host={info['host']}, port={info['port']}, channel={info['channel']}"
        print("  [PASS]")
        return True
    except Exception as e:
        test_case["status"] = "failed"
        test_case["actual"] = str(e)
        print(f"  [FAIL] {e}")
        return False


def test_about_info_source():
    """测试About信息的统一来源"""
    test_case = TEST_CASES[3]
    print(f"  [TEST] {test_case['id']}: {test_case['name']}")
    
    try:
        from core.app_info import (
            get_app_info,
            get_changelog_text,
            APP_VERSION
        )
        
        info = get_app_info()
        assert info["version"] == APP_VERSION
        assert info["version"] == "1.5.0"
        
        changelog = get_changelog_text()
        assert "v1.5.0" in changelog
        
        test_case["status"] = "passed"
        test_case["actual"] = "About信息验证通过，来源统一"
        print("  [PASS]")
        return True
    except Exception as e:
        test_case["status"] = "failed"
        test_case["actual"] = str(e)
        print(f"  [FAIL] {e}")
        return False


def run_all():
    """运行所有集成测试"""
    tests = [
        test_tray_imports,
        test_camera_module_imports,
        test_tray_integration_with_network_manager,
        test_about_info_source
    ]
    
    print("=" * 60)
    print("  INTEGRATION TESTS")
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
