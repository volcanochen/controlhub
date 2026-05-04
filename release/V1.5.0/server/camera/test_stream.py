#!/usr/bin/env python3
import requests
import time

url = 'http://192.168.50.132:8766/camera/stream'
try:
    print(f'Connecting to {url}...')
    r = requests.get(url, stream=True, timeout=15)
    print(f'Status: {r.status_code}')
    print(f'Content-Type: {r.headers.get("Content-Type")}')
    print(f'Reading stream...')
    
    data = b''
    count = 0
    start_time = time.time()
    
    for chunk in r.iter_content(chunk_size=4096):
        data += chunk
        
        while True:
            start = data.find(b'\xff\xd8')
            end = data.find(b'\xff\xd9')
            
            if start != -1 and end != -1 and end > start:
                jpg_data = data[start:end+2]
                data = data[end+2:]
                count += 1
                elapsed = time.time() - start_time
                fps = count / elapsed if elapsed > 0 else 0
                print(f'Frame {count}: {len(jpg_data)} bytes, FPS: {fps:.1f}')
                
                if count >= 10:
                    print('Test complete!')
                    break
            else:
                break
        
        if count >= 10:
            break
            
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
