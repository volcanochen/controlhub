#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple image casting demo
"""

import sys
import os
import time
import http.client
import json


def create_simple_png():
    """Create a minimal PNG image"""
    return bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
        0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
        0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,
        0x54, 0x08, 0xD7, 0x63, 0xF8, 0xFF, 0xFF, 0x3F,
        0x00, 0x05, 0xFE, 0x02, 0xFE, 0x8E, 0x8E, 0x5C,
        0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44,
        0xAE, 0x42, 0x60, 0x82
    ])


def http_request(method, path, body=None, headers=None):
    """Send HTTP request"""
    conn = None
    try:
        conn = http.client.HTTPConnection("localhost", 8765, timeout=30)
        
        if headers is None:
            headers = {}
        
        if body and isinstance(body, dict):
            body = json.dumps(body).encode('utf-8')
            headers['Content-Type'] = 'application/json'
        
        conn.request(method, path, body, headers)
        response = conn.getresponse()
        data = response.read()
        
        try:
            result = json.loads(data.decode('utf-8'))
        except:
            result = {'raw': data}
        
        return response.status, result
        
    except Exception as e:
        return -1, {'error': str(e)}
    finally:
        if conn:
            conn.close()


print("=" * 60)
print("  Image Casting Demo")
print("=" * 60)

print("\n[1] Checking server...")
status, result = http_request("GET", "/")
if status > 0:
    print("    OK: Server is running")
else:
    print("    ERROR: Server not running")
    print("    Please start server first:")
    print("      cd server")
    print("      python usb_display_control.py")
    sys.exit(1)

print("\n[2] Creating test image...")
test_image = create_simple_png()
print(f"    OK: Created test image ({len(test_image)} bytes)")

print("\n[3] Uploading image...")
headers = {
    'Content-Type': 'application/octet-stream',
    'Content-Disposition': 'attachment; filename="test.png"'
}
status, result = http_request("POST", "/image/upload", test_image, headers)
if status == 200:
    print(f"    OK: Upload successful - {result}")
else:
    print(f"    ERROR: Upload failed - {status}")

print("\n[4] Checking image status...")
status, result = http_request("GET", "/image/status")
if status == 200:
    print(f"    OK: Status - {result}")

print("\n[5] Testing zoom controls...")

print("    - Zoom In...")
status, result = http_request("POST", "/image/zoom-in")
if status == 200:
    print(f"      OK: {result}")

time.sleep(0.5)

print("    - Zoom Out...")
status, result = http_request("POST", "/image/zoom-out")
if status == 200:
    print(f"      OK: {result}")

time.sleep(0.5)

print("    - Reset Zoom...")
status, result = http_request("POST", "/image/zoom-reset")
if status == 200:
    print(f"      OK: {result}")

print("\n[6] Final status check...")
status, result = http_request("GET", "/image/status")
if status == 200:
    print(f"    OK: Final status - {result}")

print("\n" + "=" * 60)
print("  Demo Complete!")
print("=" * 60)
print("\nNext steps:")
print("  1. On Android phone: Open the app")
print("  2. Click the image button (top right)")
print("  3. View and zoom the image")
print("\nTo use GUI uploader:")
print("  cd server/imagecast")
print("  python image_uploader.py")
