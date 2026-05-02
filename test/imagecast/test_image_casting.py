#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Image Casting Test
Tests the image casting functionality
"""

import sys
import os
import time
import json
import base64
import threading
import unittest
from io import BytesIO
from http.server import HTTPServer, BaseHTTPRequestHandler

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'server'))

class ImageCastingState:
    def __init__(self):
        self.current_image = None
        self.current_image_name = None
        self.scale_level = 1.0
        self.last_update = None
        self.image_data = None
        self.auto_popup = False
        self.lock = threading.Lock()
        
    def set_image(self, image_data, image_name=None):
        with self.lock:
            self.image_data = image_data
            self.current_image = base64.b64encode(image_data).decode('utf-8') if image_data else None
            self.current_image_name = image_name or 'image.jpg'
            self.scale_level = 1.0
            self.last_update = time.time()
            self.auto_popup = True
            
    def set_scale(self, scale_level):
        with self.lock:
            self.scale_level = max(0.1, min(5.0, scale_level))
            self.last_update = time.time()
            
    def get_state(self):
        with self.lock:
            return {
                'has_image': self.current_image is not None,
                'image_name': self.current_image_name,
                'scale_level': self.scale_level,
                'last_update': self.last_update,
                'image_data': self.current_image,
                'image_size': len(self.image_data) if self.image_data else 0,
                'auto_popup': self.auto_popup
            }


class TestImageCastingState(unittest.TestCase):
    """Test cases for ImageCastingState class"""
    
    def setUp(self):
        self.state = ImageCastingState()
        
    def test_initial_state(self):
        """Test initial state has no image"""
        state = self.state.get_state()
        self.assertFalse(state['has_image'])
        self.assertEqual(state['scale_level'], 1.0)
        self.assertIsNone(state['image_name'])
        
    def test_set_image(self):
        """Test setting an image"""
        test_data = b'test image data'
        self.state.set_image(test_data, 'test.jpg')
        
        state = self.state.get_state()
        self.assertTrue(state['has_image'])
        self.assertEqual(state['image_name'], 'test.jpg')
        self.assertEqual(state['scale_level'], 1.0)
        self.assertEqual(state['image_size'], len(test_data))
        self.assertTrue(state['auto_popup'])
        
    def test_set_scale(self):
        """Test setting scale level"""
        self.state.set_scale(2.0)
        state = self.state.get_state()
        self.assertEqual(state['scale_level'], 2.0)
        
    def test_scale_clamping(self):
        """Test scale is clamped within valid range"""
        self.state.set_scale(10.0)
        self.assertEqual(self.state.get_state()['scale_level'], 5.0)
        
        self.state.set_scale(0.01)
        self.assertEqual(self.state.get_state()['scale_level'], 0.1)
        
    def test_clear_image(self):
        """Test clearing image"""
        self.state.set_image(b'test data', 'test.jpg')
        self.state.current_image = None
        self.state.current_image_name = None
        self.state.image_data = None
        self.state.scale_level = 1.0
        
        state = self.state.get_state()
        self.assertFalse(state['has_image'])


def create_test_image(width=100, height=100):
    """Create a simple test image (PNG format)"""
    png_header = bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
        0x00, 0x00, 0x00, width,
        0x00, 0x00, 0x00, height,
        0x08, 0x02, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00,
    ])
    
    png_data = png_header + bytes([
        0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41, 0x54,
        0x08, 0xD7, 0x63, 0xF8, 0x0F, 0x04, 0x00, 0x01,
        0x05, 0x01, 0x02, 0x00, 0x00, 0x00, 0x00, 0x49,
        0x45, 0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82
    ])
    
    return png_data


class TestImageCastingWorkflow(unittest.TestCase):
    """Test the complete image casting workflow"""
    
    def test_complete_workflow(self):
        """Test complete image casting workflow"""
        state = ImageCastingState()
        
        test_image = create_test_image()
        state.set_image(test_image, 'test_image.png')
        
        self.assertTrue(state.get_state()['has_image'])
        self.assertEqual(state.get_state()['image_name'], 'test_image.png')
        
        state.set_scale(1.5)
        self.assertEqual(state.get_state()['scale_level'], 1.5)
        
        state.set_scale(2.0)
        self.assertEqual(state.get_state()['scale_level'], 2.0)
        
        state.set_scale(1.0)
        self.assertEqual(state.get_state()['scale_level'], 1.0)
        
        state.current_image = None
        state.current_image_name = None
        state.image_data = None
        self.assertFalse(state.get_state()['has_image'])
        
    def test_concurrent_access(self):
        """Test concurrent access to state"""
        state = ImageCastingState()
        errors = []
        
        def set_image_thread():
            try:
                for i in range(10):
                    state.set_image(f'test{i}'.encode(), f'test{i}.jpg')
                    time.sleep(0.01)
            except Exception as e:
                errors.append(e)
        
        def set_scale_thread():
            try:
                for i in range(10):
                    state.set_scale(1.0 + i * 0.1)
                    time.sleep(0.01)
            except Exception as e:
                errors.append(e)
        
        t1 = threading.Thread(target=set_image_thread)
        t2 = threading.Thread(target=set_scale_thread)
        
        t1.start()
        t2.start()
        
        t1.join()
        t2.join()
        
        self.assertEqual(len(errors), 0)


def run_tests():
    """Run all tests"""
    print("=" * 60)
    print("Image Casting Tests")
    print("=" * 60)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestImageCastingState))
    suite.addTests(loader.loadTestsFromTestCase(TestImageCastingWorkflow))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("All tests passed!")
    else:
        print("Some tests failed!")
    print("=" * 60)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
