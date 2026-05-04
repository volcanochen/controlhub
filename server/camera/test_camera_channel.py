#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Camera Channel Test Script
Test USB and WiFi channels for camera communication
"""

import subprocess
import requests
import time
import json
import sys
from pathlib import Path

CAMERA_PORT = 8766
CONFIG_FILE = Path(__file__).parent / "config.json"

ADB_PATH = None
if sys.platform == 'win32':
    local_app_data = os.environ.get('LOCALAPPDATA', '')
    if local_app_data:
        adb_path = Path(local_app_data) / "Android" / "Sdk" / "platform-tools" / "adb.exe"
        if adb_path.exists():
            ADB_PATH = str(adb_path)
if ADB_PATH is None:
    ADB_PATH = "adb"


def run_adb_command(args, timeout=10):
    try:
        result = subprocess.run(
            [ADB_PATH] + args,
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Timeout"
    except FileNotFoundError:
        return -1, "", "ADB not found"
    except Exception as e:
        return -1, "", str(e)


def check_adb_devices():
    print("\n=== Checking ADB Devices ===")
    returncode, stdout, stderr = run_adb_command(['devices'])
    
    if returncode != 0:
        print(f"Error: {stderr}")
        return False
    
    lines = stdout.strip().split('\n')
    devices = [l for l in lines[1:] if l.strip() and 'device' in l and 'List' not in l]
    
    if devices:
        print(f"Found {len(devices)} device(s):")
        for d in devices:
            print(f"  - {d}")
        return True
    else:
        print("No devices found")
        return False


def setup_adb_forward(port=CAMERA_PORT):
    print(f"\n=== Setting up ADB Forward (Port {port}) ===")
    returncode, stdout, stderr = run_adb_command(['forward', f'tcp:{port}', f'tcp:{port}'])
    
    if returncode == 0:
        print(f"ADB forward set: tcp:{port} -> tcp:{port}")
        return True
    else:
        print(f"Failed to set ADB forward: {stderr}")
        return False


def remove_adb_forward(port=CAMERA_PORT):
    print(f"\n=== Removing ADB Forward (Port {port}) ===")
    returncode, stdout, stderr = run_adb_command(['forward', '--remove', f'tcp:{port}'])
    
    if returncode == 0:
        print(f"ADB forward removed for port {port}")
        return True
    else:
        print(f"Failed to remove ADB forward: {stderr}")
        return False


def test_camera_api(base_url, endpoint="/camera/status"):
    print(f"\n=== Testing Camera API: {endpoint} ===")
    url = f"{base_url}{endpoint}"
    print(f"URL: {url}")
    
    try:
        if "open" in endpoint or "close" in endpoint or "start" in endpoint or "stop" in endpoint:
            resp = requests.post(url, timeout=5)
        else:
            resp = requests.get(url, timeout=5)
        
        print(f"Status: {resp.status_code}")
        try:
            data = resp.json()
            print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
        except:
            print(f"Response: {resp.text[:200]}")
        return resp.status_code == 200
    except requests.exceptions.ConnectionError as e:
        print(f"Connection failed: {e}")
        return False
    except requests.exceptions.Timeout:
        print("Request timeout")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_stream(base_url, duration=3):
    print(f"\n=== Testing MJPEG Stream ({duration}s) ===")
    url = f"{base_url}/camera/stream"
    print(f"URL: {url}")
    
    try:
        resp = requests.get(url, stream=True, timeout=duration + 5)
        print(f"Status: {resp.status_code}")
        print(f"Content-Type: {resp.headers.get('Content-Type', 'N/A')}")
        
        start_time = time.time()
        frame_count = 0
        content = b""
        
        for chunk in resp.iter_content(chunk_size=4096):
            content += chunk
            if b'--ControlHubFrame' in content:
                frame_count += content.count(b'--ControlHubFrame')
                content = content[content.rfind(b'--ControlHubFrame'):]
            
            if time.time() - start_time > duration:
                break
        
        print(f"Received {frame_count} frames in {duration}s")
        print(f"Average FPS: {frame_count / duration:.1f}")
        return frame_count > 0
        
    except requests.exceptions.ConnectionError as e:
        print(f"Connection failed: {e}")
        return False
    except requests.exceptions.Timeout:
        print("Request timeout")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False


def load_config():
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {"host": "192.168.50.132", "port": 8766, "channel": "auto"}


def save_config(config):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        return True
    except:
        return False


def run_all_tests():
    print("=" * 60)
    print("  Camera Channel Test Suite")
    print("=" * 60)
    
    config = load_config()
    results = {
        "usb_available": False,
        "wifi_available": False,
        "usb_tests": {},
        "wifi_tests": {}
    }
    
    usb_connected = check_adb_devices()
    results["usb_available"] = usb_connected
    
    if usb_connected:
        print("\n" + "=" * 60)
        print("  Testing USB Channel")
        print("=" * 60)
        
        if setup_adb_forward():
            usb_url = f"http://localhost:{CAMERA_PORT}"
            
            results["usb_tests"]["status"] = test_camera_api(usb_url, "/camera/status")
            results["usb_tests"]["open"] = test_camera_api(usb_url, "/camera/open")
            time.sleep(1)
            results["usb_tests"]["stream"] = test_stream(usb_url, duration=3)
            results["usb_tests"]["close"] = test_camera_api(usb_url, "/camera/close")
            
            remove_adb_forward()
    
    print("\n" + "=" * 60)
    print("  Testing WiFi Channel")
    print("=" * 60)
    
    wifi_host = config.get("host", "192.168.50.132")
    wifi_url = f"http://{wifi_host}:{CAMERA_PORT}"
    print(f"WiFi URL: {wifi_url}")
    
    results["wifi_tests"]["status"] = test_camera_api(wifi_url, "/camera/status")
    if results["wifi_tests"]["status"]:
        results["wifi_available"] = True
        results["wifi_tests"]["open"] = test_camera_api(wifi_url, "/camera/open")
        time.sleep(1)
        results["wifi_tests"]["stream"] = test_stream(wifi_url, duration=3)
        results["wifi_tests"]["close"] = test_camera_api(wifi_url, "/camera/close")
    
    print("\n" + "=" * 60)
    print("  Test Summary")
    print("=" * 60)
    
    print(f"\nUSB Available: {'Yes' if results['usb_available'] else 'No'}")
    if results["usb_available"]:
        for test, passed in results["usb_tests"].items():
            status = "PASS" if passed else "FAIL"
            print(f"  USB {test}: {status}")
    
    print(f"\nWiFi Available: {'Yes' if results['wifi_available'] else 'No'}")
    if results["wifi_available"]:
        for test, passed in results["wifi_tests"].items():
            status = "PASS" if passed else "FAIL"
            print(f"  WiFi {test}: {status}")
    
    print("\n" + "=" * 60)
    
    return results


def test_barcode(base_url):
    print(f"\n=== Testing Barcode Scanning ===")
    
    print("Opening camera...")
    if not test_camera_api(base_url, "/camera/open"):
        print("Failed to open camera")
        return False
    
    time.sleep(1)
    
    print("Starting barcode scanner...")
    try:
        resp = requests.post(f"{base_url}/barcode/start", timeout=5)
        if resp.status_code != 200:
            print("Failed to start barcode scanner")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    print("Waiting for barcode (30s timeout)...")
    print("Point camera at a QR code...")
    
    for i in range(60):
        try:
            resp = requests.get(f"{base_url}/barcode/result", timeout=2)
            data = resp.json()
            
            if data.get("status") == "ok" and data.get("value"):
                print(f"\nBarcode detected!")
                print(f"  Format: {data.get('format', 'Unknown')}")
                print(f"  Value: {data.get('value')}")
                
                requests.post(f"{base_url}/barcode/stop", timeout=2)
                return True
        except:
            pass
        
        print(".", end="", flush=True)
        time.sleep(0.5)
    
    print("\nNo barcode detected within timeout")
    requests.post(f"{base_url}/barcode/stop", timeout=2)
    return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Camera Channel Test")
    parser.add_argument("--usb", action="store_true", help="Test USB channel only")
    parser.add_argument("--wifi", action="store_true", help="Test WiFi channel only")
    parser.add_argument("--barcode", action="store_true", help="Test barcode scanning")
    parser.add_argument("--host", type=str, help="WiFi host IP")
    parser.add_argument("--port", type=int, default=8766, help="Camera port")
    
    args = parser.parse_args()
    
    if args.host:
        config = load_config()
        config["host"] = args.host
        save_config(config)
        print(f"WiFi host set to: {args.host}")
    
    CAMERA_PORT = args.port
    
    if args.barcode:
        config = load_config()
        if check_adb_devices():
            setup_adb_forward()
            test_barcode(f"http://localhost:{CAMERA_PORT}")
            remove_adb_forward()
        else:
            wifi_url = f"http://{config.get('host', '192.168.50.132')}:{CAMERA_PORT}"
            test_barcode(wifi_url)
    elif args.usb:
        if check_adb_devices():
            setup_adb_forward()
            usb_url = f"http://localhost:{CAMERA_PORT}"
            test_camera_api(usb_url, "/camera/status")
            test_stream(usb_url)
            remove_adb_forward()
    elif args.wifi:
        config = load_config()
        wifi_url = f"http://{config.get('host', '192.168.50.132')}:{CAMERA_PORT}"
        test_camera_api(wifi_url, "/camera/status")
        test_stream(wifi_url)
    else:
        run_all_tests()
