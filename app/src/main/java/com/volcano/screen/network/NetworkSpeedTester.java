package com.volcano.screen.network;

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
 * 支持 USB 和 WiFi 两种连接方式
 */
public class NetworkSpeedTester {
    
    private static final String TAG = "NetworkSpeedTest";
    
    private static final String USB_SERVER_URL = "http://localhost:8765";
    
    private Handler mainHandler;
    private ExecutorService executor;
    private TextView resultText;
    private String serverUrl;
    
    public interface SpeedTestCallback {
        void onPingResult(double avgLatency, double minLatency, double maxLatency);
        void onDownloadResult(double speedMbps);
        void onUploadResult(double speedMbps);
        void onError(String error);
        void onComplete();
    }
    
    public NetworkSpeedTester(TextView resultText) {
        this(resultText, USB_SERVER_URL);
    }
    
    public NetworkSpeedTester(TextView resultText, String serverUrl) {
        this.resultText = resultText;
        this.serverUrl = serverUrl;
        this.mainHandler = new Handler(Looper.getMainLooper());
        this.executor = Executors.newSingleThreadExecutor();
    }
    
    public void startDualTest(String usbUrl, String wifiUrl, SpeedTestCallback callback) {
        executor.execute(() -> {
            appendResult("══════════════════════════════\n");
            appendResult("  网络速度测试 (双通道)\n");
            appendResult("══════════════════════════════\n\n");
            
            runSingleTest("USB", usbUrl, callback);
            
            appendResult("\n");
            
            runSingleTest("WiFi", wifiUrl, callback);
            
            appendResult("══════════════════════════════\n");
            appendResult("  全部测试完成!\n");
            appendResult("══════════════════════════════\n");
            
            if (callback != null) {
                mainHandler.post(callback::onComplete);
            }
        });
    }
    
    private void runSingleTest(String connType, String url, SpeedTestCallback callback) {
        appendResult("──────────────────────────────\n");
        appendResult("【" + connType + " 测试】\n");
        appendResult("服务器: " + url + "\n\n");
        
        try {
            appendResult("  Ping 测试...\n");
            PingResult pingResult = testPing(url, 5);
            if (pingResult != null) {
                String pingInfo = String.format(
                    "  平均: %.2f ms | 最小: %.2f ms | 最大: %.2f ms | 抖动: %.2f ms\n\n",
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
            } else {
                appendResult("  ❌ Ping 测试失败，" + connType + " 不可用\n\n");
                return;
            }
            
            appendResult("  下载测试...\n");
            double downloadSpeed = testDownloadSpeed(url, 5);
            if (downloadSpeed > 0) {
                String downloadInfo = String.format(
                    "  下载速度: %.2f Mbps (%.2f MB/s)\n\n",
                    downloadSpeed, downloadSpeed / 8
                );
                appendResult(downloadInfo);
                if (callback != null) {
                    mainHandler.post(() -> callback.onDownloadResult(downloadSpeed));
                }
            } else {
                appendResult("  ❌ 下载测试失败\n\n");
                return;
            }
            
            appendResult("  上传测试...\n");
            double uploadSpeed = testUploadSpeed(url, 10);
            if (uploadSpeed > 0) {
                String uploadInfo = String.format(
                    "  上传速度: %.2f Mbps (%.2f MB/s)\n\n",
                    uploadSpeed, uploadSpeed / 8
                );
                appendResult(uploadInfo);
                if (callback != null) {
                    mainHandler.post(() -> callback.onUploadResult(uploadSpeed));
                }
            } else {
                appendResult("  ❌ 上传测试失败\n\n");
            }
            
            appendResult("  ✅ " + connType + " 测试完成\n");
        } catch (Exception e) {
            Log.e(TAG, connType + "测试出错", e);
            appendResult("  ❌ " + connType + " 测试出错: " + e.getMessage() + "\n");
            if (callback != null) {
                mainHandler.post(() -> callback.onError(e.getMessage()));
            }
        }
    }
    
    public void startFullTest(SpeedTestCallback callback) {
        executor.execute(() -> {
            try {
                boolean isUsb = serverUrl.contains("localhost") || serverUrl.contains("127.0.0.1");
                String connType = isUsb ? "USB" : "WiFi";
                appendResult("开始网络速度测试 (" + connType + ")...\n");
                appendResult("服务器: " + serverUrl + "\n\n");
                
                appendResult("正在进行 Ping 测试...\n");
                PingResult pingResult = testPing(serverUrl, 5);
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
                } else {
                    appendResult("  Ping 测试失败，请检查连接\n\n");
                }
                
                appendResult("正在进行下载测试...\n");
                double downloadSpeed = testDownloadSpeed(serverUrl, 5);
                if (downloadSpeed > 0) {
                    String downloadInfo = String.format(
                        "  下载速度: %.2f Mbps (%.2f MB/s)\n\n",
                        downloadSpeed, downloadSpeed / 8
                    );
                    appendResult(downloadInfo);
                    
                    if (callback != null) {
                        mainHandler.post(() -> callback.onDownloadResult(downloadSpeed));
                    }
                } else {
                    appendResult("  下载测试失败\n\n");
                }
                
                appendResult("正在进行上传测试...\n");
                double uploadSpeed = testUploadSpeed(serverUrl, 10);
                if (uploadSpeed > 0) {
                    String uploadInfo = String.format(
                        "  上传速度: %.2f Mbps (%.2f MB/s)\n\n",
                        uploadSpeed, uploadSpeed / 8
                    );
                    appendResult(uploadInfo);
                    
                    if (callback != null) {
                        mainHandler.post(() -> callback.onUploadResult(uploadSpeed));
                    }
                } else {
                    appendResult("  上传测试失败\n\n");
                }
                
                appendResult("========================================\n");
                appendResult("测试完成! (" + connType + ")\n");
                
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
    
    private PingResult testPing(String url, int count) {
        List<Double> latencies = new ArrayList<>();
        
        for (int i = 0; i < count; i++) {
            try {
                long startTime = System.currentTimeMillis();
                URL pingUrl = new URL(url + "/ping");
                HttpURLConnection conn = (HttpURLConnection) pingUrl.openConnection();
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
    
    private double testDownloadSpeed(String url, int durationSeconds) {
        try {
            long startTime = System.currentTimeMillis();
            long totalBytes = 0;
            
            while (System.currentTimeMillis() - startTime < durationSeconds * 1000) {
                URL dlUrl = new URL(url + "/download");
                HttpURLConnection conn = (HttpURLConnection) dlUrl.openConnection();
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
    
    private double testUploadSpeed(String url, int dataSizeMB) {
        try {
            byte[] data = new byte[dataSizeMB * 1024 * 1024];
            for (int i = 0; i < data.length; i++) {
                data[i] = (byte) ('x');
            }
            
            long startTime = System.currentTimeMillis();
            
            URL upUrl = new URL(url + "/upload");
            HttpURLConnection conn = (HttpURLConnection) upUrl.openConnection();
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
            
            if (elapsed <= 0) {
                return 0;
            }
            
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
    
    private void appendResult(String text) {
        mainHandler.post(() -> {
            if (resultText != null) {
                resultText.append(text);
            }
        });
    }
    
    public void destroy() {
        executor.shutdownNow();
    }
}
