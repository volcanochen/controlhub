#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test New Image Casting APIs
"""

import http.client
import json

def api_get(path):
    conn = http.client.HTTPConnection("localhost", 8765, timeout=5)
    conn.request("GET", path)
    resp = conn.getresponse()
    data = resp.read()
    conn.close()
    return resp.status, data

def api_post(path, body=None, headers=None):
    conn = http.client.HTTPConnection("localhost", 8765, timeout=5)
    conn.request("POST", path, body, headers or {})
    resp = conn.getresponse()
    data = resp.read()
    conn.close()
    return resp.status, data

print("=" * 60)
print("  Testing New Image Casting APIs")
print("=" * 60)

# 1. API docs
print("\n[1] GET /api")
status, data = api_get("/api")
print(f"  Status: {status}")
if status == 200:
    doc = json.loads(data)
    print(f"  Service: {doc.get('service', 'N/A')}")
    print(f"  Endpoints: {len(doc.get('endpoints', {}))}")
    for name, ep in doc.get('endpoints', {}).items():
        print(f"    {ep['method']:4s} {ep['path']}")
else:
    print(f"  Body: {data[:200]}")

# 2. List images in current directory
print("\n[2] GET /image/list?dir=.")
status, data = api_get("/image/list?dir=.")
print(f"  Status: {status}")
if status == 200:
    result = json.loads(data)
    print(f"  Found {result['count']} images")
    for f in result['files'][:5]:
        print(f"    {f['name']} ({f['size_mb']} MB)")
else:
    print(f"  Body: {data[:200]}")

# 3. Cast image by file path (GET)
print("\n[3] GET /image/cast?file=<test_image>")
from PIL import Image
from io import BytesIO
img = Image.new('RGB', (400, 300), color=(255, 100, 50))
buf = BytesIO()
img.save(buf, format='JPEG')
test_path = "c:/VOLCANO/myws/andr/server/imagecast/test_cast_api.jpg"
with open(test_path, 'wb') as f:
    f.write(buf.getvalue())

import urllib.parse
encoded_path = urllib.parse.quote(test_path)
status, data = api_get(f"/image/cast?file={encoded_path}")
print(f"  Status: {status}")
if status == 200:
    result = json.loads(data)
    print(f"  Success: {result['success']}")
    print(f"  Filename: {result['filename']}")
    print(f"  Size: {result['size']} bytes")
else:
    print(f"  Body: {data[:200]}")

# 4. Cast image by file path (POST JSON)
print("\n[4] POST /image/cast (JSON)")
body = json.dumps({"file": test_path}).encode('utf-8')
headers = {'Content-Type': 'application/json'}
status, data = api_post("/image/cast", body, headers)
print(f"  Status: {status}")
if status == 200:
    result = json.loads(data)
    print(f"  Success: {result['success']}")
    print(f"  Filename: {result['filename']}")
else:
    print(f"  Body: {data[:200]}")

# 5. Check status
print("\n[5] GET /image/status")
status, data = api_get("/image/status")
if status == 200:
    result = json.loads(data)
    print(f"  Has image: {result.get('has_image')}")
    print(f"  Image name: {result.get('image_name')}")
    print(f"  Scale: {result.get('scale_level')}")

print("\n" + "=" * 60)
print("  All tests done!")
print("=" * 60)
