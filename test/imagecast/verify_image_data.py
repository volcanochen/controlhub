#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verify image data from server
"""

import http.client

conn = http.client.HTTPConnection("localhost", 8765, timeout=30)
conn.request("GET", "/image/data")
resp = conn.getresponse()
data = resp.read()
conn.close()

print(f"Status: {resp.status}")
print(f"Content-Type: {resp.getheader('Content-Type')}")
print(f"Content-Length: {resp.getheader('Content-Length')}")
print(f"Data size: {len(data)} bytes")
print(f"First 20 bytes (hex): {data[:20].hex()}")
print(f"First 20 bytes (raw): {data[:20]}")
print(f"Is JPEG: {data[:2] == b'\\xff\\xd8'}")

from PIL import Image
from io import BytesIO
try:
    img = Image.open(BytesIO(data))
    print(f"Image format: {img.format}")
    print(f"Image size: {img.size}")
    print("Image is valid!")
except Exception as e:
    print(f"Image decode error: {e}")
