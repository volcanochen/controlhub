#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run Integration Tests
=====================

Usage:
    python run_tests.py              # Run all tests
    python run_tests.py --server     # Only start server
    python run_tests.py --app        # Only test app
    python run_tests.py --ui         # Only UI automation
"""

import sys
import os
import subprocess
import time
from pathlib import Path

TEST_DIR = Path(__file__).parent


def run_test(script: str):
    """Run a test script"""
    print(f"\n{'='*60}")
    print(f"Running: {script}")
    print(f"{'='*60}\n")
    
    result = subprocess.run(
        [sys.executable, script],
        cwd=str(TEST_DIR)
    )
    return result.returncode


def main():
    args = sys.argv[1:]
    
    if not args or "--all" in args:
        # Run all tests
        results = []
        
        # 1. Basic integration test
        results.append(("Integration Test", run_test("test_integration.py")))
        
        # 2. UI automation test
        results.append(("UI Automation", run_test("test_ui_automation.py")))
        
        # Summary
        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)
        for name, code in results:
            status = "PASS" if code == 0 else "FAIL"
            print(f"  {name}: {status}")
        
        failed = sum(1 for _, c in results if c != 0)
        return failed
        
    elif "--server" in args:
        return run_test("test_integration.py")
    elif "--app" in args:
        return run_test("test_integration.py")
    elif "--ui" in args:
        return run_test("test_ui_automation.py")
    else:
        print("Unknown option. Use --all, --server, --app, or --ui")
        return 1


if __name__ == "__main__":
    sys.exit(main())
