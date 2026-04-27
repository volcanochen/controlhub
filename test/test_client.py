#!/usr/bin/env python3
"""
Test script to simulate Android app sending display switch command
"""
import urllib.request
import json

url = "http://localhost:8765/"
data = {"command": "extend"}

try:
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    
    with urllib.request.urlopen(req, timeout=5) as response:
        result = json.loads(response.read().decode('utf-8'))
        print(f"Response: {result}")
        
except Exception as e:
    print(f"Error: {e}")
