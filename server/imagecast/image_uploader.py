#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Image Uploader Tool
Uploads images from PC to Android device via USB display control server
"""

import os
import sys
import requests
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk

SERVER_URL = "http://localhost:8765"

class ImageUploaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Casting - PC Uploader")
        self.root.geometry("800x600")
        
        self.current_image = None
        self.current_image_path = None
        
        self.create_widgets()
        
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(button_frame, text="Select Image", command=self.select_image).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(button_frame, text="Upload to Device", command=self.upload_image).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Clear Image", command=self.clear_image).grid(row=0, column=2, padx=5)
        
        ttk.Separator(button_frame, orient=tk.VERTICAL).grid(row=0, column=3, sticky=(tk.N, tk.S), padx=10)
        
        ttk.Button(button_frame, text="Zoom In", command=self.zoom_in).grid(row=0, column=4, padx=5)
        ttk.Button(button_frame, text="Zoom Out", command=self.zoom_out).grid(row=0, column=5, padx=5)
        ttk.Button(button_frame, text="Reset Zoom", command=self.reset_zoom).grid(row=0, column=6, padx=5)
        
        self.preview_frame = ttk.Frame(main_frame, relief=tk.SUNKEN, borderwidth=2)
        self.preview_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.preview_label = ttk.Label(self.preview_frame, text="No image selected", anchor=tk.CENTER)
        self.preview_label.pack(expand=True, fill=tk.BOTH)
        
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
    def select_image(self):
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[
                ("Image Files", "*.jpg *.jpeg *.png *.bmp *.gif"),
                ("All Files", "*.*")
            ]
        )
        
        if file_path:
            self.current_image_path = file_path
            self.load_preview(file_path)
            self.status_var.set(f"Selected: {os.path.basename(file_path)}")
    
    def load_preview(self, file_path):
        try:
            image = Image.open(file_path)
            
            preview_width = 760
            preview_height = 480
            
            img_width, img_height = image.size
            ratio = min(preview_width / img_width, preview_height / img_height)
            new_width = int(img_width * ratio)
            new_height = int(img_height * ratio)
            
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.current_image = ImageTk.PhotoImage(image)
            
            self.preview_label.config(image=self.current_image, text="")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {e}")
            self.current_image = None
    
    def upload_image(self):
        if not self.current_image_path:
            messagebox.showwarning("Warning", "Please select an image first")
            return
        
        try:
            self.status_var.set("Uploading image...")
            self.root.update()
            
            with open(self.current_image_path, 'rb') as f:
                filename = os.path.basename(self.current_image_path)
                files = {'file': (filename, f, 'image/jpeg')}
                
                headers = {
                    'Content-Type': 'application/octet-stream',
                    'Content-Disposition': f'attachment; filename="{filename}"'
                }
                
                with open(self.current_image_path, 'rb') as img_file:
                    response = requests.post(
                        f"{SERVER_URL}/image/upload",
                        data=img_file.read(),
                        headers=headers,
                        timeout=30
                    )
            
            if response.status_code == 200:
                result = response.json()
                messagebox.showinfo("Success", f"Image uploaded successfully!\nSize: {result['size']} bytes")
                self.status_var.set("Upload complete")
            else:
                messagebox.showerror("Error", f"Upload failed: {response.text}")
                self.status_var.set("Upload failed")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to upload image: {e}")
            self.status_var.set("Upload error")
    
    def clear_image(self):
        try:
            response = requests.post(f"{SERVER_URL}/image/clear", timeout=10)
            if response.status_code == 200:
                messagebox.showinfo("Success", "Image cleared from device")
                self.status_var.set("Image cleared")
            else:
                messagebox.showerror("Error", "Failed to clear image")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear image: {e}")
    
    def zoom_in(self):
        try:
            response = requests.post(f"{SERVER_URL}/image/zoom-in", timeout=10)
            if response.status_code == 200:
                result = response.json()
                self.status_var.set(f"Zoom level: {result['scale']:.2f}x")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to zoom in: {e}")
    
    def zoom_out(self):
        try:
            response = requests.post(f"{SERVER_URL}/image/zoom-out", timeout=10)
            if response.status_code == 200:
                result = response.json()
                self.status_var.set(f"Zoom level: {result['scale']:.2f}x")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to zoom out: {e}")
    
    def reset_zoom(self):
        try:
            response = requests.post(f"{SERVER_URL}/image/zoom-reset", timeout=10)
            if response.status_code == 200:
                self.status_var.set("Zoom reset to 1.0x")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reset zoom: {e}")

def main():
    root = tk.Tk()
    app = ImageUploaderApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
