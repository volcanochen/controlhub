#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Image Casting End-to-End Demo
"""

import sys
import os
import time
import http.client
import json

SERVER_HOST = "localhost"
SERVER_PORT = 8765


def http_request(method, path, body=None, headers=None):
    """Send HTTP request"""
    conn = None
    try:
        conn = http.client.HTTPConnection(SERVER_HOST, SERVER_PORT, timeout=30)
        
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


def create_test_image():
    """Create a simple test image"""
    try:
        from PIL import Image, ImageDraw
        img = Image.new('RGB', (400, 300), color='red')
        draw = ImageDraw.Draw(img)
        
        try:
            draw.text((100, 120), "Image Casting Demo", fill='white')
            draw.text((120, 150), "From PC to Phone", fill='white')
            draw.text((140, 180), time.strftime("%Y-%m-%d %H:%M:%S"), fill='white')
        except:
            pass
        
        import io
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        return buf.getvalue(), 'demo.png'
    except ImportError:
        return create_simple_png(), 'demo.png'


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


def print_header(text):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_step(text):
    print(f"\n> {text}")


def check_server():
    print_step("Checking server connection...")
    try:
        status, result = http_request("GET", "/")
        if status == 200 or status > 0:
            print("  [OK] Server is running")
            return True
        else:
            print(f"  [ERROR] Server connection failed: {result.get('error', 'Unknown')}")
            return False
    except Exception as e:
        print(f"  [ERROR] Server connection failed: {e}")
        return False


def upload_image(image_data, filename):
    print_step(f"Uploading image: {filename} ({len(image_data)} bytes)")
    try:
        headers = {
            'Content-Type': 'application/octet-stream',
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
        status, result = http_request("POST", "/image/upload", image_data, headers)
        
        if status == 200:
            print(f"  [OK] Upload successful: {result}")
            return True
        else:
            print(f"  [ERROR] Upload failed: {status}")
            return False
    except Exception as e:
        print(f"  [ERROR] Upload exception: {e}")
        return False


def get_image_status():
    print_step("Getting image status...")
    try:
        status, result = http_request("GET", "/image/status")
        if status == 200:
            print(f"  [OK] Status: {result}")
            return result
    except Exception as e:
        print(f"  [ERROR] Failed to get status: {e}")
    return None


def run_demo():
    print_header("Image Casting - End-to-End Demo")
    print("\nDemo steps:")
    print("  1. Check server connection")
    print("  2. Create test image")
    print("  3. Upload image")
    print("  4. Verify status")
    print("  5. Test zoom controls")
    
    if not check_server():
        print("\nPlease start server first:")
        print("   cd server")
        print("   python usb_display_control.py")
        return False
    
    time.sleep(1)
    
    print_step("Creating test image...")
    image_data, filename = create_test_image()
    print(f"  [OK] Test image created: {filename}")
    
    time.sleep(1)
    
    if not upload_image(image_data, filename):
        return False
    
    time.sleep(1)
    
    status = get_image_status()
    if not status or not status.get('has_image'):
        print("  [ERROR] Status verification failed")
        return False
    
    time.sleep(1)
    
    print_header("Testing Zoom Controls")
    
    print_step("Zoom In...")
    status, result = http_request("POST", "/image/zoom-in")
    if status == 200:
        print(f"  [OK] {result}")
    time.sleep(0.5)
    
    print_step("Zoom Out...")
    status, result = http_request("POST", "/image/zoom-out")
    if status == 200:
        print(f"  [OK] {result}")
    time.sleep(0.5)
    
    print_step("Reset Zoom...")
    status, result = http_request("POST", "/image/zoom-reset")
    if status == 200:
        print(f"  [OK] {result}")
    time.sleep(0.5)
    
    get_image_status()
    
    print("\n" + "=" * 60)
    print("  Demo Complete!")
    print("=" * 60)
    print("\nOn phone:")
    print("   1. Open APP")
    print("   2. Click the image button")
    print("   3. View and zoom the image")
    print("\nOn PC:")
    print("   cd server/imagecast")
    print("   python image_uploader.py")
    
    return True


if __name__ == '__main__':
    success = run_demo()
    sys.exit(0 if success else 1)
