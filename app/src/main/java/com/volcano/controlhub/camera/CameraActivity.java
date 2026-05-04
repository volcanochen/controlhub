package com.volcano.controlhub.camera;

import android.Manifest;
import android.content.BroadcastReceiver;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.camera.view.PreviewView;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

import com.volcano.controlhub.R;

public class CameraActivity extends AppCompatActivity {
    
    private static final String TAG = "CameraActivity";
    private static final int CAMERA_PERMISSION_REQUEST = 100;
    public static final String ACTION_CLOSE_CAMERA = "com.volcano.controlhub.camera.CLOSE_CAMERA";
    
    private PreviewView previewView;
    private Button switchCameraButton;
    private Button scanButton;
    private Button backButton;
    private TextView statusText;
    private TextView urlText;
    private LinearLayout barcodeResultPanel;
    private TextView barcodeFormatText;
    private TextView barcodeValueText;
    
    private CameraService cameraService;
    private boolean hasCameraPermission = false;
    private boolean isScanning = false;
    private Handler handler = new Handler(Looper.getMainLooper());
    private Runnable hideBarcodeRunnable;
    private BroadcastReceiver closeReceiver;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_camera);
        
        initViews();
        registerCloseReceiver();
        checkCameraPermission();
    }
    
    private void registerCloseReceiver() {
        closeReceiver = new BroadcastReceiver() {
            @Override
            public void onReceive(Context context, Intent intent) {
                if (ACTION_CLOSE_CAMERA.equals(intent.getAction())) {
                    Log.d(TAG, "Received close camera broadcast");
                    finish();
                }
            }
        };
        
        IntentFilter filter = new IntentFilter(ACTION_CLOSE_CAMERA);
        registerReceiver(closeReceiver, filter);
    }
    
    private void initViews() {
        previewView = findViewById(R.id.preview_view);
        switchCameraButton = findViewById(R.id.switch_camera_button);
        scanButton = findViewById(R.id.scan_button);
        backButton = findViewById(R.id.back_button);
        statusText = findViewById(R.id.status_text);
        urlText = findViewById(R.id.url_text);
        barcodeResultPanel = findViewById(R.id.barcode_result_panel);
        barcodeFormatText = findViewById(R.id.barcode_format_text);
        barcodeValueText = findViewById(R.id.barcode_value_text);
        
        switchCameraButton.setOnClickListener(v -> switchCamera());
        scanButton.setOnClickListener(v -> toggleScanning());
        backButton.setOnClickListener(v -> finish());
        
        barcodeResultPanel.setOnClickListener(v -> copyBarcodeToClipboard());
    }
    
    private void checkCameraPermission() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA) 
                == PackageManager.PERMISSION_GRANTED) {
            hasCameraPermission = true;
            initializeCamera();
        } else {
            ActivityCompat.requestPermissions(this,
                    new String[]{Manifest.permission.CAMERA},
                    CAMERA_PERMISSION_REQUEST);
        }
    }
    
    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions,
                                           @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        
        if (requestCode == CAMERA_PERMISSION_REQUEST) {
            if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                hasCameraPermission = true;
                initializeCamera();
            } else {
                Toast.makeText(this, "Camera permission denied", Toast.LENGTH_LONG).show();
                statusText.setText("Permission denied");
            }
        }
    }
    
    private void initializeCamera() {
        if (!hasCameraPermission) {
            return;
        }
        
        cameraService = CameraService.getInstance();
        cameraService.initialize(this);
        cameraService.startCamera(this, previewView);
        
        cameraService.setBarcodeCallback((value, format, formatName) -> {
            runOnUiThread(() -> showBarcodeResult(value, formatName));
        });
        
        updateStatus();
    }
    
    private void toggleScanning() {
        isScanning = !isScanning;
        
        if (cameraService != null) {
            cameraService.setBarcodeScanningEnabled(isScanning);
        }
        
        if (isScanning) {
            scanButton.setText("Stop Scan");
            scanButton.setBackgroundColor(0xFFFF5722);
            barcodeResultPanel.setVisibility(View.GONE);
            Toast.makeText(this, "Scanning...", Toast.LENGTH_SHORT).show();
        } else {
            scanButton.setText("Scan QR");
            scanButton.setBackgroundColor(0xFF6200EE);
        }
        
        updateStatus();
    }
    
    private void showBarcodeResult(String value, String formatName) {
        barcodeFormatText.setText(formatName);
        barcodeValueText.setText(value);
        barcodeResultPanel.setVisibility(View.VISIBLE);
        
        if (hideBarcodeRunnable != null) {
            handler.removeCallbacks(hideBarcodeRunnable);
        }
        
        hideBarcodeRunnable = () -> {
            if (barcodeResultPanel.getVisibility() == View.VISIBLE) {
                barcodeResultPanel.setVisibility(View.GONE);
            }
        };
        handler.postDelayed(hideBarcodeRunnable, 5000);
    }
    
    private void copyBarcodeToClipboard() {
        String value = barcodeValueText.getText().toString();
        if (!value.isEmpty()) {
            ClipboardManager clipboard = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
            ClipData clip = ClipData.newPlainText("barcode", value);
            clipboard.setPrimaryClip(clip);
            Toast.makeText(this, "Copied to clipboard", Toast.LENGTH_SHORT).show();
        }
    }
    
    private void switchCamera() {
        if (cameraService != null) {
            cameraService.switchCamera();
            updateStatus();
        }
    }
    
    private void updateStatus() {
        if (cameraService == null) {
            return;
        }
        
        String camera = cameraService.isCameraRunning() ? "Front" : "Stopped";
        String streaming = cameraService.isStreaming() ? "Yes" : "No";
        String scanning = isScanning ? " | Scanning" : "";
        
        statusText.setText("Camera: " + camera + " | Streaming: " + streaming + scanning);
        urlText.setText("http://localhost:" + cameraService.getServerPort() + "/camera/stream");
    }
    
    @Override
    protected void onResume() {
        super.onResume();
        updateStatus();
    }
    
    @Override
    protected void onPause() {
        super.onPause();
    }
    
    @Override
    protected void onDestroy() {
        super.onDestroy();
        if (closeReceiver != null) {
            unregisterReceiver(closeReceiver);
        }
        if (hideBarcodeRunnable != null) {
            handler.removeCallbacks(hideBarcodeRunnable);
        }
        if (cameraService != null) {
            cameraService.setBarcodeScanningEnabled(false);
            cameraService.stopCamera();
        }
    }
}
