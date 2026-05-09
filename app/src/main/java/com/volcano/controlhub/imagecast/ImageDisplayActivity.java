package com.volcano.controlhub.imagecast;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Matrix;
import android.net.Uri;
import android.os.Bundle;
import android.os.Environment;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.view.GestureDetector;
import android.view.MotionEvent;
import android.view.ScaleGestureDetector;
import android.view.WindowManager;
import android.widget.Button;
import android.content.SharedPreferences;
import android.widget.ImageView;
import android.widget.TextView;
import android.widget.Toast;

import com.volcano.controlhub.R;

import java.io.File;
import java.io.FileOutputStream;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class ImageDisplayActivity extends Activity {
    
    private static final String TAG = "ImageDisplay";
    
    private ImageView imageView;
    private TextView statusText;
    private TextView scaleText;
    private Button backBtn;
    private Button openExternalBtn;
    
    private ImageCastingController controller;
    private ExecutorService executorService;
    private Handler mainHandler;
    
    private Matrix matrix;
    private ScaleGestureDetector scaleDetector;
    private GestureDetector gestureDetector;
    
    private float currentScale = 1.0f;
    private float fitScale = 1.0f;
    private float posX = 0f, posY = 0f;
    private float lastTouchX, lastTouchY;
    
    private boolean isFitToScreen = true;
    
    private boolean isPolling = false;
    private double lastUpdateTime = 0;
    private Handler pollHandler;
    private Runnable pollRunnable;
    
    private Bitmap currentBitmap;
    private String currentImageName = null;
    private byte[] currentImageBytes = null;
    
    private int viewWidth, viewHeight;
    
    private float originalBrightness = -1f;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_image_display);
        
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        
        initViews();
        
        controller = new ImageCastingController(this);
        executorService = Executors.newSingleThreadExecutor();
        mainHandler = new Handler(Looper.getMainLooper());
        pollHandler = new Handler(Looper.getMainLooper());
        matrix = new Matrix();
        
        setupGestureDetectors();
        setupPolling();
        
        imageView.post(() -> {
            viewWidth = imageView.getWidth();
            viewHeight = imageView.getHeight();
            refreshImage(true);
        });
    }
    
    private void initViews() {
        imageView = findViewById(R.id.image_display);
        statusText = findViewById(R.id.image_status_text);
        scaleText = findViewById(R.id.scale_text);
        backBtn = findViewById(R.id.back_btn);
        openExternalBtn = findViewById(R.id.open_external_btn);
        
        backBtn.setOnClickListener(v -> finish());
        openExternalBtn.setOnClickListener(v -> openWithExternalViewer());
    }
    
    private void openWithExternalViewer() {
        if (currentImageBytes == null || currentImageBytes.length == 0) {
            Toast.makeText(this, "No image to view", Toast.LENGTH_SHORT).show();
            return;
        }
        
        executorService.execute(() -> {
            try {
                File cacheDir = getExternalFilesDir(Environment.DIRECTORY_PICTURES);
                if (cacheDir == null) {
                    cacheDir = getCacheDir();
                }
                
                String fileName = currentImageName != null ? currentImageName : "shared_image.jpg";
                if (!fileName.toLowerCase().endsWith(".jpg") && !fileName.toLowerCase().endsWith(".png")) {
                    fileName = fileName + ".jpg";
                }
                
                File imageFile = new File(cacheDir, fileName);
                
                try (FileOutputStream fos = new FileOutputStream(imageFile)) {
                    fos.write(currentImageBytes);
                }
                
                Uri uri = androidx.core.content.FileProvider.getUriForFile(
                    this,
                    getPackageName() + ".fileprovider",
                    imageFile
                );
                
                Intent intent = new Intent(Intent.ACTION_VIEW);
                intent.setDataAndType(uri, "image/*");
                intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
                intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                
                startActivity(Intent.createChooser(intent, "View image with"));
                
            } catch (Exception e) {
                Log.e(TAG, "Failed to open external viewer", e);
                mainHandler.post(() -> 
                    Toast.makeText(this, "Failed: " + e.getMessage(), Toast.LENGTH_SHORT).show()
                );
            }
        });
    }
    
    private void setupGestureDetectors() {
        scaleDetector = new ScaleGestureDetector(this, new ScaleGestureDetector.SimpleOnScaleGestureListener() {
            @Override
            public boolean onScale(ScaleGestureDetector detector) {
                float scaleFactor = detector.getScaleFactor();
                float newScale = currentScale * scaleFactor;
                newScale = Math.max(0.1f, Math.min(10.0f, newScale));
                
                float focusX = detector.getFocusX();
                float focusY = detector.getFocusY();
                
                float scaleChange = newScale / currentScale;
                
                posX = focusX - (focusX - posX) * scaleChange;
                posY = focusY - (focusY - posY) * scaleChange;
                
                currentScale = newScale;
                isFitToScreen = false;
                
                updateMatrix();
                sendScaleToServer(currentScale);
                return true;
            }
        });
        
        gestureDetector = new GestureDetector(this, new GestureDetector.SimpleOnGestureListener() {
            @Override
            public boolean onDoubleTap(MotionEvent e) {
                toggleViewMode();
                return true;
            }
            
            @Override
            public boolean onDown(MotionEvent e) {
                return true;
            }
        });
    }
    
    private void toggleViewMode() {
        if (currentBitmap == null) return;
        
        if (isFitToScreen) {
            currentScale = 1.0f;
            isFitToScreen = false;
        } else {
            currentScale = fitScale;
            isFitToScreen = true;
        }
        
        posX = (viewWidth - currentBitmap.getWidth() * currentScale) / 2f;
        posY = (viewHeight - currentBitmap.getHeight() * currentScale) / 2f;
        
        updateMatrix();
        sendScaleToServer(currentScale);
        
        String mode = isFitToScreen ? "Fit screen" : "100%";
        Toast.makeText(this, mode, Toast.LENGTH_SHORT).show();
    }
    
    private void setupPolling() {
        pollRunnable = new Runnable() {
            @Override
            public void run() {
                if (isPolling) {
                    checkForUpdates();
                    pollHandler.postDelayed(this, 2000);
                }
            }
        };
    }
    
    @Override
    protected void onResume() {
        super.onResume();
        isPolling = true;
        pollHandler.post(pollRunnable);
        
        restoreBrightness();
    }
    
    @Override
    protected void onPause() {
        super.onPause();
        isPolling = false;
        pollHandler.removeCallbacks(pollRunnable);
    }
    
    private void restoreBrightness() {
        WindowManager.LayoutParams params = getWindow().getAttributes();
        if (originalBrightness < 0) {
            originalBrightness = params.screenBrightness;
            if (originalBrightness < 0) {
                originalBrightness = 1.0f;
            }
        }
        params.screenBrightness = 1.0f;
        getWindow().setAttributes(params);
    }
    
    @Override
    public boolean onTouchEvent(MotionEvent event) {
        scaleDetector.onTouchEvent(event);
        gestureDetector.onTouchEvent(event);
        
        if (event.getPointerCount() == 1 && !scaleDetector.isInProgress()) {
            handleDrag(event);
        }
        
        return true;
    }
    
    private void handleDrag(MotionEvent event) {
        switch (event.getAction()) {
            case MotionEvent.ACTION_DOWN:
                lastTouchX = event.getX();
                lastTouchY = event.getY();
                break;
                
            case MotionEvent.ACTION_MOVE:
                float dx = event.getX() - lastTouchX;
                float dy = event.getY() - lastTouchY;
                
                posX += dx;
                posY += dy;
                
                lastTouchX = event.getX();
                lastTouchY = event.getY();
                
                updateMatrix();
                break;
        }
    }
    
    private void updateMatrix() {
        if (currentBitmap == null) return;
        
        matrix.reset();
        matrix.postScale(currentScale, currentScale);
        matrix.postTranslate(posX, posY);
        
        imageView.setImageMatrix(matrix);
        scaleText.setText(String.format("%.1fx", currentScale / fitScale));
    }
    
    private void refreshImage(boolean force) {
        mainHandler.post(() -> statusText.setText("Loading..."));
        
        executorService.execute(() -> {
            try {
                ImageCastingController.ImageStatus status = controller.getImageStatus();
                Log.d(TAG, "Status: hasImage=" + status.hasImage + " name=" + status.imageName);
                
                if (!force && status.lastUpdate > 0 && status.lastUpdate == lastUpdateTime) {
                    Log.d(TAG, "Same image, skip reload");
                    return;
                }
                
                lastUpdateTime = status.lastUpdate;
                
                if (status.hasImage) {
                    byte[] imageBytes = controller.downloadImageBytes();
                    Log.d(TAG, "Downloaded: " + imageBytes.length + " bytes");
                    
                    final Bitmap bitmap = BitmapFactory.decodeByteArray(imageBytes, 0, imageBytes.length);
                    
                    if (bitmap != null) {
                        Log.d(TAG, "Decoded bitmap: " + bitmap.getWidth() + "x" + bitmap.getHeight());
                        mainHandler.post(() -> {
                            if (currentBitmap != null && !currentBitmap.isRecycled()) {
                                currentBitmap.recycle();
                            }
                            currentBitmap = bitmap;
                            currentImageBytes = imageBytes;
                            currentImageName = status.imageName;
                            
                            viewWidth = imageView.getWidth();
                            viewHeight = imageView.getHeight();
                            
                            fitScale = Math.min(
                                (float) viewWidth / bitmap.getWidth(),
                                (float) viewHeight / bitmap.getHeight()
                            );
                            
                            if (isFitToScreen || force) {
                                currentScale = fitScale;
                                isFitToScreen = true;
                            }
                            
                            posX = (viewWidth - bitmap.getWidth() * currentScale) / 2f;
                            posY = (viewHeight - bitmap.getHeight() * currentScale) / 2f;
                            
                            imageView.setImageBitmap(bitmap);
                            statusText.setText(status.imageName != null ? status.imageName : "Image");
                            updateMatrix();
                        });
                    } else {
                        Log.e(TAG, "Failed to decode bitmap");
                        mainHandler.post(() -> statusText.setText("Decode failed"));
                    }
                } else {
                    mainHandler.post(() -> {
                        statusText.setText("No image");
                        imageView.setImageBitmap(null);
                        currentImageName = null;
                        currentImageBytes = null;
                        finish();
                    });
                }
                
            } catch (Exception e) {
                Log.e(TAG, "refreshImage error", e);
                mainHandler.post(() -> {
                    statusText.setText("Error: " + e.getMessage());
                    Toast.makeText(ImageDisplayActivity.this, 
                        "Connection error: " + e.getMessage(), Toast.LENGTH_LONG).show();
                });
            }
        });
    }
    
    private void checkForUpdates() {
        executorService.execute(() -> {
            try {
                ImageCastingController.ImageStatus status = controller.getImageStatus();
                
                if (status.closeWindow) {
                    Log.d(TAG, "Close window requested by server");
                    controller.ackCloseWindow();
                    mainHandler.post(() -> finish());
                    return;
                }
                
                ImageCastingController.PollResult result = controller.pollUpdates(lastUpdateTime);
                Log.d(TAG, "Poll: hasUpdate=" + result.hasUpdate);
                
                if (result.hasUpdate && result.state != null) {
                    Log.d(TAG, "Update detected: hasImage=" + result.state.hasImage);
                    if (result.state.hasImage) {
                        mainHandler.post(() -> refreshImage(false));
                    } else {
                        mainHandler.post(() -> {
                            if (currentBitmap != null && !currentBitmap.isRecycled()) {
                                currentBitmap.recycle();
                            }
                            currentBitmap = null;
                            currentImageName = null;
                            currentImageBytes = null;
                            imageView.setImageDrawable(null);
                            statusText.setText("No image");
                            finish();
                        });
                    }
                    
                    if (result.state.scaleLevel != currentScale / fitScale) {
                        final float newScale = result.state.scaleLevel * fitScale;
                        mainHandler.post(() -> {
                            currentScale = newScale;
                            isFitToScreen = false;
                            if (currentBitmap != null) {
                                posX = (viewWidth - currentBitmap.getWidth() * currentScale) / 2f;
                                posY = (viewHeight - currentBitmap.getHeight() * currentScale) / 2f;
                            }
                            updateMatrix();
                        });
                    }
                }
                
            } catch (Exception e) {
                Log.d(TAG, "Poll error: " + e.getMessage());
            }
        });
    }
    
    private void sendScaleToServer(float scale) {
        executorService.execute(() -> {
            try {
                float serverScale = scale / fitScale;
                controller.setScale(serverScale);
            } catch (Exception e) {
                Log.d(TAG, "sendScale error: " + e.getMessage());
            }
        });
    }
    
    @Override
    protected void onDestroy() {
        super.onDestroy();
        if (currentBitmap != null && !currentBitmap.isRecycled()) {
            currentBitmap.recycle();
            currentBitmap = null;
        }
        if (executorService != null) {
            executorService.shutdown();
        }
        pollHandler.removeCallbacks(pollRunnable);
    }
}
