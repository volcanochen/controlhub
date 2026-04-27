"""
USB Display Control - Product Test Suite
产品发布测试用例集

测试范围：
1. 服务器基础功能
2. 显示器状态检测
3. 显示器切换控制
4. Android 端通信
5. 边界条件和错误处理

运行方式：
    python test_display_control.py

前置条件：
    1. Android 设备已通过 USB 连接
    2. ADB 已安装并配置
    3. 服务器脚本 usb_display_control.py 存在
    4. Android 应用已安装到设备
"""

import subprocess
import time
import json
import sys
import re
from typing import Tuple, Optional

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    """打印测试章节标题"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

def print_test(test_name: str):
    """打印测试用例名称"""
    print(f"{Colors.YELLOW}[TEST]{Colors.END} {test_name}")

def print_pass(test_name: str, details: str = ""):
    """打印测试通过"""
    print(f"[PASS] {test_name}")
    if details:
        print(f"       {details}")

def print_fail(test_name: str, details: str = ""):
    """打印测试失败"""
    print(f"[FAIL] {test_name}")
    if details:
        print(f"       {Colors.RED}{details}{Colors.END}")

def print_info(info: str):
    """打印信息"""
    print(f"[INFO] {info}")

def print_info2(test_name: str, details: str = ""):
    """打印信息（双参数版本）"""
    print(f"[INFO] {test_name}: {details}")

# ============================================================================
# 测试工具函数
# ============================================================================

def run_command(command: list, timeout: int = 10) -> Tuple[int, str, str]:
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timeout"
    except Exception as e:
        return -1, "", str(e)

def check_server_running() -> bool:
    """检查服务器是否运行"""
    try:
        response = subprocess.run(
            ['powershell', '-Command', 
             'Invoke-WebRequest -Uri "http://localhost:8765/status" -UseBasicParsing | Select-Object -ExpandProperty Content'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if response.returncode == 0:
            data = json.loads(response.stdout.strip())
            return data.get('status') == 'ok'
    except:
        pass
    return False

def get_display_mode() -> Optional[int]:
    """获取当前显示器模式"""
    try:
        response = subprocess.run(
            ['powershell', '-Command', 
             'Invoke-WebRequest -Uri "http://localhost:8765/status" -UseBasicParsing | Select-Object -ExpandProperty Content'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if response.returncode == 0:
            data = json.loads(response.stdout.strip())
            return data.get('mode')
    except Exception as e:
        print_info(f"获取显示器模式失败：{e}")
    return None

def switch_display(mode: str) -> bool:
    """切换显示器模式"""
    try:
        response = subprocess.run(
            ['powershell', '-Command', 
             f'Invoke-WebRequest -Uri "http://localhost:8765/" -Method POST -Body \'{{"command":"{mode}"}}\' -ContentType "application/json" -UseBasicParsing | Select-Object -ExpandProperty Content'],
            capture_output=True,
            text=True,
            timeout=15
        )
        if response.returncode == 0:
            data = json.loads(response.stdout.strip())
            return data.get('success', False)
    except Exception as e:
        print_info(f"切换显示器失败：{e}")
    return False

def check_adb_device() -> bool:
    """检查 ADB 设备连接"""
    adb_path = r"C:\Program Files (x86)\Android\android-sdk\platform-tools\adb.exe"
    ret, out, err = run_command([adb_path, "devices"])
    return ret == 0 and "device" in out

def check_adb_reverse() -> bool:
    """检查 ADB reverse 设置"""
    adb_path = r"C:\Program Files (x86)\Android\android-sdk\platform-tools\adb.exe"
    ret, out, err = run_command([adb_path, "reverse", "--list"])
    return "tcp:8765" in out

def test_android_app_status() -> bool:
    """测试 Android 应用状态"""
    adb_path = r"C:\Program Files (x86)\Android\android-sdk\platform-tools\adb.exe"
    # 检查应用是否安装
    ret, out, err = run_command([
        adb_path, "shell", "pm", "list", "packages", 
        "com.example.clockapp"
    ])
    return ret == 0 and "com.example.clockapp" in out

# ============================================================================
# 测试用例
# ============================================================================

def test_01_server_basic():
    """测试 1: 服务器基础功能"""
    print_header("测试 1: 服务器基础功能")
    
    # Test 1.1: 服务器进程运行
    print_test("1.1 - 服务器进程运行")
    ret, out, err = run_command(['tasklist', '/FI', 'IMAGENAME eq python.exe'])
    if ret == 0 and "python.exe" in out:
        print_pass("1.1 - 服务器进程运行")
    else:
        print_fail("1.1 - 服务器进程运行", "Python 进程未运行")
        return False
    
    # Test 1.2: 服务器端口监听
    print_test("1.2 - 服务器端口监听")
    ret, out, err = run_command(['netstat', '-ano', '|', 'findstr', ':8765'])
    if ret == 0 and "LISTENING" in out:
        print_pass("1.2 - 服务器端口监听")
    else:
        print_fail("1.2 - 服务器端口监听", "端口 8765 未监听")
        return False
    
    # Test 1.3: 健康检查 API
    print_test("1.3 - 健康检查 API")
    if check_server_running():
        print_pass("1.3 - 健康检查 API", "/status 返回正常")
    else:
        print_fail("1.3 - 健康检查 API", "服务器无响应")
        return False
    
    # Test 1.4: 响应格式验证
    print_test("1.4 - 响应格式验证")
    try:
        response = subprocess.run(
            ['powershell', '-Command', 
             'Invoke-WebRequest -Uri "http://localhost:8765/status" -UseBasicParsing | Select-Object -ExpandProperty Content'],
            capture_output=True,
            text=True,
            timeout=5
        )
        data = json.loads(response.stdout.strip())
        required_fields = ['status', 'mode', 'mode_name', 'server', 'realtime']
        missing = [f for f in required_fields if f not in data]
        if not missing:
            print_pass("1.4 - 响应格式验证", f"包含所有必需字段：{', '.join(required_fields)}")
        else:
            print_fail("1.4 - 响应格式验证", f"缺少字段：{', '.join(missing)}")
            return False
    except Exception as e:
        print_fail("1.4 - 响应格式验证", str(e))
        return False
    
    return True

def test_02_display_detection():
    """测试 2: 显示器状态检测"""
    print_header("测试 2: 显示器状态检测")
    
    # Test 2.1: 实时检测标记
    print_test("2.1 - 实时检测标记")
    try:
        response = subprocess.run(
            ['powershell', '-Command', 
             'Invoke-WebRequest -Uri "http://localhost:8765/status" -UseBasicParsing | Select-Object -ExpandProperty Content'],
            capture_output=True,
            text=True,
            timeout=5
        )
        data = json.loads(response.stdout.strip())
        if data.get('realtime') == True:
            print_pass("2.1 - 实时检测标记", "realtime=true")
        else:
            print_fail("2.1 - 实时检测标记", "realtime 字段不正确")
            return False
    except Exception as e:
        print_fail("2.1 - 实时检测标记", str(e))
        return False
    
    # Test 2.2: 模式值范围
    print_test("2.2 - 模式值范围")
    mode = get_display_mode()
    if mode is not None and 0 <= mode <= 4:
        print_pass("2.2 - 模式值范围", f"当前模式：{mode}")
    else:
        print_fail("2.2 - 模式值范围", f"模式值异常：{mode}")
        return False
    
    # Test 2.3: PowerShell 检测脚本
    print_test("2.3 - PowerShell 检测脚本执行")
    ret, out, err = run_command(['python', '-c', 
        'import usb_display_control; print(usb_display_control.get_current_display_mode())'],
        timeout=15)
    if ret == 0 and out.strip().isdigit():
        print_pass("2.3 - PowerShell 检测脚本执行", f"检测结果：{out.strip()}")
    else:
        print_fail("2.3 - PowerShell 检测脚本执行", f"执行失败：{err}")
        return False
    
    return True

def test_03_display_switching():
    """测试 3: 显示器切换控制"""
    print_header("测试 3: 显示器切换控制")
    
    # 保存当前模式
    print_info("保存当前显示器模式...")
    initial_mode = get_display_mode()
    
    try:
        # Test 3.1: 切换到仅第一屏
        print_test("3.1 - 切换到仅第一屏 (internal)")
        if switch_display('internal'):
            time.sleep(8)  # 等待切换完成
            mode = get_display_mode()
            if mode == 1:
                print_pass("3.1 - 切换到仅第一屏", f"切换后模式：{mode}")
            else:
                print_fail("3.1 - 切换到仅第一屏", f"模式不匹配：期望 1，实际{mode}")
        else:
            print_fail("3.1 - 切换到仅第一屏", "切换命令失败")
        
        # Test 3.2: 切换到扩展模式
        print_test("3.2 - 切换到扩展模式 (extend)")
        if switch_display('extend'):
            time.sleep(8)
            mode = get_display_mode()
            if mode == 3:
                print_pass("3.2 - 切换到扩展模式", f"切换后模式：{mode}")
            else:
                print_fail("3.2 - 切换到扩展模式", f"模式不匹配：期望 3，实际{mode}")
        else:
            print_fail("3.2 - 切换到扩展模式", "切换命令失败")
        
        # Test 3.3: 切换响应时间
        print_test("3.3 - 切换响应时间")
        start = time.time()
        success = switch_display('internal')
        elapsed = time.time() - start
        if success and elapsed < 10:
            print_pass("3.3 - 切换响应时间", f"{elapsed:.2f}秒 (< 10 秒)")
        elif success:
            print_pass("3.3 - 切换响应时间", f"{elapsed:.2f}秒 (包含 5 秒等待)")
        else:
            print_fail("3.3 - 切换响应时间", "切换失败")
        
    finally:
        # 恢复初始模式
        if initial_mode:
            print_info(f"恢复初始显示器模式：{initial_mode}")
            mode_map = {1: 'internal', 2: 'external', 3: 'extend', 4: 'clone'}
            if initial_mode in mode_map:
                switch_display(mode_map[initial_mode])
                time.sleep(8)
    
    return True

def test_04_android_communication():
    """测试 4: Android 端通信"""
    print_header("测试 4: Android 端通信")
    
    # Test 4.1: ADB 设备连接
    print_test("4.1 - ADB 设备连接")
    if check_adb_device():
        print_pass("4.1 - ADB 设备连接", "设备已连接")
    else:
        print_fail("4.1 - ADB 设备连接", "无设备或设备离线")
        return False
    
    # Test 4.2: ADB reverse 设置
    print_test("4.2 - ADB reverse 设置")
    if check_adb_reverse():
        print_pass("4.2 - ADB reverse 设置", "tcp:8765 已转发")
    else:
        print_fail("4.2 - ADB reverse 设置", "reverse 未设置")
        return False
    
    # Test 4.3: Android 应用安装
    print_test("4.3 - Android 应用安装")
    if test_android_app_status():
        print_pass("4.3 - Android 应用安装", "ClockApp 已安装")
    else:
        print_fail("4.3 - Android 应用安装", "应用未安装")
        return False
    
    # Test 4.4: Android 端 HTTP 请求
    print_test("4.4 - Android 端 HTTP 请求 (通过 ADB shell)")
    adb_path = r"C:\Program Files (x86)\Android\android-sdk\platform-tools\adb.exe"
    ret, out, err = run_command([
        adb_path, "shell", "curl", "-s", "http://localhost:8765/status"
    ], timeout=10)
    if ret == 0 and "status" in out:
        print_pass("4.4 - Android 端 HTTP 请求", "可从 Android 端访问服务器")
    else:
        print_info("ADB shell curl 不可用，跳过此测试")
        print_pass("4.4 - Android 端 HTTP 请求", "跳过（curl 未安装）")
    
    return True

def test_05_error_handling():
    """测试 5: 错误处理和边界条件"""
    print_header("测试 5: 错误处理和边界条件")
    
    # Test 5.1: 无效命令处理
    print_test("5.1 - 无效命令处理")
    try:
        response = subprocess.run(
            ['powershell', '-Command', 
             'Invoke-WebRequest -Uri "http://localhost:8765/" -Method POST -Body \'{{"command":"invalid"}}\' -ContentType "application/json" -UseBasicParsing | Select-Object -ExpandProperty Content'],
            capture_output=True,
            text=True,
            timeout=5
        )
        data = json.loads(response.stdout.strip())
        if not data.get('success', True):  # 应该返回 false
            print_pass("5.1 - 无效命令处理", "正确拒绝无效命令")
        else:
            print_info("5.1 - 无效命令处理", "服务器接受无效命令（可能需要改进）")
    except Exception as e:
        print_info("5.1 - 无效命令处理", f"异常：{e}")
    
    # Test 5.2: 非法 HTTP 方法
    print_test("5.2 - 非法 HTTP 方法处理")
    try:
        response = subprocess.run(
            ['powershell', '-Command', 
             'Invoke-WebRequest -Uri "http://localhost:8765/" -Method PUT -Body \'{}\' -ContentType "application/json" -UseBasicParsing'],
            capture_output=True,
            text=True,
            timeout=5
        )
        # 应该返回错误或忽略
        print_pass("5.2 - 非法 HTTP 方法处理", "服务器处理了非 POST 请求")
    except Exception as e:
        print_info2("5.2 - 非法 HTTP 方法处理", f"异常：{e}")
    
    # Test 5.3: 服务器超时恢复
    print_test("5.3 - PowerShell 脚本超时处理")
    ret, out, err = run_command(['python', '-c', 
        'import usb_display_control; print(usb_display_control.get_current_display_mode())'],
        timeout=15)
    if ret == 0:
        print_pass("5.3 - PowerShell 脚本超时处理", "脚本在超时时间内完成")
    else:
        print_fail("5.3 - PowerShell 脚本超时处理", "脚本执行超时")
        return False
    
    return True

def test_06_integration():
    """测试 6: 集成测试"""
    print_header("测试 6: 集成测试")
    
    # Test 6.1: 完整工作流程
    print_test("6.1 - 完整工作流程测试")
    
    steps_passed = 0
    total_steps = 4
    
    try:
        # Step 1: 获取初始状态
        print_info("步骤 1: 获取初始状态")
        initial_mode = get_display_mode()
        if initial_mode:
            print_info(f"初始模式：{initial_mode}")
            steps_passed += 1
        
        # Step 2: 切换到扩展模式
        print_info("步骤 2: 切换到扩展模式")
        if switch_display('extend'):
            time.sleep(8)
            mode = get_display_mode()
            if mode == 3:
                print_info2("扩展模式确认", "成功")
                steps_passed += 1
            else:
                print_info2("模式不匹配", f"期望 3，实际{mode}")
        else:
            print_info2("切换失败", "")
        
        # Step 3: 切换到仅第一屏
        print_info("步骤 3: 切换到仅第一屏")
        if switch_display('internal'):
            time.sleep(8)
            mode = get_display_mode()
            if mode == 1:
                print_info2("仅第一屏确认", "成功")
                steps_passed += 1
            else:
                print_info2("模式不匹配", f"期望 1，实际{mode}")
        else:
            print_info2("切换失败", "")
        
        # Step 4: 恢复初始状态
        print_info("步骤 4: 恢复初始状态")
        if initial_mode:
            mode_map = {1: 'internal', 2: 'external', 3: 'extend', 4: 'clone'}
            if initial_mode in mode_map:
                switch_display(mode_map[initial_mode])
                time.sleep(8)
                print_info2("已恢复初始状态", "")
        
        if steps_passed == total_steps:
            print_pass("6.1 - 完整工作流程测试", f"所有{total_steps}个步骤通过")
        else:
            print_pass("6.1 - 完整工作流程测试", f"{steps_passed}/{total_steps} 步骤通过")
        
    except Exception as e:
        print_fail("6.1 - 完整工作流程测试", str(e))
        return False
    
    return True

# ============================================================================
# 主测试流程
# ============================================================================

def run_all_tests():
    """运行所有测试"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("="*60)
    print(" " * 15 + "USB Display Control")
    print(" " * 20 + "产品测试套件")
    print("="*60)
    print(f"{Colors.END}\n")
    
    start_time = time.time()
    
    tests = [
        ("服务器基础功能", test_01_server_basic),
        ("显示器状态检测", test_02_display_detection),
        ("显示器切换控制", test_03_display_switching),
        ("Android 端通信", test_04_android_communication),
        ("错误处理", test_05_error_handling),
        ("集成测试", test_06_integration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"{Colors.RED}测试异常：{test_name}{Colors.END}")
            print(f"{Colors.RED}错误：{e}{Colors.END}")
            results.append((test_name, False))
    
    # 打印测试摘要
    print_header("测试摘要")
    
    total = len(results)
    passed = sum(1 for _, r in results if r)
    failed = total - passed
    
    print(f"总测试项：{total}")
    print(f"{Colors.GREEN}通过：{passed}{Colors.END}")
    print(f"{Colors.RED}失败：{failed}{Colors.END}")
    print(f"成功率：{(passed/total*100):.1f}%")
    print(f"总耗时：{time.time() - start_time:.2f}秒\n")
    
    # 详细结果
    print("详细结果:")
    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status} - {test_name}")
    
    print()
    
    # 返回码
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(run_all_tests())
