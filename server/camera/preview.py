#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
摄像头预览窗口 - 独立进程运行
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from camera_client import CameraClient


def main():
    parser = argparse.ArgumentParser(description="Camera Preview")
    parser.add_argument("--host", default="localhost", help="Camera host")
    parser.add_argument("--port", type=int, default=8766, help="Camera port")
    args = parser.parse_args()
    
    client = CameraClient(args.host, args.port)
    client.show_preview("ControlHub Camera")


if __name__ == "__main__":
    main()
