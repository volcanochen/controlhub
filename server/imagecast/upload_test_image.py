#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Upload a real test image
"""

import os
import sys
import http.client
import json
from io import BytesIO

SERVER_HOST = "localhost"
SERVER_PORT = 8765

def create_real_test_image():
    """Create a real test image"""
    try:
        from PIL import Image, ImageDraw
        img = Image.new('RGB', (800, 600), color='blue')
        draw = ImageDraw.Draw(img)
        
        try:
            draw.rectangle([100, 100, 700, 500], fill='white', outline='black', width=3)
            draw.text((200, 200), "Image Casting Demo!", fill='black')
            draw.text((200, 280), "From PC to Phone!", fill='black')
            draw.text((200, 360), "It Works!", fill='red')
        except:
            draw.rectangle([100, 100, 700, 500], fill='white')
            draw.ellipse([300, 200, 500, 400], fill='red')
        
        buf = BytesIO()
        img.save(buf, format='PNG')
        return buf.getvalue(), "test_image.png"
    except ImportError:
        return create_colored_png(), "test_image.png"

def create_colored_png():
    """Create a simple colored PNG"""
    return bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
        0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x01, 0x80,
        0x08, 0x02, 0x00, 0x00, 0x00, 0xBA, 0x8C, 0x7C,
        0xD9, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,
        0x54, 0x08, 0xD7, 0x63, 0xF8, 0xFF, 0xFF, 0x3F,
        0x00, 0x05, 0xFE, 0x02, 0xFE, 0x8E, 0x8E, 0x5C,
        0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44,
        0xAE, 0x42, 0x60, 0x82
    ])

def http_request(method, path, body=None, headers=None):
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

def main():
    print("=" * 60)
    print("  Upload Real Test Image")
    print("=" * 60)
    print()
    
    print("[1] Creating test image...")
    img_data, img_name = create_real_test_image()
    print(f"  [OK] Created: {img_name} ({len(img_data)} bytes)")
    
    print()
    print("[2] Uploading to server...")
    headers = {
        'Content-Type': 'application/octet-stream',
        'Content-Disposition': f'attachment; filename="{img_name}"'
    }
    status, result = http_request("POST", "/image/upload", img_data, headers)
    
    if status == 200:
        print(f"  [OK] Upload successful: {result}")
    else:
        print(f"  [ERROR] Upload failed: {status}")
        print(f"  {result}")
        return 1
    
    print()
    print("[3] Checking image status...")
    status, result = http_request("GET", "/image/status")
    if status == 200:
        print(f"  [OK] Status: {result}")
    
    print()
    print("=" * 60)
    print("  Done! Now try clicking the image button in the APP!")
    print("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())
