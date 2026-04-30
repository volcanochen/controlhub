#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Network Speed Test
Quick test for network speed between PC and Android
"""

import time
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

TEST_PORT = 8766

class SpeedTestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/ping':
            start = time.time()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {'status': 'pong', 'time': start}
            self.wfile.write(json.dumps(response).encode())
            
        elif self.path == '/download':
            # Send 10MB data
            data_size = 10 * 1024 * 1024
            data = b'x' * data_size
            self.send_response(200)
            self.send_header('Content-Type', 'application/octet-stream')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            print(f"[OK] Sent {len(data) / 1024 / 1024:.2f} MB")
    
    def do_POST(self):
        if self.path == '/upload':
            content_length = int(self.headers.get('Content-Length', 0))
            start = time.time()
            received = 0
            
            while received < content_length:
                chunk = self.rfile.read(min(1024*1024, content_length - received))
                if not chunk:
                    break
                received += len(chunk)
            
            elapsed = time.time() - start
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {
                'received': received,
                'elapsed': elapsed,
                'speed_mbps': (received / elapsed * 8 / 1024 / 1024) if elapsed > 0 else 0
            }
            self.wfile.write(json.dumps(response).encode())
            print(f"[OK] Received {received / 1024 / 1024:.2f} MB in {elapsed:.2f}s")
    
    def log_message(self, format, *args):
        pass

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

if __name__ == '__main__':
    print("=" * 60)
    print("Network Speed Test Server")
    print("=" * 60)
    print(f"\nServer starting on port {TEST_PORT}...")
    print(f"Local: http://127.0.0.1:{TEST_PORT}")
    print(f"LAN: http://{get_local_ip()}:{TEST_PORT}")
    print("\nUse Android app to connect and test speed")
    print("Press Ctrl+C to stop\n")
    
    server = HTTPServer(('0.0.0.0', TEST_PORT), SpeedTestHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[OK] Server stopped")
        server.server_close()
