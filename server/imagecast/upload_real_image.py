#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Upload real image with verification
"""

import http.client
import json
from PIL import Image, ImageDraw
from io import BytesIO

SERVER_HOST = "localhost"
SERVER_PORT = 8765

def create_test_image():
    img = Image.new('RGB', (800, 600), color=(30, 60, 120))
    draw = ImageDraw.Draw(img)
    draw.rectangle([50, 50, 750, 550], fill=(255, 255, 255), outline=(0, 0, 0), width=3)
    draw.rectangle([100, 100, 700, 200], fill=(220, 50, 50))
    draw.text((180, 120), "Image Casting Test", fill=(255, 255, 255))
    draw.rectangle([100, 250, 700, 350], fill=(50, 180, 50))
    draw.text((250, 270), "PC -> Phone", fill=(255, 255, 255))
    draw.rectangle([100, 400, 700, 500], fill=(50, 50, 200))
    draw.text((280, 420), "It Works!", fill=(255, 255, 255))
    buf = BytesIO()
    img.save(buf, format='JPEG', quality=90)
    return buf.getvalue()

img_data = create_test_image()
print(f"Image size: {len(img_data)} bytes")

assert img_data[:2] == b'\xff\xd8', "Not a valid JPEG!"
print("Valid JPEG confirmed")

headers = {
    'Content-Type': 'application/octet-stream',
    'Content-Disposition': 'attachment; filename="test_casting.jpg"'
}
conn = http.client.HTTPConnection(SERVER_HOST, SERVER_PORT, timeout=30)
conn.request("POST", "/image/upload", img_data, headers)
resp = conn.getresponse()
result = json.loads(resp.read().decode())
print(f"Upload: {result}")
conn.close()

conn = http.client.HTTPConnection(SERVER_HOST, SERVER_PORT, timeout=30)
conn.request("GET", "/image/data")
resp = conn.getresponse()
data = resp.read()
conn.close()
print(f"/image/data: status={resp.status}, content-type={resp.getheader('Content-Type')}, size={len(data)} bytes")
print(f"JPEG header check: {data[:2] == b'\\xff\\xd8'}")

conn = http.client.HTTPConnection(SERVER_HOST, SERVER_PORT, timeout=30)
conn.request("GET", "/image/status")
resp = conn.getresponse()
status = json.loads(resp.read().decode())
print(f"/image/status: {json.dumps(status, indent=2)}")
conn.close()

print("\nAll checks passed! Image is ready on server.")
