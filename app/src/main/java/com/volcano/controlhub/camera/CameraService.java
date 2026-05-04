package com.volcano.controlhub.camera;

import android.content.Context;
import android.util.Log;

import androidx.camera.view.PreviewView;
import androidx.lifecycle.LifecycleOwner;

import java.io.IOException;

public class CameraService {
    
    private static final String TAG = "CameraService";
    
    private static CameraService instance;
    
    private CameraController cameraController;
    private MJPEGStreamServer streamServer;
    private Context context;
    private boolean isInitialized = false;
    
    private CameraService() {
    }
    
    public static synchronized CameraService getInstance() {
        if (instance == null) {
            instance = new CameraService();
        }
        return instance;
    }
    
    public void initialize(Context context) {
        if (isInitialized) {
            return;
        }
        
        this.context = context.getApplicationContext();
        
        cameraController = new CameraController();
        streamServer = new MJPEGStreamServer();
        streamServer.setContext(this.context);
        
        try {
            streamServer.start();
            Log.d(TAG, "MJPEG server started on port " + MJPEGStreamServer.DEFAULT_PORT);
        } catch (IOException e) {
            Log.e(TAG, "Failed to start MJPEG server", e);
        }
        
        isInitialized = true;
    }
    
    public void startCamera(LifecycleOwner owner, PreviewView previewView) {
        if (!isInitialized || cameraController == null) {
            Log.e(TAG, "CameraService not initialized");
            return;
        }
        
        cameraController.initialize(owner, previewView, (jpegData, width, height) -> {
            if (streamServer != null) {
                streamServer.provideFrame(jpegData);
            }
        });
        
        streamServer.setCameraController(cameraController);
    }
    
    public void stopCamera() {
        if (cameraController != null) {
            cameraController.stop();
        }
    }
    
    public void switchCamera() {
        if (cameraController != null) {
            cameraController.switchCamera();
        }
    }
    
    public void setResolution(int width, int height) {
        if (cameraController != null) {
            cameraController.setResolution(width, height);
        }
    }
    
    public void setJpegQuality(int quality) {
        if (cameraController != null) {
            cameraController.setJpegQuality(quality);
        }
    }
    
    public boolean isCameraRunning() {
        return cameraController != null && cameraController.isRunning();
    }
    
    public boolean isStreaming() {
        return streamServer != null && streamServer.isStreaming();
    }
    
    public int getServerPort() {
        return MJPEGStreamServer.DEFAULT_PORT;
    }
    
    public void setBarcodeCallback(CameraController.BarcodeCallback callback) {
        if (cameraController != null && streamServer != null) {
            final CameraController.BarcodeCallback serverCallback = streamServer.getBarcodeCallback();
            cameraController.setBarcodeCallback((value, format, formatName) -> {
                if (serverCallback != null) {
                    serverCallback.onBarcodeDetected(value, format, formatName);
                }
                if (callback != null) {
                    callback.onBarcodeDetected(value, format, formatName);
                }
            });
        }
    }
    
    public void setBarcodeScanningEnabled(boolean enabled) {
        if (cameraController != null) {
            cameraController.setBarcodeScanningEnabled(enabled);
        }
    }
    
    public boolean isBarcodeScanningEnabled() {
        return cameraController != null && cameraController.isBarcodeScanningEnabled();
    }
    
    public void destroy() {
        if (cameraController != null) {
            cameraController.destroy();
            cameraController = null;
        }
        
        if (streamServer != null) {
            streamServer.stop();
            streamServer = null;
        }
        
        isInitialized = false;
    }
}
