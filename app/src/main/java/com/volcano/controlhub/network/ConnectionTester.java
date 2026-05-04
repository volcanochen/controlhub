package com.volcano.controlhub.network;

import android.app.AlertDialog;
import android.content.Context;
import android.graphics.Color;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.widget.TextView;

import com.volcano.controlhub.display.DisplayManager;

import java.util.concurrent.ExecutorService;

public class ConnectionTester {

    private static final String TAG = "ConnectionTester";

    public interface TestCallback {
        void onResult(String result);
    }

    public static void test(Context context, DisplayManager displayManager, ExecutorService executorService) {
        AlertDialog.Builder builder = new AlertDialog.Builder(context);
        builder.setTitle("Connection Test");

        final TextView resultText = new TextView(context);
        resultText.setPadding(50, 50, 50, 50);
        resultText.setTextSize(14);
        resultText.setTextColor(Color.BLACK);
        resultText.setMovementMethod(android.text.method.ScrollingMovementMethod.getInstance());
        resultText.setMinHeight(400);

        builder.setView(resultText);
        builder.setPositiveButton("Close", null);

        final AlertDialog dialog = builder.create();
        resultText.setText("Testing connection...\nPlease wait, may take 10-20 seconds\n");
        dialog.show();

        executorService.execute(() -> {
            StringBuilder result = new StringBuilder();
            result.append("Connection Test Results\n");
            result.append("================\n\n");

            try {
                Log.d(TAG, "Starting USB test...");
                result.append("[1/2] Testing USB connection...\n");
                new Handler(Looper.getMainLooper()).post(() -> resultText.setText(result.toString()));

                boolean usbAvailable = displayManager.isUsbAvailable();
                Log.d(TAG, "USB test result: " + usbAvailable);
                result.append("USB: ").append(usbAvailable ? "Available" : "Not available").append("\n\n");
                new Handler(Looper.getMainLooper()).post(() -> resultText.setText(result.toString()));
            } catch (Exception e) {
                Log.e(TAG, "USB test error", e);
                result.append("USB: Error - ").append(e.getMessage()).append("\n\n");
                new Handler(Looper.getMainLooper()).post(() -> resultText.setText(result.toString()));
            }

            try {
                Log.d(TAG, "Starting WiFi test...");
                result.append("[2/2] Testing WiFi connection...\n");
                new Handler(Looper.getMainLooper()).post(() -> resultText.setText(result.toString()));

                boolean wifiAvailable = displayManager.isWifiAvailable();
                Log.d(TAG, "WiFi test result: " + wifiAvailable);
                result.append("WiFi: ").append(wifiAvailable ? "Available" : "Not available").append("\n\n");
                new Handler(Looper.getMainLooper()).post(() -> resultText.setText(result.toString()));
            } catch (Exception e) {
                Log.e(TAG, "WiFi test error", e);
                result.append("WiFi: Error - ").append(e.getMessage()).append("\n\n");
                new Handler(Looper.getMainLooper()).post(() -> resultText.setText(result.toString()));
            }

            try {
                String currentMode = displayManager.getController().getConnectionType();
                result.append("Current: ").append(currentMode).append("\n");
            } catch (Exception e) {
                result.append("Current: Failed - ").append(e.getMessage()).append("\n");
            }

            new Handler(Looper.getMainLooper()).post(() -> resultText.setText(result.toString()));
        });
    }
}
