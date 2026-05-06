#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行所有测试 - 完整测试套件
"""

import sys
import time
import datetime
from pathlib import Path

TEST_DIR = Path(__file__).parent
PROJECT_ROOT = TEST_DIR.parent

sys.path.insert(0, str(TEST_DIR / "whitebox"))
sys.path.insert(0, str(TEST_DIR / "blackbox"))
sys.path.insert(0, str(TEST_DIR / "integration"))


def log(msg):
    print(f"  {msg}")


def run_test_module(name, module_name):
    print("\n" + "="*60)
    print(f"  {name}")
    print("="*60)
    try:
        module = __import__(module_name)
        result = module.run_all()
        if len(result) == 3:
            passed, failed, _ = result
        else:
            passed, failed = result
        return passed, failed, None
    except Exception as e:
        print(f"  [ERROR] {e}")
        return 0, 1, str(e)


def run_test_script(name, script_path):
    print("\n" + "="*60)
    print(f"  {name}")
    print("="*60)
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(script_path.parent),
            capture_output=True,
            text=True,
            timeout=60
        )
        print(result.stdout)
        if result.stderr:
            print("  [STDERR] " + result.stderr)
        if result.returncode == 0:
            return 1, 0, None
        else:
            return 0, 1, f"Exit code: {result.returncode}"
    except Exception as e:
        print(f"  [ERROR] {e}")
        return 0, 1, str(e)


def generate_html_report(results, start_time, end_time):
    test_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    duration = "{:.2f}".format(end_time - start_time)
    
    total_tests = 0
    total_passed = 0
    total_failed = 0
    
    html_parts = []
    
    html_parts.append("""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ControlHub v1.5.0 - 完整测试报告</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; background: white; border-radius: 15px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); overflow: hidden; }
        .header { background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%); color: white; padding: 40px; text-align: center; }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 20px; padding: 30px; background: #f8f9fa; }
        .summary-card { background: white; padding: 20px; border-radius: 10px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .summary-card h3 { color: #666; font-size: 0.9em; margin-bottom: 10px; text-transform: uppercase; }
        .summary-card .value { font-size: 2em; font-weight: bold; }
        .passed .value { color: #4CAF50; }
        .failed .value { color: #f44336; }
        .total .value { color: #2196F3; }
        .content { padding: 30px; }
        .category { margin-bottom: 40px; }
        .category h2 { color: #333; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 3px solid #4CAF50; font-size: 1.5em; }
        .test-item { background: #f9f9f9; border: 1px solid #ddd; border-radius: 8px; margin-bottom: 15px; padding: 15px; }
        .test-item.pass { border-left: 4px solid #4CAF50; }
        .test-item.fail { border-left: 4px solid #f44336; }
        .test-name { font-weight: bold; font-size: 1.1em; margin-bottom: 5px; }
        .test-status { display: inline-block; padding: 3px 10px; border-radius: 15px; font-size: 0.9em; font-weight: bold; }
        .status-pass { background: #d4edda; color: #155724; }
        .status-fail { background: #f8d7da; color: #721c24; }
        .test-error { margin-top: 10px; padding: 10px; background: #fff3cd; border-radius: 5px; color: #856404; }
        .footer { text-align: center; padding: 30px; color: #666; background: #f8f9fa; border-top: 1px solid #ddd; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>[TEST] ControlHub v1.5.0</h1>
            <p>完整测试报告 - Full Test Report</p>
        </div>""")
    
    # Summary will be filled later
    html_parts.append("<div class='summary'></div>")
    html_parts.append("<div class='content'>")
    
    for name, passed, failed, error in results:
        total_tests += passed + failed
        total_passed += passed
        total_failed += failed
        
        status_class = "pass" if failed == 0 else "fail"
        status_text = "[PASS] 全部通过" if failed == 0 else f"[FAIL] 失败 {failed}"
        
        html_parts.append(f"""
        <div class='category'>
            <h2>[TEST] {name}</h2>
            <div class='test-item {status_class}'>
                <div class='test-name'>{name}</div>
                <span class='test-status status-pass'>通过: {passed}</span>
                <span class='test-status status-fail'>失败: {failed}</span>""")
        
        if error:
            html_parts.append(f"<div class='test-error'>错误: {error}</div>")
        
        html_parts.append("</div></div>")
    
    html_parts.append("</div>")
    
    # Now fill the summary
    if total_tests > 0:
        pass_rate = "{:.1f}".format((total_passed / total_tests) * 100)
    else:
        pass_rate = "0.0"
    
    summary_html = f"""
    <div class="summary">
        <div class="summary-card total"><h3>总测试数</h3><div class="value">{total_tests}</div></div>
        <div class="summary-card passed"><h3>[PASS] 通过</h3><div class="value">{total_passed}</div></div>
        <div class="summary-card failed"><h3>[FAIL] 失败</h3><div class="value">{total_failed}</div></div>
        <div class="summary-card total"><h3>通过率</h3><div class="value">{pass_rate}%</div></div>
        <div class="summary-card total"><h3>总耗时</h3><div class="value">{duration}s</div></div>
    </div>"""
    
    html_str = "".join(html_parts)
    html_str = html_str.replace("<div class='summary'></div>", summary_html)
    
    html_str += f"""
        <div class="footer">
            <p>测试时间: {test_time}</p>
            <p>报告生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>"""
    
    local_report = TEST_DIR / "test_report_full.html"
    with open(local_report, "w", encoding="utf-8") as f:
        f.write(html_str)
    
    release_report = PROJECT_ROOT / "release" / f"test_report_v1.5.0.html"
    release_report.parent.mkdir(exist_ok=True)
    with open(release_report, "w", encoding="utf-8") as f:
        f.write(html_str)
    
    return local_report, release_report


def main():
    print("=" * 60)
    print("  ControlHub v1.5.0 - 完整测试套件")
    print("=" * 60)
    
    start_time = time.time()
    results = []
    
    # --- Whitebox ---
    print("\n" + "="*60)
    print("  [WHITEBOX] 白盒测试 - Whitebox Tests")
    print("="*60)
    
    passed, failed, error = run_test_module("AppInfo", "test_app_info")
    results.append(("白盒 - AppInfo", passed, failed, error))
    
    passed, failed, error = run_test_module("NetworkManager", "test_network_manager")
    results.append(("白盒 - NetworkManager", passed, failed, error))
    
    # --- Blackbox ---
    print("\n" + "="*60)
    print("  [BLACKBOX] 黑盒测试 - Blackbox Tests")
    print("="*60)
    
    passed, failed, error = run_test_module("发布包验证", "test_publish")
    results.append(("黑盒 - 发布包", passed, failed, error))
    
    # --- Integration ---
    print("\n" + "="*60)
    print("  [INTEGRATION] 集成测试 - Integration Tests")
    print("="*60)
    
    passed, failed, error = run_test_module("网络模块集成", "test_network_integration")
    results.append(("集成 - 网络模块", passed, failed, error))
    
    # --- Display Tests ---
    print("\n" + "="*60)
    print("  [DISPLAY] 显示控制测试 - Display Tests")
    print("="*60)
    
    display_test1 = TEST_DIR / "display" / "test_displays.py"
    if display_test1.exists():
        passed, failed, error = run_test_script("显示检测", display_test1)
        results.append(("显示 - 检测", passed, failed, error))
    
    display_test2 = TEST_DIR / "display" / "test_display_control.py"
    if display_test2.exists():
        passed, failed, error = run_test_script("显示控制", display_test2)
        results.append(("显示 - 控制", passed, failed, error))
    
    # --- Network Tests ---
    print("\n" + "="*60)
    print("  [NETWORK] 网络测试 - Network Tests")
    print("="*60)
    
    adb_test = TEST_DIR / "network" / "test_adb.py"
    if adb_test.exists():
        passed, failed, error = run_test_script("ADB 连接", adb_test)
        results.append(("网络 - ADB", passed, failed, error))
    
    # --- Image Cast ---
    print("\n" + "="*60)
    print("  [IMAGECAST] 图像投射测试 - Image Cast Tests")
    print("="*60)
    
    api_test = TEST_DIR / "imagecast" / "test_api.py"
    if api_test.exists():
        passed, failed, error = run_test_script("API 测试", api_test)
        results.append(("图像 - API", passed, failed, error))
    
    # --- Summary ---
    end_time = time.time()
    local_report, release_report = generate_html_report(results, start_time, end_time)
    
    print("\n" + "="*60)
    print("  [SUCCESS] 测试完成！")
    print("="*60)
    
    total_passed = sum(r[1] for r in results)
    total_failed = sum(r[2] for r in results)
    print(f"\n  总通过: {total_passed}")
    print(f"  总失败: {total_failed}")
    print(f"  总耗时: {end_time - start_time:.2f}秒")
    print(f"\n  完整报告 (本地): {local_report}")
    print(f"  完整报告 (发布): {release_report}")
    
    return total_failed


if __name__ == "__main__":
    exit_code = main()
    sys.exit(0 if exit_code == 0 else 1)
