package com.volcano.controlhub.camera;

import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Matrix;
import android.graphics.Rect;
import android.graphics.YuvImage;
import android.media.Image;
import android.util.Log;
import android.util.Size;

import androidx.annotation.NonNull;
import androidx.camera.core.CameraSelector;
import androidx.camera.core.ImageAnalysis;
import androidx.camera.core.ImageProxy;
import androidx.camera.core.Preview;
import androidx.camera.lifecycle.ProcessCameraProvider;
import androidx.camera.view.PreviewView;
import androidx.core.content.ContextCompat;
import androidx.lifecycle.LifecycleOwner;

import com.google.android.gms.tasks.Task;
import com.google.common.util.concurrent.ListenableFuture;
import com.google.mlkit.vision.barcode.BarcodeScanner;
import com.google.mlkit.vision.barcode.BarcodeScannerOptions;
import com.google.mlkit.vision.barcode.BarcodeScanning;
import com.google.mlkit.vision.barcode.common.Barcode;
import com.google.mlkit.vision.common.InputImage;

import java.io.File;
import java.nio.ByteBuffer;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class CameraController {
    
    private static final String TAG = "CameraController";
    
    public static final int CAMERA_FRONT = CameraSelector.LENS_FACING_FRONT;
    public static final int CAMERA_BACK = CameraSelector.LENS_FACING_BACK;
    
    public static final int DEFAULT_WIDTH = 1280;
    public static final int DEFAULT_HEIGHT = 720;
    public static final int DEFAULT_JPEG_QUALITY = 75;
    
    private ProcessCameraProvider cameraProvider;
    private Preview preview;
    private ImageAnalysis imageAnalysis;
    private CameraSelector cameraSelector;
    
    private int currentCamera = CAMERA_FRONT;
    private int width = DEFAULT_WIDTH;
    private int height = DEFAULT_HEIGHT;
    private int jpegQuality = DEFAULT_JPEG_QUALITY;
    
    private PreviewView previewView;
    private LifecycleOwner lifecycleOwner;
    private ExecutorService cameraExecutor;
    
    private FrameCallback frameCallback;
    private BarcodeCallback barcodeCallback;
    private boolean isRunning = false;
    private boolean barcodeScanningEnabled = false;
    
    private BarcodeScanner barcodeScanner;
    
    public interface FrameCallback {
        void onFrame(byte[] jpegData, int width, int height);
    }
    
    public interface BarcodeCallback {
        void onBarcodeDetected(String barcodeValue, int barcodeFormat, String formatName);
    }
    
    public CameraController() {
        cameraExecutor = Executors.newSingleThreadExecutor();
        cameraSelector = new CameraSelector.Builder()
                .requireLensFacing(currentCamera)
                .build();
        
        BarcodeScannerOptions options = new BarcodeScannerOptions.Builder()
                .setBarcodeFormats(Barcode.FORMAT_ALL_FORMATS)
                .build();
        barcodeScanner = BarcodeScanning.getClient(options);
    }
    
    public void initialize(@NonNull LifecycleOwner owner, @NonNull PreviewView view, 
                          @NonNull FrameCallback callback) {
        this.lifecycleOwner = owner;
        this.previewView = view;
        this.frameCallback = callback;
        
        ListenableFuture<ProcessCameraProvider> cameraProviderFuture = 
                ProcessCameraProvider.getInstance(view.getContext());
        
        cameraProviderFuture.addListener(() -> {
            try {
                cameraProvider = cameraProviderFuture.get();
                setupUseCases();
            } catch (Exception e) {
                Log.e(TAG, "Failed to get camera provider", e);
            }
        }, ContextCompat.getMainExecutor(view.getContext()));
    }
    
    private void setupUseCases() {
        if (cameraProvider == null || lifecycleOwner == null || previewView == null) {
            return;
        }
        
        cameraProvider.unbindAll();
        
        preview = new Preview.Builder()
                .setTargetResolution(new Size(width, height))
                .build();
        
        imageAnalysis = new ImageAnalysis.Builder()
                .setTargetResolution(new Size(width, height))
                .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                .build();
        
        imageAnalysis.setAnalyzer(cameraExecutor, this::analyzeImage);
        
        preview.setSurfaceProvider(previewView.getSurfaceProvider());
        
        cameraProvider.bindToLifecycle(lifecycleOwner, cameraSelector, preview, imageAnalysis);
        
        isRunning = true;
        Log.d(TAG, "Camera started: " + (currentCamera == CAMERA_FRONT ? "front" : "back"));
    }
    
    private void analyzeImage(@NonNull ImageProxy imageProxy) {
        try {
            Image image = imageProxy.getImage();
            if (image == null) {
                imageProxy.close();
                return;
            }
            
            int width = imageProxy.getWidth();
            int height = imageProxy.getHeight();
            int rotation = imageProxy.getImageInfo().getRotationDegrees();
            
            byte[] nv21 = imageToNv21(image, width, height);
            byte[] jpeg = nv21ToJpeg(nv21, width, height, rotation);
            
            if (frameCallback != null && jpeg != null) {
                frameCallback.onFrame(jpeg, width, height);
            }
            
            if (barcodeScanningEnabled && barcodeCallback != null) {
                scanBarcode(imageProxy, rotation);
            }
            
        } catch (Exception e) {
            Log.e(TAG, "Error analyzing image", e);
        } finally {
            if (!barcodeScanningEnabled) {
                imageProxy.close();
            }
        }
    }
    
    private void scanBarcode(@NonNull ImageProxy imageProxy, int rotation) {
        Image image = imageProxy.getImage();
        if (image == null) {
            imageProxy.close();
            return;
        }
        
        InputImage inputImage = InputImage.fromMediaImage(image, rotation);
        
        Task<List<Barcode>> result = barcodeScanner.process(inputImage)
                .addOnSuccessListener(barcodes -> {
                    if (barcodes != null && !barcodes.isEmpty()) {
                        for (Barcode barcode : barcodes) {
                            String value = barcode.getRawValue();
                            int format = barcode.getFormat();
                            String formatName = getBarcodeFormatName(format);
                            
                            if (value != null && !value.isEmpty()) {
                                Log.d(TAG, "Barcode detected: " + value + " (" + formatName + ")");
                                if (barcodeCallback != null) {
                                    barcodeCallback.onBarcodeDetected(value, format, formatName);
                                }
                            }
                        }
                    }
                    imageProxy.close();
                })
                .addOnFailureListener(e -> {
                    Log.e(TAG, "Barcode scanning failed", e);
                    imageProxy.close();
                });
    }
    
    private String getBarcodeFormatName(int format) {
        switch (format) {
            case Barcode.FORMAT_QR_CODE: return "QR Code";
            case Barcode.FORMAT_EAN_13: return "EAN-13";
            case Barcode.FORMAT_EAN_8: return "EAN-8";
            case Barcode.FORMAT_UPC_A: return "UPC-A";
            case Barcode.FORMAT_UPC_E: return "UPC-E";
            case Barcode.FORMAT_CODE_128: return "Code 128";
            case Barcode.FORMAT_CODE_39: return "Code 39";
            case Barcode.FORMAT_CODE_93: return "Code 93";
            case Barcode.FORMAT_CODABAR: return "Codabar";
            case Barcode.FORMAT_DATA_MATRIX: return "Data Matrix";
            case Barcode.FORMAT_PDF417: return "PDF417";
            case Barcode.FORMAT_AZTEC: return "Aztec";
            case Barcode.FORMAT_ITF: return "ITF";
            default: return "Unknown";
        }
    }
    
    private byte[] imageToNv21(Image image, int width, int height) {
        Image.Plane[] planes = image.getPlanes();
        byte[] nv21 = new byte[width * height * 3 / 2];
        
        ByteBuffer yBuffer = planes[0].getBuffer();
        int yRowStride = planes[0].getRowStride();
        int yPixelStride = planes[0].getPixelStride();
        
        byte[] yBytes = new byte[yBuffer.remaining()];
        yBuffer.get(yBytes);
        
        for (int row = 0; row < height; row++) {
            for (int col = 0; col < width; col++) {
                int srcIndex = row * yRowStride + col * yPixelStride;
                int dstIndex = row * width + col;
                if (srcIndex < yBytes.length) {
                    nv21[dstIndex] = yBytes[srcIndex];
                }
            }
        }
        
        ByteBuffer uBuffer = planes[1].getBuffer();
        ByteBuffer vBuffer = planes[2].getBuffer();
        
        int uvRowStride = planes[1].getRowStride();
        int uvPixelStride = planes[1].getPixelStride();
        int uvHeight = height / 2;
        int uvWidth = width / 2;
        
        byte[] uBytes = new byte[uBuffer.remaining()];
        byte[] vBytes = new byte[vBuffer.remaining()];
        uBuffer.get(uBytes);
        vBuffer.get(vBytes);
        
        int uvIndex = width * height;
        
        for (int row = 0; row < uvHeight; row++) {
            for (int col = 0; col < uvWidth; col++) {
                int srcIndex = row * uvRowStride + col * uvPixelStride;
                
                if (srcIndex < vBytes.length) {
                    nv21[uvIndex++] = vBytes[srcIndex];
                }
                if (srcIndex < uBytes.length) {
                    nv21[uvIndex++] = uBytes[srcIndex];
                }
            }
        }
        
        return nv21;
    }
    
    private byte[] nv21ToJpeg(byte[] nv21, int width, int height, int rotation) {
        try {
            YuvImage yuvImage = new YuvImage(nv21, android.graphics.ImageFormat.NV21, 
                    width, height, null);
            java.io.ByteArrayOutputStream out = new java.io.ByteArrayOutputStream();
            yuvImage.compressToJpeg(new Rect(0, 0, width, height), jpegQuality, out);
            
            byte[] jpegBytes = out.toByteArray();
            
            jpegBytes = addExifRotation(jpegBytes, rotation, width, height);
            
            return jpegBytes;
        } catch (Exception e) {
            Log.e(TAG, "Error converting to JPEG", e);
            return null;
        }
    }
    
    private byte[] addExifRotation(byte[] jpegBytes, int rotation, int width, int height) {
        try {
            File tempFile = File.createTempFile("camera_exif", ".jpg");
            try {
                java.io.FileOutputStream fos = new java.io.FileOutputStream(tempFile);
                fos.write(jpegBytes);
                fos.close();
                
                android.media.ExifInterface exif = new android.media.ExifInterface(tempFile.getAbsolutePath());
                
                int exifOrientation;
                switch (rotation) {
                    case 90:
                        exifOrientation = android.media.ExifInterface.ORIENTATION_ROTATE_90;
                        break;
                    case 180:
                        exifOrientation = android.media.ExifInterface.ORIENTATION_ROTATE_180;
                        break;
                    case 270:
                        exifOrientation = android.media.ExifInterface.ORIENTATION_ROTATE_270;
                        break;
                    default:
                        exifOrientation = android.media.ExifInterface.ORIENTATION_NORMAL;
                        break;
                }
                
                exif.setAttribute(android.media.ExifInterface.TAG_ORIENTATION, 
                    String.valueOf(exifOrientation));
                exif.setAttribute(android.media.ExifInterface.TAG_IMAGE_WIDTH, String.valueOf(width));
                exif.setAttribute(android.media.ExifInterface.TAG_IMAGE_LENGTH, String.valueOf(height));
                
                if (currentCamera == CAMERA_FRONT) {
                    exif.setAttribute("CameraFacing", "front");
                } else {
                    exif.setAttribute("CameraFacing", "back");
                }
                
                exif.saveAttributes();
                
                java.io.FileInputStream fis = new java.io.FileInputStream(tempFile);
                byte[] result = new byte[(int) tempFile.length()];
                fis.read(result);
                fis.close();
                
                return result;
            } finally {
                tempFile.delete();
            }
        } catch (Exception e) {
            Log.e(TAG, "Error adding EXIF data", e);
            return jpegBytes;
        }
    }
    
    public void switchCamera() {
        currentCamera = (currentCamera == CAMERA_FRONT) ? CAMERA_BACK : CAMERA_FRONT;
        cameraSelector = new CameraSelector.Builder()
                .requireLensFacing(currentCamera)
                .build();
        
        if (isRunning) {
            setupUseCases();
        }
    }
    
    public void setResolution(int width, int height) {
        this.width = width;
        this.height = height;
        
        if (isRunning) {
            setupUseCases();
        }
    }
    
    public void setJpegQuality(int quality) {
        this.jpegQuality = Math.max(10, Math.min(100, quality));
    }
    
    public void stop() {
        if (cameraProvider != null) {
            cameraProvider.unbindAll();
        }
        isRunning = false;
        Log.d(TAG, "Camera stopped");
    }
    
    public void destroy() {
        stop();
        if (cameraExecutor != null) {
            cameraExecutor.shutdown();
        }
    }
    
    public boolean isRunning() {
        return isRunning;
    }
    
    public int getCurrentCamera() {
        return currentCamera;
    }
    
    public int getWidth() {
        return width;
    }
    
    public int getHeight() {
        return height;
    }
    
    public void setBarcodeCallback(BarcodeCallback callback) {
        this.barcodeCallback = callback;
    }
    
    public void setBarcodeScanningEnabled(boolean enabled) {
        this.barcodeScanningEnabled = enabled;
        Log.d(TAG, "Barcode scanning " + (enabled ? "enabled" : "disabled"));
    }
    
    public boolean isBarcodeScanningEnabled() {
        return barcodeScanningEnabled;
    }
}
