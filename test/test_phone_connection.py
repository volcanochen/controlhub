#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test connection from phone to PC server
"""

import urllib.request
import json
import time

# Use your PC's IP address
SERVER_URL = "http://192.168.50.111:8766"

print("Testing connection to server...")
print(f"Server: {SERVER_URL}")
print()

try:
    # Test 1: Ping
    print("1. Testing Ping...")
    start = time.time()
    req = urllib.request.urlopen(f"{SERVER_URL}/ping", timeout=5)
    elapsed = (time.time() - start) * 1000
    print(f"   [OK] Ping: {elapsed:.2f} ms")
    print()
    
    # Test 2: Download
    print("2. Testing Download (10MB)...")
    start = time.time()
    req = urllib.request.urlopen(f"{SERVER_URL}/download", timeout=30)
    data = req.read()
    elapsed = time.time() - start
    speed = len(data) / elapsed / 1024 / 1024 * 8
    print(f"   [OK] Downloaded {len(data) / 1024 / 1024:.2f} MB in {elapsed:.2f}s")
    print(f"   [OK] Speed: {speed:.2f} Mbps ({speed/8:.2f} MB/s)")
    print()
    
    # Test 3: Upload
    print("3. Testing Upload (10MB)...")
    data = b'x' * (10 * 1024 * 1024)
    start = time.time()
    req = urllib.request.Request(
        f"{SERVER_URL}/upload",
        data=data,
        headers={'Content-Type': 'application/octet-stream'},
        method='POST'
    )
    req.add_header('Content-Length', str(len(data)))
    response = urllib.request.urlopen(req, timeout=120)
    result = json.loads(response.read().decode())
    elapsed = result.get('elapsed', time.time() - start)
    speed = len(data) / elapsed / 1024 / 1024 * 8
    print(f"   [OK] Uploaded {result.get('received', len(data)) / 1024 / 1024:.2f} MB in {elapsed:.2f}s")
    print(f"   [OK] Speed: {speed:.2f} Mbps ({speed/8:.2f} MB/s)")
    print()
    
    print("=" * 50)
    print("ALL TESTS PASSED!")
    print("=" * 50)
    
except Exception as e:
    print(f"ERROR: {e}")
    print()
    print("Possible issues:")
    print("1. Server is not running")
    print("2. Firewall is blocking port 8766")
    print("3. IP address is incorrect")
    print("4. Network is not reachable")
