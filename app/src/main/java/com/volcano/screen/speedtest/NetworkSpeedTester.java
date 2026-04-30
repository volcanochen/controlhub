package com.volcano.screen.speedtest;

import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.widget.TextView;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * 网络速度测试器
 * 使用USB连接进行测试
 */
public class NetworkSpeedTester {
    
    private static final String TAG = "NetworkSpeedTest";
    
    // USB连接使用ADB reverse进行端口转发
    private static final String SERVER_URL = "http://localhost:8765";
    
    private Handler mainHandler;
    private ExecutorService executor;
    private TextView resultText;
    
    public interface SpeedTestCallback {
        void onPingResult(double avgLatency, double minLatency, double maxLatency);
        void onDownloadResult(double speedMbps);
        void onUploadResult(double speedMbps);
        void onError(String error);
        void onComplete();
    }
    
    public NetworkSpeedTester(TextView resultText) {
        this.resultText = resultText;
        this.mainHandler = new Handler(Looper.getMainLooper());
        this.executor = Executors.newSingleThreadExecutor();
    }
    
    /**
     * 开始完整测试
     */
    public void startFullTest(SpeedTestCallback callback) {
        executor.execute(() -> {
            try {
                appendResult("开始网络速度测试 (USB连接)...\n\n");
                
                // 1. Ping测试
                appendResult("正在进行 Ping 测试...\n");
                PingResult pingResult = testPing(5);
                if (pingResult != null) {
                    String pingInfo = String.format(
                        "  平均: %.2f ms\n  最小: %.2f ms\n  最大: %.2f ms\n  抖动: %.2f ms\n\n",
                        pingResult.avgLatency, pingResult.minLatency, 
                        pingResult.maxLatency, pingResult.jitter
                    );
                    appendResult(pingInfo);
                    
                    if (callback != null) {
                        mainHandler.post(() -> 
                            callback.onPingResult(pingResult.avgLatency, 
                                pingResult.minLatency, pingResult.maxLatency)
                        );
                    }
                }
                
                // 2. 下载测试
                appendResult("正在进行下载测试...\n");
                double downloadSpeed = testDownloadSpeed(5);
                if (downloadSpeed > 0) {
                    String downloadInfo = String.format(
                        "  下载速度: %.2f Mbps (%.2f MB/s)\n\n",
                        downloadSpeed, downloadSpeed / 8
                    );
                    appendResult(downloadInfo);
                    
                    if (callback != null) {
                        mainHandler.post(() -> callback.onDownloadResult(downloadSpeed));
                    }
                }
                
                // 3. 上传测试
                appendResult("正在进行上传测试...\n");
                double uploadSpeed = testUploadSpeed(10);
                if (uploadSpeed > 0) {
                    String uploadInfo = String.format(
                        "  上传速度: %.2f Mbps (%.2f MB/s)\n\n",
                        uploadSpeed, uploadSpeed / 8
                    );
                    appendResult(uploadInfo);
                    
                    if (callback != null) {
                        mainHandler.post(() -> callback.onUploadResult(uploadSpeed));
                    }
                }
                
                // 测试完成
                appendResult("=".repeat(40) + "\n");
                appendResult("测试完成!\n");
                
                if (callback != null) {
                    mainHandler.post(callback::onComplete);
                }
                
            } catch (Exception e) {
                Log.e(TAG, "测试出错", e);
                String errorMsg = "测试出错: " + e.getMessage() + "\n";
                appendResult(errorMsg);
                
                if (callback != null) {
                    mainHandler.post(() -> callback.onError(e.getMessage()));
                }
            }
        });
    }
    
    /**
     * Ping测试结果
     */
    private static class PingResult {
        double avgLatency;
        double minLatency;
        double maxLatency;
        double jitter;
        
        PingResult(double avg, double min, double max, double j) {
            avgLatency = avg;
            minLatency = min;
            maxLatency = max;
            jitter = j;
        }
    }
    
    /**
     * Ping测试
     */
    private PingResult testPing(int count) {
        List<Double> latencies = new ArrayList<>();
        
        for (int i = 0; i < count; i++) {
            try {
                long startTime = System.currentTimeMillis();
                URL url = new URL(SERVER_URL + "/ping");
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setConnectTimeout(10000);
                conn.setReadTimeout(10000);
                conn.setRequestMethod("GET");
                
                int responseCode = conn.getResponseCode();
                long endTime = System.currentTimeMillis();
                
                if (responseCode == 200) {
                    double latency = endTime - startTime;
                    latencies.add(latency);
                    Log.d(TAG, "Ping " + (i + 1) + ": " + latency + " ms");
                }
                
                conn.disconnect();
            } catch (Exception e) {
                Log.e(TAG, "Ping测试出错", e);
            }
        }
        
        if (latencies.isEmpty()) {
            return null;
        }
        
        double sum = 0;
        double min = latencies.get(0);
        double max = latencies.get(0);
        
        for (double latency : latencies) {
            sum += latency;
            if (latency < min) min = latency;
            if (latency > max) max = latency;
        }
        
        double avg = sum / latencies.size();
        double jitter = calculateJitter(latencies);
        
        return new PingResult(avg, min, max, jitter);
    }
    
    /**
     * 计算抖动
     */
    private double calculateJitter(List<Double> latencies) {
        if (latencies.size() < 2) {
            return 0;
        }
        
        double sumSquaredDiff = 0;
        double avg = latencies.stream().mapToDouble(Double::doubleValue).average().orElse(0);
        
        for (double latency : latencies) {
            double diff = latency - avg;
            sumSquaredDiff += diff * diff;
        }
        
        return Math.sqrt(sumSquaredDiff / (latencies.size() - 1));
    }
    
    /**
     * 下载速度测试
     */
    private double testDownloadSpeed(int durationSeconds) {
        try {
            long startTime = System.currentTimeMillis();
            long totalBytes = 0;
            
            while (System.currentTimeMillis() - startTime < durationSeconds * 1000) {
                URL url = new URL(SERVER_URL + "/download");
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setConnectTimeout(30000);
                conn.setReadTimeout(30000);
                conn.setRequestMethod("GET");
                
                BufferedReader reader = new BufferedReader(
                    new InputStreamReader(conn.getInputStream(), StandardCharsets.UTF_8)
                );
                
                int bytesRead;
                char[] buffer = new char[8192];
                while ((bytesRead = reader.read(buffer)) != -1) {
                    totalBytes += bytesRead;
                }
                reader.close();
                conn.disconnect();
            }
            
            long elapsed = System.currentTimeMillis() - startTime;
            double elapsedSeconds = elapsed / 1000.0;
            double speedBytesPerSec = totalBytes / elapsedSeconds;
            double speedMbps = (speedBytesPerSec * 8) / 1024 / 1024;
            
            Log.d(TAG, "下载完成: " + totalBytes + " bytes, 耗时: " + elapsed + "ms");
            
            return speedMbps;
            
        } catch (Exception e) {
            Log.e(TAG, "下载测试出错", e);
            return 0;
        }
    }
    
    /**
     * 上传速度测试
     */
    private double testUploadSpeed(int dataSizeMB) {
        try {
            byte[] data = new byte[dataSizeMB * 1024 * 1024];
            // 填充数据
            for (int i = 0; i < data.length; i++) {
                data[i] = (byte) ('x');
            }
            
            long startTime = System.currentTimeMillis();
            
            URL url = new URL(SERVER_URL + "/upload");
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setConnectTimeout(60000);
            conn.setReadTimeout(60000);
            conn.setRequestMethod("POST");
            conn.setDoOutput(true);
            conn.setRequestProperty("Content-Type", "application/octet-stream");
            conn.setRequestProperty("Content-Length", String.valueOf(data.length));
            
            try (OutputStream os = conn.getOutputStream()) {
                os.write(data);
                os.flush();
            }
            
            int responseCode = conn.getResponseCode();
            long elapsed = System.currentTimeMillis() - startTime;
            
            if (responseCode == 200) {
                BufferedReader reader = new BufferedReader(
                    new InputStreamReader(conn.getInputStream(), StandardCharsets.UTF_8)
                );
                StringBuilder response = new StringBuilder();
                String line;
                while ((line = reader.readLine()) != null) {
                    response.append(line);
                }
                reader.close();
                
                Log.d(TAG, "上传响应: " + response.toString());
            }
            
            conn.disconnect();
            
            double elapsedSeconds = elapsed / 1000.0;
            double speedBytesPerSec = data.length / elapsedSeconds;
            double speedMbps = (speedBytesPerSec * 8) / 1024 / 1024;
            
            Log.d(TAG, "上传完成: " + data.length + " bytes, 耗时: " + elapsed + "ms");
            
            return speedMbps;
            
        } catch (Exception e) {
            Log.e(TAG, "上传测试出错", e);
            return 0;
        }
    }
    
    /**
     * 追加结果到UI
     */
    private void appendResult(String text) {
        mainHandler.post(() -> {
            if (resultText != null) {
                resultText.append(text);
            }
        });
    }
    
    /**
     * 销毁
     */
    public void destroy() {
        executor.shutdownNow();
    }
}
