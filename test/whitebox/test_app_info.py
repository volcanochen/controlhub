#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
白盒测试 - 测试 app_info.py
"""

import sys
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "server"))

from core.app_info import (
    APP_NAME,
    APP_VERSION,
    APP_COPYRIGHT,
    APP_DESCRIPTION,
    APP_AUTHOR,
    APP_REPO,
    VERSION_CHANGELOG,
    get_changelog_text,
    get_app_info
)

# 测试用例元数据
TEST_CASES = [
    {
        "id": "WB-APP-001",
        "name": "test_app_info_constants",
        "purpose": "验证app_info.py中的所有常量是否正确定义",
        "steps": [
            "1. 导入app_info模块",
            "2. 检查APP_NAME是否为'ControlHub'",
            "3. 检查APP_VERSION是否为'1.5.0'",
            "4. 检查其他必填字段是否非空"
        ],
        "expected": "所有常量都有正确的值，且非空",
        "actual": "",
        "status": "pending"
    },
    {
        "id": "WB-APP-002",
        "name": "test_changelog",
        "purpose": "验证更新日志数据结构是否完整",
        "steps": [
            "1. 检查VERSION_CHANGELOG是否为列表类型",
            "2. 检查列表长度至少为1",
            "3. 检查最新版本是否为1.5.0"
        ],
        "expected": "更新日志包含完整的版本信息，最新版本为1.5.0",
        "actual": "",
        "status": "pending"
    },
    {
        "id": "WB-APP-003",
        "name": "test_get_changelog_text",
        "purpose": "验证get_changelog_text()函数能正确生成格式化文本",
        "steps": [
            "1. 调用get_changelog_text()获取文本",
            "2. 检查返回值是否为字符串类型",
            "3. 检查文本中是否包含'v1.5.0'"
        ],
        "expected": "生成的文本包含正确的版本信息，格式正确",
        "actual": "",
        "status": "pending"
    },
    {
        "id": "WB-APP-004",
        "name": "test_get_app_info",
        "purpose": "验证get_app_info()函数能正确返回完整信息",
        "steps": [
            "1. 调用get_app_info()获取信息字典",
            "2. 检查返回值是否为字典类型",
            "3. 检查字典是否包含所有必填字段"
        ],
        "expected": "返回的字典包含name、version、copyright、changelog等所有必填字段",
        "actual": "",
        "status": "pending"
    }
]


def test_app_info_constants():
    """测试基本常量"""
    test_case = TEST_CASES[0]
    print(f"  [TEST] {test_case['id']}: {test_case['name']}")
    
    try:
        assert APP_NAME == "ControlHub"
        assert APP_VERSION == "1.5.0"
        assert isinstance(APP_COPYRIGHT, str) and len(APP_COPYRIGHT) > 0
        assert isinstance(APP_DESCRIPTION, str) and len(APP_DESCRIPTION) > 0
        assert isinstance(APP_AUTHOR, str) and len(APP_AUTHOR) > 0
        assert isinstance(APP_REPO, str) and len(APP_REPO) > 0
        
        test_case["status"] = "passed"
        test_case["actual"] = "所有常量值正确"
        print("  [PASS]")
        return True
    except Exception as e:
        test_case["status"] = "failed"
        test_case["actual"] = str(e)
        print(f"  [FAIL] {e}")
        return False


def test_changelog():
    """测试更新日志"""
    test_case = TEST_CASES[1]
    print(f"  [TEST] {test_case['id']}: {test_case['name']}")
    
    try:
        assert isinstance(VERSION_CHANGELOG, list)
        assert len(VERSION_CHANGELOG) >= 1
        
        latest = VERSION_CHANGELOG[0]
        assert latest["version"] == "1.5.0"
        assert len(latest["changes"]) >= 1
        
        test_case["status"] = "passed"
        test_case["actual"] = f"找到{len(VERSION_CHANGELOG)}个版本，最新版本为1.5.0"
        print("  [PASS]")
        return True
    except Exception as e:
        test_case["status"] = "failed"
        test_case["actual"] = str(e)
        print(f"  [FAIL] {e}")
        return False


def test_get_changelog_text():
    """测试获取格式化更新日志"""
    test_case = TEST_CASES[2]
    print(f"  [TEST] {test_case['id']}: {test_case['name']}")
    
    try:
        text = get_changelog_text()
        assert isinstance(text, str)
        assert "v1.5.0" in text
        assert "摄像头" in text
        
        test_case["status"] = "passed"
        test_case["actual"] = f"文本长度为{len(text)}字符，包含v1.5.0"
        print("  [PASS]")
        return True
    except Exception as e:
        test_case["status"] = "failed"
        test_case["actual"] = str(e)
        print(f"  [FAIL] {e}")
        return False


def test_get_app_info():
    """测试获取完整应用信息"""
    test_case = TEST_CASES[3]
    print(f"  [TEST] {test_case['id']}: {test_case['name']}")
    
    try:
        info = get_app_info()
        assert isinstance(info, dict)
        assert "name" in info
        assert "version" in info
        assert "copyright" in info
        assert "changelog" in info
        assert info["version"] == "1.5.0"
        
        test_case["status"] = "passed"
        test_case["actual"] = f"成功返回包含{len(info.keys())}个字段的字典"
        print("  [PASS]")
        return True
    except Exception as e:
        test_case["status"] = "failed"
        test_case["actual"] = str(e)
        print(f"  [FAIL] {e}")
        return False


def run_all():
    """运行所有白盒测试"""
    tests = [
        test_app_info_constants,
        test_changelog,
        test_get_changelog_text,
        test_get_app_info
    ]
    
    print("=" * 60)
    print("  WHITE BOX TESTS - app_info.py")
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
