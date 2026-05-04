#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Brightness Control Module
Provides unified brightness control functionality for monitors.
Supports WMI, DDC/CI, and Gamma Ramp methods.
"""

import sys
import subprocess
from pathlib import Path


def get_script_path():
    """Get the path to the brightness_control.ps1 script"""
    return Path(__file__).parent / "brightness_control.ps1"


def set_brightness(brightness, silent=True):
    """
    Set monitor brightness (0-100)
    
    Args:
        brightness: int 0-100
        silent: if True, suppress console window on Windows
    
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        brightness = int(brightness)
        if brightness < 0 or brightness > 100:
            return False, f"Invalid brightness value: {brightness} (must be 0-100)"
        
        ps_script = get_script_path()
        
        if not ps_script.exists():
            return False, f"Brightness script not found: {ps_script}"
        
        cmd = [
            'powershell',
            '-ExecutionPolicy', 'Bypass',
            '-File', str(ps_script),
            '-Brightness', str(brightness)
        ]
        
        creationflags = 0
        if silent and sys.platform == 'win32':
            creationflags = subprocess.CREATE_NO_WINDOW
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=creationflags
        )
        
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        
        if result.returncode == 0 and "OK:" in stdout:
            message = stdout.split(":", 1)[1].strip() if ":" in stdout else "OK"
            return True, f"[OK] {message}"
        else:
            error_msg = stderr if stderr else stdout
            return False, error_msg if error_msg else "Unknown error"
            
    except subprocess.TimeoutExpired:
        return False, "Timeout: brightness control took too long"
    except Exception as e:
        return False, f"Error: {str(e)}"


def show_brightness_dialog():
    """
    Show a GUI dialog for brightness adjustment
    """
    import tkinter as tk
    from tkinter import ttk
    
    current_brightness = 100
    
    root = tk.Tk()
    root.title("Adjust Brightness")
    root.geometry("380x200")
    root.resizable(False, False)
    
    main_frame = ttk.Frame(root, padding="20")
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    title_label = ttk.Label(main_frame, text="Monitor Brightness", font=('Segoe UI', 12, 'bold'))
    title_label.pack(pady=(0, 15))
    
    slider_frame = ttk.Frame(main_frame)
    slider_frame.pack(fill=tk.X, pady=5)
    
    ttk.Label(slider_frame, text="0%", font=('Segoe UI', 9)).pack(side='left')
    ttk.Label(slider_frame, text="100%", font=('Segoe UI', 9)).pack(side='right')
    
    brightness_var = tk.IntVar(value=current_brightness)
    
    def on_brightness_change(value):
        nonlocal current_brightness
        current_brightness = int(float(value))
        brightness_label.config(text=f"{current_brightness}%")
    
    def on_brightness_release(event):
        success, msg = set_brightness(current_brightness)
        if not success:
            status_label.config(text=f"Error: {msg[:30]}", foreground='red')
        else:
            status_label.config(text=msg, foreground='green')
    
    slider = ttk.Scale(
        slider_frame,
        from_=0,
        to=100,
        orient=tk.HORIZONTAL,
        variable=brightness_var,
        command=on_brightness_change,
        length=320
    )
    slider.pack(fill=tk.X, pady=5)
    slider.bind('<ButtonRelease-1>', on_brightness_release)
    
    brightness_label = ttk.Label(main_frame, text=f"{current_brightness}%", font=('Segoe UI', 20, 'bold'))
    brightness_label.pack(pady=5)
    
    status_label = ttk.Label(main_frame, text="", font=('Segoe UI', 9))
    status_label.pack(pady=5)
    
    btn_frame = ttk.Frame(main_frame)
    btn_frame.pack(fill=tk.X, pady=10)
    
    def set_and_close(value):
        set_brightness(value)
        root.destroy()
    
    ttk.Button(btn_frame, text="25%", width=8, command=lambda: set_and_close(25)).pack(side='left', padx=5, expand=True)
    ttk.Button(btn_frame, text="50%", width=8, command=lambda: set_and_close(50)).pack(side='left', padx=5, expand=True)
    ttk.Button(btn_frame, text="75%", width=8, command=lambda: set_and_close(75)).pack(side='left', padx=5, expand=True)
    ttk.Button(btn_frame, text="100%", width=8, command=lambda: set_and_close(100)).pack(side='left', padx=5, expand=True)
    
    root.mainloop()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            brightness = int(sys.argv[1])
            success, msg = set_brightness(brightness)
            print(msg)
            sys.exit(0 if success else 1)
        except ValueError:
            print("Usage: python brightness.py [0-100]")
            sys.exit(1)
    else:
        show_brightness_dialog()
