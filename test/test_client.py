#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Client-side network speed test
Tests connection to the speed test server
"""

import time
import urllib.request
import json
import statistics

SERVER_URL = "http://127.0.0.1:8766"

def test_ping(count=5):
    """Test latency"""
    print(f"\nTesting Ping ({count} times)...")
    latencies = []
    
    for i in range(count):
        try:
            start = time.time()
            req = urllib.request.urlopen(f"{SERVER_URL}/ping", timeout=10)
            elapsed = (time.time() - start) * 1000  # ms
            latencies.append(elapsed)
            print(f"  Ping {i+1}: {elapsed:.2f} ms")
            time.sleep(0.3)
        except Exception as e:
            print(f"  Ping {i+1}: FAILED - {e}")
    
    if latencies:
        avg = statistics.mean(latencies)
        min_lat = min(latencies)
        max_lat = max(latencies)
        jitter = statistics.stdev(latencies) if len(latencies) > 1 else 0
        
        print(f"\n[RESULTS] Ping Test:")
        print(f"  Average: {avg:.2f} ms")
        print(f"  Min: {min_lat:.2f} ms")
        print(f"  Max: {max_lat:.2f} ms")
        print(f"  Jitter: {jitter:.2f} ms")
        return avg
    return None

def test_download(duration=5):
    """Test download speed"""
    print(f"\nTesting Download Speed ({duration} seconds)...")
    
    start_time = time.time()
    total_bytes = 0
    
    try:
        while time.time() - start_time < duration:
            req = urllib.request.urlopen(f"{SERVER_URL}/download", timeout=30)
            data = req.read()
            total_bytes += len(data)
    except Exception as e:
        pass
    
    elapsed = time.time() - start_time
    speed_bps = total_bytes / elapsed if elapsed > 0 else 0
    speed_mbps = (speed_bps * 8) / 1024 / 1024
    speed_mbs = speed_bps / 1024 / 1024
    
    print(f"\n[RESULTS] Download Speed:")
    print(f"  Data: {total_bytes / 1024 / 1024:.2f} MB")
    print(f"  Time: {elapsed:.2f} seconds")
    print(f"  Speed: {speed_mbps:.2f} Mbps ({speed_mbs:.2f} MB/s)")
    
    return speed_mbps

def test_upload(data_size_mb=10):
    """Test upload speed"""
    print(f"\nTesting Upload Speed ({data_size_mb} MB)...")
    
    data = b'x' * (data_size_mb * 1024 * 1024)
    start_time = time.time()
    
    try:
        req = urllib.request.Request(
            f"{SERVER_URL}/upload",
            data=data,
            headers={'Content-Type': 'application/octet-stream'},
            method='POST'
        )
        req.add_header('Content-Length', str(len(data)))
        
        response = urllib.request.urlopen(req, timeout=120)
        result = json.loads(response.read().decode())
        
        elapsed = result.get('elapsed', time.time() - start_time)
        received = result.get('received', len(data))
        speed_bps = received / elapsed if elapsed > 0 else 0
        speed_mbps = (speed_bps * 8) / 1024 / 1024
        speed_mbs = speed_bps / 1024 / 1024
        
        print(f"\n[RESULTS] Upload Speed:")
        print(f"  Data: {received / 1024 / 1024:.2f} MB")
        print(f"  Time: {elapsed:.2f} seconds")
        print(f"  Speed: {speed_mbps:.2f} Mbps ({speed_mbs:.2f} MB/s)")
        
        return speed_mbps
    except Exception as e:
        print(f"  Upload FAILED: {e}")
        return None

def main():
    print("=" * 60)
    print("Network Speed Test Client")
    print("=" * 60)
    print(f"Testing connection to: {SERVER_URL}")
    
    # Check if server is reachable
    try:
        urllib.request.urlopen(f"{SERVER_URL}/ping", timeout=2)
        print("[OK] Server is reachable")
    except Exception as e:
        print(f"[ERROR] Cannot connect to server: {e}")
        print("Please make sure the server is running:")
        print("  python simple_speed_test.py")
        return
    
    # Run tests
    ping_result = test_ping(5)
    download_speed = test_download(5)
    upload_speed = test_upload(10)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    if ping_result:
        print(f"Ping: {ping_result:.2f} ms")
    if download_speed:
        print(f"Download: {download_speed:.2f} Mbps ({download_speed/8:.2f} MB/s)")
    if upload_speed:
        print(f"Upload: {upload_speed:.2f} Mbps ({upload_speed/8:.2f} MB/s)")
    print("=" * 60)
    
    # Performance rating
    print("\nPERFORMANCE RATING:")
    if ping_result and ping_result < 10:
        print("  Ping: EXCELLENT")
    elif ping_result and ping_result < 50:
        print("  Ping: GOOD")
    else:
        print("  Ping: FAIR")
    
    if download_speed and download_speed > 50:
        print("  Bandwidth: EXCELLENT")
    elif download_speed and download_speed > 20:
        print("  Bandwidth: GOOD")
    else:
        print("  Bandwidth: FAIR")
    
    print("=" * 60)

if __name__ == '__main__':
    main()
