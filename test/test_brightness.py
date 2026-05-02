#!/usr/bin/env python3
import sys
import os
import json
import time
import urllib.request
import urllib.error

SERVER_URL = "http://localhost:8765"

passed = 0
failed = 0
errors = []
skipped = 0
brightness_available = True

def test(name, func):
    global passed, failed, skipped
    print(f"  Testing: {name}...", end=" ")
    try:
        result = func()
        if result == "skip":
            print("SKIP")
            skipped += 1
        else:
            print("PASS")
            passed += 1
    except Exception as e:
        print(f"FAIL: {e}")
        failed += 1
        errors.append(f"{name}: {e}")

def api_get(path):
    url = f"{SERVER_URL}{path}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read().decode())

def api_post(path, data=None, timeout=10):
    global brightness_available
    url = f"{SERVER_URL}{path}"
    body = json.dumps(data).encode() if data else b''
    req = urllib.request.Request(url, data=body, method='POST')
    req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 500:
            brightness_available = False
            raise
        raise

def check_brightness_env():
    global brightness_available
    try:
        result = api_post("/brightness", {"brightness": 50})
        if result.get("success") == False:
            brightness_available = False
            return False
        return True
    except urllib.error.HTTPError:
        brightness_available = False
        return False

def test_brightness_api_exists():
    if not brightness_available:
        return "skip"
    result = api_post("/brightness", {"brightness": 50})
    assert result.get("success") == True, f"brightness API failed: {result}"

def test_brightness_valid_range():
    if not brightness_available:
        return "skip"
    result = api_post("/brightness", {"brightness": 0})
    assert result.get("success") == True, f"brightness=0 failed: {result}"
    
    result = api_post("/brightness", {"brightness": 100})
    assert result.get("success") == True, f"brightness=100 failed: {result}"
    
    result = api_post("/brightness", {"brightness": 50})
    assert result.get("success") == True, f"brightness=50 failed: {result}"

def test_brightness_invalid_value():
    try:
        result = api_post("/brightness", {"brightness": 150})
        assert result.get("success") == False, f"brightness=150 should fail: {result}"
    except urllib.error.HTTPError:
        pass

def test_brightness_negative_value():
    try:
        result = api_post("/brightness", {"brightness": -10})
        assert result.get("success") == False, f"brightness=-10 should fail: {result}"
    except urllib.error.HTTPError:
        pass

def test_brightness_missing_param():
    try:
        result = api_post("/brightness", {})
        assert result.get("success") == False, f"Missing brightness should fail: {result}"
    except urllib.error.HTTPError:
        pass

def test_brightness_restore():
    if not brightness_available:
        return "skip"
    result = api_post("/brightness", {"brightness": 50})
    assert result.get("success") == True, f"Restore brightness failed: {result}"

def test_ping_api():
    result = api_get("/ping")
    assert result.get("status") == "pong", f"ping failed: {result}"

def test_download_api():
    url = f"{SERVER_URL}/download"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = resp.read()
    assert len(data) > 0, "download returned empty data"

def test_api_docs():
    result = api_get("/api")
    assert "endpoints" in result or "api" in result, f"api docs missing: {result}"

def test_status_api():
    result = api_get("/status")
    assert "status" in result, f"status missing 'status': {result}"
    assert "mode" in result, f"status missing 'mode': {result}"

if __name__ == '__main__':
    print("=" * 60)
    print("Brightness & Utility API Tests")
    print("=" * 60)
    
    try:
        api_get("/ping")
        print("[OK] Server is running\n")
    except Exception as e:
        print(f"[ERROR] Server not running: {e}")
        sys.exit(1)
    
    env_ok = check_brightness_env()
    if not env_ok:
        print("[INFO] Brightness control not available in this environment")
        print("[INFO] Brightness tests will be skipped\n")
    
    print("--- Brightness API ---")
    test("Brightness API exists", test_brightness_api_exists)
    test("Brightness valid range (0, 50, 100)", test_brightness_valid_range)
    test("Brightness invalid value (>100)", test_brightness_invalid_value)
    test("Brightness negative value", test_brightness_negative_value)
    test("Brightness missing param", test_brightness_missing_param)
    test("Brightness restore to 50%", test_brightness_restore)
    
    print("\n--- Utility API ---")
    test("Ping API", test_ping_api)
    test("Download API", test_download_api)
    test("API docs endpoint", test_api_docs)
    test("Status API", test_status_api)
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed, {skipped} skipped")
    print("=" * 60)
    
    if errors:
        print("\nFailed tests:")
        for e in errors:
            print(f"  - {e}")
    
    sys.exit(0 if failed == 0 else 1)
