#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test API responses
"""

import http.client
import json

print("=" * 60)
print("  Testing Image Status API")
print("=" * 60)
print()

conn = http.client.HTTPConnection("localhost", 8765, timeout=10)
conn.request("GET", "/image/status")
response = conn.getresponse()
data = response.read()
conn.close()

json_str = data.decode('utf-8')
print("Response:")
print(json_str)
print()

print("Parsing:")
if '"has_image":' in json_str:
    idx = json_str.find('"has_image":')
    end = json_str.find(',', idx) if json_str.find(',', idx) > 0 else json_str.find('}')
    val = json_str[idx+12:end].strip()
    print(f"  has_image: '{val}' -> {val.lower() == 'true'}")

if '"image_name":' in json_str:
    idx = json_str.find('"image_name":')
    q1 = json_str.find('"', idx+13)
    q2 = json_str.find('"', q1+1)
    val = json_str[q1+1:q2]
    print(f"  image_name: '{val}'")

if '"scale_level":' in json_str:
    idx = json_str.find('"scale_level":')
    end = json_str.find(',', idx) if json_str.find(',', idx) > 0 else json_str.find('}')
    val = json_str[idx+14:end].strip()
    print(f"  scale_level: '{val}' -> {float(val)}")

print()
print("=" * 60)
print("  Done!")
print("=" * 60)
