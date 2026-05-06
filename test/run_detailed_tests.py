#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行所有测试并生成详细的专业测试报告
"""

import sys
import time
import datetime
import platform
import subprocess
from pathlib import Path

TEST_DIR = Path(__file__).parent
PROJECT_ROOT = TEST_DIR.parent

sys.path.insert(0, str(TEST_DIR / "whitebox"))
sys.path.insert(0, str(TEST_DIR / "blackbox"))
sys.path.insert(0, str(TEST_DIR / "integration"))


def get_environment_info():
    """获取测试环境信息"""
    return {
        "os": platform.system() + " " + platform.release(),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "test_time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }


def run_test_module(name, module_name, category):
    """运行测试模块并返回详细结果"""
    print("\n" + "="*60)
    print(f"  {name}")
    print("="*60)
    
    result = {
        "category": category,
        "name": name,
        "test_cases": [],
        "passed": 0,
        "failed": 0,
        "error": None,
        "start_time": time.time(),
        "end_time": None
    }
    
    try:
        module = __import__(module_name)
        module_result = module.run_all()
        
        if len(module_result) == 3:
            passed, failed, test_cases = module_result
            result["test_cases"] = test_cases
            result["passed"] = passed
            result["failed"] = failed
        else:
            passed, failed = module_result
            result["passed"] = passed
            result["failed"] = failed
            
    except Exception as e:
        print(f"  [ERROR] {e}")
        result["error"] = str(e)
        result["failed"] = 1
    
    result["end_time"] = time.time()
    result["duration"] = result["end_time"] - result["start_time"]
    return result


def run_test_script(name, script_path, category):
    """运行独立测试脚本"""
    print("\n" + "="*60)
    print(f"  {name}")
    print("="*60)
    
    result = {
        "category": category,
        "name": name,
        "test_cases": [],
        "passed": 0,
        "failed": 0,
        "error": None,
        "start_time": time.time(),
        "end_time": None,
        "stdout": "",
        "stderr": ""
    }
    
    try:
        proc_result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(script_path.parent),
            capture_output=True,
            text=True,
            timeout=120,
            encoding='utf-8',
            errors='replace'
        )
        
        result["stdout"] = proc_result.stdout
        result["stderr"] = proc_result.stderr
        
        print(proc_result.stdout)
        if proc_result.stderr:
            print("  [STDERR] " + proc_result.stderr)
        
        result["passed"] = 1 if proc_result.returncode == 0 else 0
        result["failed"] = 0 if proc_result.returncode == 0 else 1
        
        if proc_result.returncode != 0:
            result["error"] = f"Exit code: {proc_result.returncode}"
            
    except Exception as e:
        print(f"  [ERROR] {e}")
        result["error"] = str(e)
        result["failed"] = 1
    
    result["end_time"] = time.time()
    result["duration"] = result["end_time"] - result["start_time"]
    return result


def generate_html_report(all_results, env_info, start_time, end_time):
    """生成详细的HTML测试报告"""
    total_tests = sum(r["passed"] + r["failed"] for r in all_results)
    total_passed = sum(r["passed"] for r in all_results)
    total_failed = sum(r["failed"] for r in all_results)
    total_duration = end_time - start_time
    
    if total_tests > 0:
        pass_rate = (total_passed / total_tests) * 100
    else:
        pass_rate = 0
    
    html_parts = []
    
    html_parts.append(f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ControlHub v1.5.0 - 详细测试报告</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', 'Microsoft YaHei', Arial, sans-serif; background: linear-gradient(135deg, #1a365d 0%, #2c5282 100%); padding: 20px; line-height: 1.6; }}
        .container {{ max-width: 1400px; margin: 0 auto; background: white; border-radius: 15px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); overflow: hidden; }}
        .header {{ background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%); color: white; padding: 50px 40px; text-align: center; }}
        .header h1 {{ font-size: 2.8em; margin-bottom: 10px; font-weight: 700; }}
        .header .subtitle {{ font-size: 1.2em; opacity: 0.9; margin-top: 10px; }}
        
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 25px; padding: 40px; background: #f7fafc; border-bottom: 3px solid #e2e8f0; }}
        .summary-card {{ background: white; padding: 25px; border-radius: 12px; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.08); transition: transform 0.2s; }}
        .summary-card:hover {{ transform: translateY(-3px); }}
        .summary-card h3 {{ color: #718096; font-size: 0.85em; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; }}
        .summary-card .value {{ font-size: 2.5em; font-weight: 800; }}
        .passed .value {{ color: #38a169; }}
        .failed .value {{ color: #e53e3e; }}
        .total .value {{ color: #3182ce; }}
        .rate .value {{ color: #805ad5; }}
        
        .env-info {{ padding: 30px 40px; background: #edf2f7; border-bottom: 1px solid #e2e8f0; }}
        .env-info h2 {{ color: #2d3748; margin-bottom: 20px; font-size: 1.4em; }}
        .env-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }}
        .env-item {{ background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #3182ce; }}
        .env-item .label {{ color: #718096; font-size: 0.85em; font-weight: 600; }}
        .env-item .value {{ color: #2d3748; font-weight: 600; margin-top: 5px; }}
        
        .content {{ padding: 40px; }}
        
        .category {{ margin-bottom: 50px; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; }}
        .category-header {{ background: linear-gradient(135deg, #4a5568 0%, #2d3748 100%); color: white; padding: 20px 25px; display: flex; justify-content: space-between; align-items: center; }}
        .category-header h2 {{ font-size: 1.4em; font-weight: 600; }}
        .category-stats {{ display: flex; gap: 20px; }}
        .stat-item {{ display: flex; align-items: center; gap: 8px; }}
        .stat-badge {{ padding: 5px 12px; border-radius: 20px; font-weight: 700; font-size: 0.9em; }}
        .stat-badge.pass {{ background: #c6f6d5; color: #22543d; }}
        .stat-badge.fail {{ background: #fed7d7; color: #742a2a; }}
        
        .test-item {{ background: white; border-bottom: 1px solid #e2e8f0; padding: 25px; }}
        .test-item:last-child {{ border-bottom: none; }}
        .test-item.pass {{ border-left: 5px solid #38a169; }}
        .test-item.fail {{ border-left: 5px solid #e53e3e; }}
        
        .test-header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 15px; }}
        .test-id {{ background: #2d3748; color: white; padding: 6px 14px; border-radius: 6px; font-family: 'Consolas', monospace; font-weight: 700; font-size: 0.9em; }}
        .test-status {{ padding: 6px 16px; border-radius: 20px; font-weight: 700; font-size: 0.9em; }}
        .test-status.pass {{ background: #c6f6d5; color: #22543d; }}
        .test-status.fail {{ background: #fed7d7; color: #742a2a; }}
        
        .test-name {{ font-size: 1.2em; font-weight: 700; color: #2d3748; margin: 10px 0; }}
        .test-section {{ margin: 15px 0; }}
        .test-section h4 {{ color: #4a5568; font-size: 0.95em; margin-bottom: 8px; font-weight: 600; }}
        .test-section p, .test-section ul {{ color: #4a5568; margin-left: 10px; }}
        .test-section ul {{ padding-left: 20px; }}
        .test-section li {{ margin: 5px 0; }}
        
        .code-block {{ background: #1a202c; color: #e2e8f0; padding: 15px; border-radius: 8px; font-family: 'Consolas', monospace; font-size: 0.9em; overflow-x: auto; margin-top: 10px; white-space: pre-wrap; word-wrap: break-word; }}
        .code-block.stdout {{ border-left: 4px solid #38a169; }}
        .code-block.stderr {{ border-left: 4px solid #e53e3e; }}
        
        .compare {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 10px; }}
        .compare-box {{ padding: 15px; border-radius: 8px; }}
        .compare-box.expected {{ background: #ebf8ff; border: 1px solid #90cdf4; }}
        .compare-box.actual {{ background: #f0fff4; border: 1px solid #9ae6b4; }}
        .compare-box h5 {{ color: #2c5282; margin-bottom: 8px; font-size: 0.9em; }}
        
        .footer {{ text-align: center; padding: 40px; color: #718096; background: #f7fafc; border-top: 1px solid #e2e8f0; }}
        .footer p {{ margin: 5px 0; }}
        
        .toggle-btn {{ background: #4299e1; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: 600; margin-top: 10px; }}
        .toggle-btn:hover {{ background: #3182ce; }}
        .collapsible {{ display: none; }}
        .collapsible.show {{ display: block; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>ControlHub v1.5.0</h1>
            <p class="subtitle">详细测试报告 - Detailed Test Report</p>
        </div>
        
        <div class="summary">
            <div class="summary-card total">
                <h3>总测试数</h3>
                <div class="value">{total_tests}</div>
            </div>
            <div class="summary-card passed">
                <h3>通过</h3>
                <div class="value">{total_passed}</div>
            </div>
            <div class="summary-card failed">
                <h3>失败</h3>
                <div class="value">{total_failed}</div>
            </div>
            <div class="summary-card rate">
                <h3>通过率</h3>
                <div class="value">{pass_rate:.1f}%</div>
            </div>
            <div class="summary-card total">
                <h3>总耗时</h3>
                <div class="value">{total_duration:.2f}s</div>
            </div>
        </div>
        
        <div class="env-info">
            <h2>📋 测试环境信息</h2>
            <div class="env-grid">
                <div class="env-item">
                    <div class="label">操作系统</div>
                    <div class="value">{env_info['os']}</div>
                </div>
                <div class="env-item">
                    <div class="label">Python版本</div>
                    <div class="value">{env_info['python_version']}</div>
                </div>
                <div class="env-item">
                    <div class="label">平台信息</div>
                    <div class="value">{env_info['platform']}</div>
                </div>
                <div class="env-item">
                    <div class="label">测试时间</div>
                    <div class="value">{env_info['test_time']}</div>
                </div>
            </div>
        </div>
        
        <div class="content">
""")
    
    # 生成每个测试模块的详细报告
    for result in all_results:
        status_class = "pass" if result["failed"] == 0 else "fail"
        
        html_parts.append(f"""
            <div class="category">
                <div class="category-header">
                    <h2>{result['category']} - {result['name']}</h2>
                    <div class="category-stats">
                        <div class="stat-item">
                            <span class="stat-badge pass">通过: {result['passed']}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-badge fail">失败: {result['failed']}</span>
                        </div>
                        <div class="stat-item" style="color: #a0aec0;">
                            耗时: {result['duration']:.2f}s
                        </div>
                    </div>
                </div>
        """)
        
        # 显示详细测试用例
        if result["test_cases"]:
            for tc in result["test_cases"]:
                tc_status = tc.get("status", "pending")
                tc_status_class = "pass" if tc_status == "passed" else "fail"
                tc_status_text = "通过" if tc_status == "passed" else "失败"
                
                html_parts.append(f"""
                <div class="test-item {tc_status_class}">
                    <div class="test-header">
                        <span class="test-id">{tc.get('id', 'N/A')}</span>
                        <span class="test-status {tc_status_class}">{tc_status_text}</span>
                    </div>
                    <div class="test-name">{tc.get('name', 'N/A')}</div>
                    
                    <div class="test-section">
                        <h4>🎯 测试目的</h4>
                        <p>{tc.get('purpose', 'N/A')}</p>
                    </div>
                    
                    <div class="test-section">
                        <h4>📝 测试步骤</h4>
                        <ul>
                """)
                
                for step in tc.get("steps", []):
                    html_parts.append(f"<li>{step}</li>")
                
                html_parts.append("</ul></div>")
                
                html_parts.append(f"""
                    <div class="test-section">
                        <div class="compare">
                            <div class="compare-box expected">
                                <h5>期望结果</h5>
                                <p>{tc.get('expected', 'N/A')}</p>
                            </div>
                            <div class="compare-box actual">
                                <h5>实际结果</h5>
                                <p>{tc.get('actual', 'N/A')}</p>
                            </div>
                        </div>
                    </div>
                """)
                
                html_parts.append("</div>")
        
        # 显示脚本输出
        if "stdout" in result and result["stdout"]:
            html_parts.append(f"""
                <div class="test-item {status_class}">
                    <div class="test-header">
                        <span class="test-id">SCRIPT-OUTPUT</span>
                        <span class="test-status {status_class}">{'通过' if status_class == 'pass' else '失败'}</span>
                    </div>
                    <div class="test-name">{result['name']} - 执行输出</div>
            """)
            
            if result["stdout"]:
                html_parts.append(f"""
                    <div class="test-section">
                        <h4>📤 标准输出</h4>
                        <div class="code-block stdout">{result['stdout']}</div>
                    </div>
                """)
            
            if result["stderr"]:
                html_parts.append(f"""
                    <div class="test-section">
                        <h4>⚠️ 错误输出</h4>
                        <div class="code-block stderr">{result['stderr']}</div>
                    </div>
                """)
            
            if result["error"]:
                html_parts.append(f"""
                    <div class="test-section">
                        <h4>❌ 错误信息</h4>
                        <div class="code-block stderr">{result['error']}</div>
                    </div>
                """)
            
            html_parts.append("</div>")
        
        html_parts.append("</div>")
    
    html_parts.append(f"""
        </div>
        
        <div class="footer">
            <p><strong>报告生成时间:</strong> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>测试执行时长:</strong> {total_duration:.2f} 秒</p>
            <p style="margin-top: 15px; font-size: 0.9em; color: #a0aec0;">
                ControlHub v1.5.0 - 自动化测试报告
            </p>
        </div>
    </div>
</body>
</html>
""")
    
    html_content = "".join(html_parts)
    
    # 保存报告
    local_report = TEST_DIR / "test_report_detailed.html"
    with open(local_report, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    release_report = PROJECT_ROOT / "release" / "test_report_v1.5.0.html"
    release_report.parent.mkdir(exist_ok=True)
    with open(release_report, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    return local_report, release_report


def main():
    print("=" * 70)
    print("  ControlHub v1.5.0 - 详细测试套件")
    print("=" * 70)
    
    start_time = time.time()
    env_info = get_environment_info()
    all_results = []
    
    # 白盒测试
    result = run_test_module("AppInfo", "test_app_info", "白盒测试")
    all_results.append(result)
    
    result = run_test_module("NetworkManager", "test_network_manager", "白盒测试")
    all_results.append(result)
    
    # 黑盒测试
    result = run_test_module("发布包验证", "test_publish", "黑盒测试")
    all_results.append(result)
    
    # 集成测试
    result = run_test_module("网络模块集成", "test_network_integration", "集成测试")
    all_results.append(result)
    
    # 显示测试
    display_test1 = TEST_DIR / "display" / "test_displays.py"
    if display_test1.exists():
        result = run_test_script("显示检测", display_test1, "显示控制")
        all_results.append(result)
    
    display_test2 = TEST_DIR / "display" / "test_display_control.py"
    if display_test2.exists():
        result = run_test_script("显示控制", display_test2, "显示控制")
        all_results.append(result)
    
    # 网络测试
    adb_test = TEST_DIR / "network" / "test_adb.py"
    if adb_test.exists():
        result = run_test_script("ADB连接", adb_test, "网络测试")
        all_results.append(result)
    
    # 图像投射测试
    api_test = TEST_DIR / "imagecast" / "test_api.py"
    if api_test.exists():
        result = run_test_script("图像API", api_test, "图像投射")
        all_results.append(result)
    
    # 生成报告
    end_time = time.time()
    local_report, release_report = generate_html_report(all_results, env_info, start_time, end_time)
    
    # 统计结果
    total_passed = sum(r["passed"] for r in all_results)
    total_failed = sum(r["failed"] for r in all_results)
    
    print("\n" + "=" * 70)
    print("  [SUCCESS] 测试完成！")
    print("=" * 70)
    print(f"\n  总通过: {total_passed}")
    print(f"  总失败: {total_failed}")
    print(f"  总耗时: {end_time - start_time:.2f}秒")
    print(f"\n  详细报告 (本地): {local_report}")
    print(f"  详细报告 (发布): {release_report}")
    
    return total_failed


if __name__ == "__main__":
    exit_code = main()
    sys.exit(0 if exit_code == 0 else 1)
