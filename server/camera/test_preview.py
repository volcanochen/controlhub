#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试预览窗口
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from camera_client import CameraClient


def test_preview():
    print("[TEST] 启动预览窗口测试")
    client = CameraClient()
    try:
        client.show_preview("ControlHub Camera 测试")
    except KeyboardInterrupt:
        print("\n[TEST] 用户中断")
    except Exception as e:
        print(f"\n[TEST] 错误: {e}")


if __name__ == "__main__":
    test_preview()

