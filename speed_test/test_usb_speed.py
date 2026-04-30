#!/usr/bin/env python3
import urllib.request
import json
import time

SERVER_URL = 'http://localhost:8765'

print('Testing Ping...')
start = time.time()
req = urllib.request.urlopen(f'{SERVER_URL}/ping', timeout=5)
elapsed = (time.time() - start) * 1000
print(f'Ping: {elapsed:.2f}ms')

print('\nTesting Download...')
start = time.time()
req = urllib.request.urlopen(f'{SERVER_URL}/download', timeout=30)
data = req.read()
elapsed = time.time() - start
speed = len(data) / elapsed / 1024 / 1024 * 8
print(f'Downloaded: {len(data)/1024/1024:.2f}MB, Speed: {speed:.2f}Mbps')

print('\nTesting Upload...')
data = b'x' * (10 * 1024 * 1024)  # 10MB
start = time.time()
req = urllib.request.Request(f'{SERVER_URL}/upload', data=data, headers={'Content-Type': 'application/octet-stream'}, method='POST')
response = urllib.request.urlopen(req, timeout=120)
result = json.loads(response.read().decode())
elapsed = result.get('elapsed', time.time() - start)
speed = len(data) / elapsed / 1024 / 1024 * 8
print(f'Uploaded: {result.get("received", len(data))/1024/1024:.2f}MB, Speed: {speed:.2f}Mbps')

print('\nALL TESTS OK!')