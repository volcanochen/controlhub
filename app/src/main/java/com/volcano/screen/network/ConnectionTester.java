package com.volcano.screen.network;

import android.app.AlertDialog;
import android.content.Context;
import android.graphics.Color;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.widget.TextView;

import com.volcano.screen.display.DisplayManager;

import java.util.concurrent.ExecutorService;

public class ConnectionTester {

    private static final String TAG = "ConnectionTester";

    public interface TestCallback {
        void onResult(String result);
    }

    public static void test(Context context, DisplayManager displayManager, ExecutorService executorService) {
        AlertDialog.Builder builder = new AlertDialog.Builder(context);
        builder.setTitle("连接测试");

        final TextView resultText = new TextView(context);
        resultText.setPadding(50, 50, 50, 50);
        resultText.setTextSize(14);
        resultText.setTextColor(Color.BLACK);
        resultText.setMovementMethod(android.text.method.ScrollingMovementMethod.getInstance());
        resultText.setMinHeight(400);

        builder.setView(resultText);
        builder.setPositiveButton("关闭", null);

        final AlertDialog dialog = builder.create();
        resultText.setText("正在测试连接...\n请稍候，可能需要10-20秒\n");
        dialog.show();

        executorService.execute(() -> {
            StringBuilder result = new StringBuilder();
            result.append("连接测试结果\n");
            result.append("================\n\n");

            try {
                Log.d(TAG, "Starting USB test...");
                result.append("[1/2] 测试 USB 连接...\n");
                new Handler(Looper.getMainLooper()).post(() -> resultText.setText(result.toString()));

                boolean usbAvailable = displayManager.isUsbAvailable();
                Log.d(TAG, "USB test result: " + usbAvailable);
                result.append("USB 连接: ").append(usbAvailable ? "✅ 可用" : "❌ 不可用").append("\n\n");
                new Handler(Looper.getMainLooper()).post(() -> resultText.setText(result.toString()));
            } catch (Exception e) {
                Log.e(TAG, "USB test error", e);
                result.append("USB 连接: ❌ 错误 - ").append(e.getMessage()).append("\n\n");
                new Handler(Looper.getMainLooper()).post(() -> resultText.setText(result.toString()));
            }

            try {
                Log.d(TAG, "Starting WiFi test...");
                result.append("[2/2] 测试 WiFi 连接...\n");
                new Handler(Looper.getMainLooper()).post(() -> resultText.setText(result.toString()));

                boolean wifiAvailable = displayManager.isWifiAvailable();
                Log.d(TAG, "WiFi test result: " + wifiAvailable);
                result.append("WiFi 连接: ").append(wifiAvailable ? "✅ 可用" : "❌ 不可用").append("\n\n");
                new Handler(Looper.getMainLooper()).post(() -> resultText.setText(result.toString()));
            } catch (Exception e) {
                Log.e(TAG, "WiFi test error", e);
                result.append("WiFi 连接: ❌ 错误 - ").append(e.getMessage()).append("\n\n");
                new Handler(Looper.getMainLooper()).post(() -> resultText.setText(result.toString()));
            }

            try {
                String currentMode = displayManager.getController().getConnectionType();
                result.append("当前使用: ").append(currentMode).append("\n");
            } catch (Exception e) {
                result.append("当前使用: 获取失败 - ").append(e.getMessage()).append("\n");
            }

            new Handler(Looper.getMainLooper()).post(() -> resultText.setText(result.toString()));
        });
    }
}
