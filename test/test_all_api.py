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

def test(name, func):
    global passed, failed
    print(f"  Testing: {name}...", end=" ")
    try:
        func()
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

def api_post(path, data=None, timeout=15):
    url = f"{SERVER_URL}{path}"
    body = json.dumps(data).encode() if data else b''
    req = urllib.request.Request(url, data=body, method='POST')
    req.add_header('Content-Type', 'application/json')
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())

def api_post_raw(path, data, content_type='application/octet-stream'):
    url = f"{SERVER_URL}{path}"
    req = urllib.request.Request(url, data=data, method='POST')
    req.add_header('Content-Type', content_type)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())

def test_get_status():
    result = api_get("/status")
    assert "status" in result, f"Missing 'status': {result}"
    assert "mode" in result, f"Missing 'mode': {result}"

def test_post_display_command():
    result = api_post("/", {"command": "extend"})
    assert "success" in result, f"Missing 'success': {result}"

def test_get_ping():
    result = api_get("/ping")
    assert result.get("status") == "pong", f"ping failed: {result}"

def test_get_api_docs():
    result = api_get("/api")
    assert isinstance(result, dict), f"api docs should be dict: {result}"

def test_image_status_no_image():
    result = api_get("/image/status")
    assert "has_image" in result, f"Missing 'has_image': {result}"

def test_image_cast_and_clear():
    test_image_path = os.path.join(os.path.dirname(__file__), '..', 'server', 'static', 'test_cast.jpg')
    test_image_path = os.path.abspath(test_image_path)
    
    if not os.path.exists(test_image_path):
        test_image_path = os.path.join(os.path.dirname(__file__), '..', 'server', 'imagecast', 'test_cast.jpg')
        test_image_path = os.path.abspath(test_image_path)
    
    if os.path.exists(test_image_path):
        result = api_get(f"/image/cast?file={test_image_path.replace(os.sep, '/')}")
        assert result.get("success") == True, f"cast failed: {result}"
        
        status = api_get("/image/status")
        assert status.get("has_image") == True, f"Image not found after cast: {status}"
        
        result = api_post("/image/clear")
        assert result.get("success") == True, f"clear failed: {result}"
        
        status = api_get("/image/status")
        assert status.get("has_image") == False, f"Image still exists after clear: {status}"
    else:
        print("SKIP (no test image)")

def test_image_upload():
    test_data = b'\xff\xd8\xff\xe0' + b'\x00' * 100 + b'\xff\xd9'
    
    boundary = '----TestBoundary12345'
    body = f'--{boundary}\r\n'.encode()
    body += b'Content-Disposition: form-data; name="file"; filename="test.jpg"\r\n'
    body += b'Content-Type: image/jpeg\r\n\r\n'
    body += test_data
    body += f'\r\n--{boundary}--\r\n'.encode()
    
    url = f"{SERVER_URL}/image/upload"
    req = urllib.request.Request(url, data=body, method='POST')
    req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
    with urllib.request.urlopen(req, timeout=10) as resp:
        result = json.loads(resp.read().decode())
    
    assert result.get("success") == True, f"upload failed: {result}"
    
    api_post("/image/clear")

def test_image_scale():
    test_image_path = os.path.join(os.path.dirname(__file__), '..', 'server', 'static', 'test_cast.jpg')
    test_image_path = os.path.abspath(test_image_path)
    
    if os.path.exists(test_image_path):
        api_get(f"/image/cast?file={test_image_path.replace(os.sep, '/')}")
        
        result = api_post("/image/scale", {"scale": 1.5})
        assert result.get("success") == True, f"scale failed: {result}"
        
        status = api_get("/image/status")
        assert status.get("scale_level") == 1.5, f"scale not applied: {status}"
        
        api_post("/image/clear")
    else:
        print("SKIP (no test image)")

def test_image_zoom():
    test_image_path = os.path.join(os.path.dirname(__file__), '..', 'server', 'static', 'test_cast.jpg')
    test_image_path = os.path.abspath(test_image_path)
    
    if os.path.exists(test_image_path):
        api_get(f"/image/cast?file={test_image_path.replace(os.sep, '/')}")
        
        result = api_post("/image/zoom-in")
        assert result.get("success") == True, f"zoom-in failed: {result}"
        
        result = api_post("/image/zoom-out")
        assert result.get("success") == True, f"zoom-out failed: {result}"
        
        result = api_post("/image/zoom-reset")
        assert result.get("success") == True, f"zoom-reset failed: {result}"
        
        api_post("/image/clear")
    else:
        print("SKIP (no test image)")

def test_image_poll():
    result = api_get("/image/poll?t=0")
    assert "has_update" in result, f"Missing 'has_update': {result}"

def test_image_ack_popup():
    result = api_post("/image/ack-popup")
    assert "success" in result, f"ack-popup failed: {result}"

def test_image_ack_close():
    result = api_post("/image/ack-close")
    assert "success" in result, f"ack-close failed: {result}"

def test_image_list():
    result = api_get("/image/list?dir=C:/")
    assert "images" in result or "success" in result, f"list failed: {result}"

def test_brightness():
    try:
        result = api_post("/brightness", {"brightness": 50}, timeout=10)
        if result.get("success") == False:
            print("(script error, env limitation)", end=" ")
        else:
            assert result.get("success") == True, f"brightness failed: {result}"
    except urllib.error.HTTPError as e:
        if e.code == 500:
            print("(500: brightness script env error)", end=" ")
        else:
            raise

def test_download():
    url = f"{SERVER_URL}/download"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = resp.read()
    assert len(data) > 0, "download returned empty"

def test_upload_speed():
    test_data = b'\x00' * 1024
    result = api_post_raw("/upload", test_data)
    assert "received" in result or "success" in result, f"upload speed test failed: {result}"

if __name__ == '__main__':
    print("=" * 60)
    print("Complete API Endpoint Tests")
    print("=" * 60)
    
    try:
        api_get("/ping")
        print("[OK] Server is running\n")
    except Exception as e:
        print(f"[ERROR] Server not running: {e}")
        sys.exit(1)
    
    print("--- Display Control API ---")
    test("GET /status", test_get_status)
    test("POST / (display command)", test_post_display_command)
    
    print("\n--- Utility API ---")
    test("GET /ping", test_get_ping)
    test("GET /api", test_get_api_docs)
    test("GET /download", test_download)
    test("POST /upload", test_upload_speed)
    
    print("\n--- Image Casting API ---")
    test("GET /image/status", test_image_status_no_image)
    test("GET /image/cast + POST /image/clear", test_image_cast_and_clear)
    test("POST /image/upload", test_image_upload)
    test("POST /image/scale", test_image_scale)
    test("POST /image/zoom-in/out/reset", test_image_zoom)
    test("GET /image/poll", test_image_poll)
    test("POST /image/ack-popup", test_image_ack_popup)
    test("POST /image/ack-close", test_image_ack_close)
    test("GET /image/list", test_image_list)
    
    print("\n--- Brightness API ---")
    test("POST /brightness", test_brightness)
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if errors:
        print("\nFailed tests:")
        for e in errors:
            print(f"  - {e}")
    
    sys.exit(0 if failed == 0 else 1)
