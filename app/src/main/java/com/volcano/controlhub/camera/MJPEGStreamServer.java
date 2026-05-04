package com.volcano.controlhub.camera;

import android.content.Context;
import android.content.Intent;
import android.util.Log;

import fi.iki.elonen.NanoHTTPD;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.TimeUnit;

public class MJPEGStreamServer extends NanoHTTPD {
    
    private static final String TAG = "MJPEGStreamServer";
    public static final int DEFAULT_PORT = 8766;
    
    private static final String BOUNDARY = "ControlHubFrame";
    private static final String CONTENT_TYPE = "multipart/x-mixed-replace; boundary=" + BOUNDARY;
    
    private BlockingQueue<byte[]> frameQueue = new LinkedBlockingQueue<>(2);
    private volatile boolean streaming = false;
    private byte[] latestFrame = null;
    private final Object frameLock = new Object();
    
    private CameraController cameraController;
    private int currentCamera = CameraController.CAMERA_FRONT;
    private boolean cameraStarted = false;
    
    private volatile String latestBarcodeValue = null;
    private volatile String latestBarcodeFormat = null;
    private final Object barcodeLock = new Object();
    
    private CameraController.BarcodeCallback serverBarcodeCallback;
    
    private Context context;
    
    public MJPEGStreamServer() {
        super(DEFAULT_PORT);
    }
    
    public MJPEGStreamServer(int port) {
        super(port);
    }
    
    public void setContext(Context context) {
        this.context = context;
    }
    
    public void setCameraController(CameraController controller) {
        this.cameraController = controller;
        
        if (controller != null) {
            serverBarcodeCallback = (value, format, formatName) -> {
                synchronized (barcodeLock) {
                    latestBarcodeValue = value;
                    latestBarcodeFormat = formatName;
                }
                Log.d(TAG, "Barcode received: " + value + " (" + formatName + ")");
            };
            controller.setBarcodeCallback(serverBarcodeCallback);
        }
    }
    
    public CameraController.BarcodeCallback getBarcodeCallback() {
        return serverBarcodeCallback;
    }
    
    public void provideFrame(byte[] jpegData) {
        synchronized (frameLock) {
            latestFrame = jpegData;
        }
        
        if (streaming) {
            frameQueue.offer(jpegData);
        }
    }
    
    @Override
    public Response serve(IHTTPSession session) {
        String uri = session.getUri();
        Method method = session.getMethod();
        
        Log.d(TAG, "Request: " + method + " " + uri);
        
        try {
            switch (uri) {
                case "/camera/stream":
                    return handleStreamRequest();
                    
                case "/camera/snapshot":
                    return handleSnapshotRequest();
                    
                case "/camera/status":
                    return handleStatusRequest();
                    
                case "/camera/start":
                    if (method == Method.POST) {
                        return handleStartCamera(session);
                    }
                    break;
                    
                case "/camera/stop":
                    if (method == Method.POST) {
                        return handleStopCamera();
                    }
                    break;
                    
                case "/camera/switch":
                    if (method == Method.POST) {
                        return handleSwitchCamera();
                    }
                    break;
                    
                case "/barcode/start":
                    if (method == Method.POST) {
                        return handleBarcodeStart();
                    }
                    break;
                    
                case "/barcode/stop":
                    if (method == Method.POST) {
                        return handleBarcodeStop();
                    }
                    break;
                    
                case "/barcode/result":
                    return handleBarcodeResult();
                    
                case "/camera/open":
                    if (method == Method.POST) {
                        return handleOpenCamera();
                    }
                    break;
                    
                case "/camera/close":
                    if (method == Method.POST) {
                        return handleCloseCamera();
                    }
                    break;
                    
                default:
                    if (uri.equals("/") || uri.equals("/camera")) {
                        return handleStatusRequest();
                    }
            }
        } catch (Exception e) {
            Log.e(TAG, "Error handling request: " + uri, e);
            return newFixedLengthResponse(Response.Status.INTERNAL_ERROR, 
                    MIME_PLAINTEXT, "Error: " + e.getMessage());
        }
        
        return newFixedLengthResponse(Response.Status.NOT_FOUND, 
                MIME_PLAINTEXT, "Not Found");
    }
    
    private Response handleStreamRequest() {
        streaming = true;
        Log.d(TAG, "Stream request received, streaming started");
        
        return newChunkedResponse(Response.Status.OK, CONTENT_TYPE, new InputStream() {
            private boolean closed = false;
            private byte[] currentData = null;
            private int currentPos = 0;
            
            @Override
            public int read() throws IOException {
                if (closed) {
                    return -1;
                }
                
                if (currentData == null || currentPos >= currentData.length) {
                    if (!prepareNextFrame()) {
                        return -1;
                    }
                }
                
                if (currentData == null || currentPos >= currentData.length) {
                    return -1;
                }
                
                return currentData[currentPos++] & 0xFF;
            }
            
            @Override
            public int read(byte[] buffer, int byteOffset, int byteCount) throws IOException {
                if (closed) {
                    return -1;
                }
                
                if (currentData == null || currentPos >= currentData.length) {
                    if (!prepareNextFrame()) {
                        return -1;
                    }
                }
                
                if (currentData == null) {
                    return -1;
                }
                
                int bytesToCopy = Math.min(byteCount, currentData.length - currentPos);
                System.arraycopy(currentData, currentPos, buffer, byteOffset, bytesToCopy);
                currentPos += bytesToCopy;
                
                return bytesToCopy;
            }
            
            private boolean prepareNextFrame() {
                try {
                    byte[] frame = frameQueue.poll(2, TimeUnit.SECONDS);
                    if (frame == null) {
                        synchronized (frameLock) {
                            frame = latestFrame;
                        }
                    }
                    
                    if (frame == null) {
                        Log.w(TAG, "No frame available after waiting");
                        return false;
                    }
                    
                    StringBuilder header = new StringBuilder();
                    header.append("--").append(BOUNDARY).append("\r\n");
                    header.append("Content-Type: image/jpeg\r\n");
                    header.append("Content-Length: ").append(frame.length).append("\r\n");
                    header.append("\r\n");
                    
                    byte[] headerBytes = header.toString().getBytes("UTF-8");
                    
                    currentData = new byte[headerBytes.length + frame.length + 2];
                    System.arraycopy(headerBytes, 0, currentData, 0, headerBytes.length);
                    System.arraycopy(frame, 0, currentData, headerBytes.length, frame.length);
                    currentData[currentData.length - 2] = '\r';
                    currentData[currentData.length - 1] = '\n';
                    currentPos = 0;
                    
                    Log.d(TAG, "Prepared frame: " + frame.length + " bytes, total: " + currentData.length);
                    return true;
                    
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    closed = true;
                    return false;
                } catch (Exception e) {
                    Log.e(TAG, "Error preparing frame", e);
                    return false;
                }
            }
            
            @Override
            public void close() throws IOException {
                closed = true;
                streaming = false;
                Log.d(TAG, "Stream closed");
                super.close();
            }
        });
    }
    
    private Response handleSnapshotRequest() {
        byte[] frame;
        synchronized (frameLock) {
            frame = latestFrame;
        }
        
        if (frame == null) {
            return newFixedLengthResponse(Response.Status.NOT_FOUND, 
                    MIME_PLAINTEXT, "No frame available");
        }
        
        return newFixedLengthResponse(Response.Status.OK, "image/jpeg", 
                new ByteArrayInputStream(frame), frame.length);
    }
    
    private Response handleStatusRequest() {
        StringBuilder json = new StringBuilder();
        json.append("{");
        json.append("\"status\":\"ok\",");
        json.append("\"camera\":\"").append(currentCamera == CameraController.CAMERA_FRONT ? "front" : "back").append("\",");
        json.append("\"resolution\":\"").append(cameraController != null ? cameraController.getWidth() : 1280)
            .append("x").append(cameraController != null ? cameraController.getHeight() : 720).append("\",");
        json.append("\"streaming\":").append(streaming).append(",");
        json.append("\"cameraStarted\":").append(cameraStarted);
        json.append("}");
        
        return newFixedLengthResponse(Response.Status.OK, "application/json", json.toString());
    }
    
    private Response handleStartCamera(IHTTPSession session) {
        try {
            java.util.Map<String, String> body = new java.util.HashMap<>();
            session.parseBody(body);
            
            String jsonData = body.get("postData");
            if (jsonData != null) {
                if (jsonData.contains("\"front\"")) {
                    currentCamera = CameraController.CAMERA_FRONT;
                } else if (jsonData.contains("\"back\"")) {
                    currentCamera = CameraController.CAMERA_BACK;
                }
            }
            
            cameraStarted = true;
            
            String response = "{\"status\":\"ok\",\"message\":\"Camera started\",\"camera\":\"" + 
                    (currentCamera == CameraController.CAMERA_FRONT ? "front" : "back") + "\"}";
            return newFixedLengthResponse(Response.Status.OK, "application/json", response);
            
        } catch (Exception e) {
            Log.e(TAG, "Error starting camera", e);
            return newFixedLengthResponse(Response.Status.INTERNAL_ERROR, 
                    "application/json", "{\"status\":\"error\",\"message\":\"" + e.getMessage() + "\"}");
        }
    }
    
    private Response handleStopCamera() {
        cameraStarted = false;
        streaming = false;
        
        return newFixedLengthResponse(Response.Status.OK, "application/json", 
                "{\"status\":\"ok\",\"message\":\"Camera stopped\"}");
    }
    
    private Response handleSwitchCamera() {
        currentCamera = (currentCamera == CameraController.CAMERA_FRONT) ? 
                CameraController.CAMERA_BACK : CameraController.CAMERA_FRONT;
        
        if (cameraController != null) {
            cameraController.switchCamera();
        }
        
        String response = "{\"status\":\"ok\",\"camera\":\"" + 
                (currentCamera == CameraController.CAMERA_FRONT ? "front" : "back") + "\"}";
        return newFixedLengthResponse(Response.Status.OK, "application/json", response);
    }
    
    public boolean isStreaming() {
        return streaming;
    }
    
    public boolean isCameraStarted() {
        return cameraStarted;
    }
    
    public int getCurrentCamera() {
        return currentCamera;
    }
    
    private Response handleBarcodeStart() {
        if (cameraController == null) {
            return newFixedLengthResponse(Response.Status.INTERNAL_ERROR, 
                    "application/json", "{\"status\":\"error\",\"message\":\"Camera not initialized\"}");
        }
        
        synchronized (barcodeLock) {
            latestBarcodeValue = null;
            latestBarcodeFormat = null;
        }
        
        cameraController.setBarcodeScanningEnabled(true);
        
        Log.d(TAG, "Barcode scanning started");
        return newFixedLengthResponse(Response.Status.OK, "application/json", 
                "{\"status\":\"ok\",\"message\":\"Barcode scanning started\"}");
    }
    
    private Response handleBarcodeStop() {
        if (cameraController != null) {
            cameraController.setBarcodeScanningEnabled(false);
        }
        
        Log.d(TAG, "Barcode scanning stopped");
        return newFixedLengthResponse(Response.Status.OK, "application/json", 
                "{\"status\":\"ok\",\"message\":\"Barcode scanning stopped\"}");
    }
    
    private Response handleBarcodeResult() {
        synchronized (barcodeLock) {
            if (latestBarcodeValue == null) {
                return newFixedLengthResponse(Response.Status.OK, "application/json", 
                        "{\"status\":\"waiting\",\"message\":\"No barcode detected yet\"}");
            }
            
            String escapedValue = latestBarcodeValue
                    .replace("\\", "\\\\")
                    .replace("\"", "\\\"")
                    .replace("\n", "\\n")
                    .replace("\r", "\\r");
            
            String response = "{\"status\":\"ok\",\"value\":\"" + escapedValue + "\",\"format\":\"" + latestBarcodeFormat + "\"}";
            
            latestBarcodeValue = null;
            latestBarcodeFormat = null;
            
            return newFixedLengthResponse(Response.Status.OK, "application/json", response);
        }
    }
    
    private Response handleOpenCamera() {
        if (context == null) {
            return newFixedLengthResponse(Response.Status.INTERNAL_ERROR, 
                    "application/json", "{\"status\":\"error\",\"message\":\"Context not available\"}");
        }
        
        try {
            Intent intent = new Intent(context, CameraActivity.class);
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            context.startActivity(intent);
            
            Log.d(TAG, "CameraActivity opened");
            return newFixedLengthResponse(Response.Status.OK, "application/json", 
                    "{\"status\":\"ok\",\"message\":\"Camera activity opened\"}");
        } catch (Exception e) {
            Log.e(TAG, "Failed to open camera activity", e);
            return newFixedLengthResponse(Response.Status.INTERNAL_ERROR, 
                    "application/json", "{\"status\":\"error\",\"message\":\"" + e.getMessage() + "\"}");
        }
    }
    
    private Response handleCloseCamera() {
        if (context == null) {
            return newFixedLengthResponse(Response.Status.INTERNAL_ERROR, 
                    "application/json", "{\"status\":\"error\",\"message\":\"Context not available\"}");
        }
        
        try {
            Intent intent = new Intent("com.volcano.controlhub.camera.CLOSE_CAMERA");
            context.sendBroadcast(intent);
            
            Log.d(TAG, "Close camera broadcast sent");
            return newFixedLengthResponse(Response.Status.OK, "application/json", 
                    "{\"status\":\"ok\",\"message\":\"Camera close request sent\"}");
        } catch (Exception e) {
            Log.e(TAG, "Failed to close camera activity", e);
            return newFixedLengthResponse(Response.Status.INTERNAL_ERROR, 
                    "application/json", "{\"status\":\"error\",\"message\":\"" + e.getMessage() + "\"}");
        }
    }
}
