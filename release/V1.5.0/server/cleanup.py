#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cleanup script for ControlHub Server
Kills any remaining server processes and frees up ports.
"""

import subprocess
import sys
import time

PORTS = [8765, 8766, 8767]


def find_processes_on_port(port):
    """Find processes using the specified port"""
    try:
        result = subprocess.run(
            ['netstat', '-ano'],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        
        pids = set()
        for line in result.stdout.split('\n'):
            if f':{port}' in line and 'LISTENING' in line:
                parts = line.split()
                if len(parts) >= 5:
                    try:
                        pid = int(parts[-1])
                        pids.add(pid)
                    except ValueError:
                        pass
        return pids
    except Exception as e:
        print(f"Error finding processes on port {port}: {e}")
        return set()


def kill_process(pid):
    """Kill a process by PID"""
    try:
        subprocess.run(
            ['taskkill', '/F', '/PID', str(pid)],
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        print(f"  Killed process PID {pid}")
        return True
    except Exception as e:
        print(f"  Failed to kill PID {pid}: {e}")
        return False


def find_python_processes():
    """Find Python processes related to ControlHub"""
    try:
        result = subprocess.run(
            ['tasklist', '/FI', 'IMAGENAME eq python.exe', '/FO', 'CSV', '/NH'],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        
        pids = []
        for line in result.stdout.split('\n'):
            if 'python.exe' in line.lower():
                parts = line.split(',')
                if len(parts) >= 2:
                    try:
                        pid = int(parts[1].strip('"'))
                        pids.append(pid)
                    except ValueError:
                        pass
        return pids
    except Exception as e:
        print(f"Error finding Python processes: {e}")
        return []


def cleanup():
    """Main cleanup function"""
    print("=" * 50)
    print("ControlHub Server Cleanup")
    print("=" * 50)
    
    killed_any = False
    
    # Clean up ports
    print("\n[1] Checking ports...")
    for port in PORTS:
        pids = find_processes_on_port(port)
        if pids:
            print(f"\n  Port {port} is in use by PIDs: {pids}")
            for pid in pids:
                if kill_process(pid):
                    killed_any = True
        else:
            print(f"  Port {port}: Free")
    
    # Give processes time to terminate
    if killed_any:
        print("\n[2] Waiting for processes to terminate...")
        time.sleep(1)
    
    # Verify ports are free
    print("\n[3] Verifying ports...")
    all_free = True
    for port in PORTS:
        pids = find_processes_on_port(port)
        if pids:
            print(f"  Port {port}: STILL IN USE by PIDs {pids}")
            all_free = False
        else:
            print(f"  Port {port}: Free")
    
    if all_free:
        print("\n" + "=" * 50)
        print("All ports are now free!")
        print("=" * 50)
    else:
        print("\n" + "=" * 50)
        print("WARNING: Some ports are still in use!")
        print("You may need to manually kill the processes or restart your computer.")
        print("=" * 50)
    
    return all_free


if __name__ == "__main__":
    cleanup()
