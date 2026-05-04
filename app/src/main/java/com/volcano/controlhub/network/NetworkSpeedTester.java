package com.volcano.controlhub.network;

import android.content.Context;
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

public class NetworkSpeedTester {
    
    private static final String TAG = "NetworkSpeedTest";
    
    private Handler mainHandler;
    private ExecutorService executor;
    private TextView resultText;
    private ChannelManager channelManager;
    
    public interface SpeedTestCallback {
        void onPingResult(double avgLatency, double minLatency, double maxLatency);
        void onDownloadResult(double speedMbps);
        void onUploadResult(double speedMbps);
        void onError(String error);
        void onComplete();
    }
    
    public NetworkSpeedTester(Context context, TextView resultText) {
        this.resultText = resultText;
        this.channelManager = ChannelManager.getInstance(context);
        this.mainHandler = new Handler(Looper.getMainLooper());
        this.executor = Executors.newSingleThreadExecutor();
    }
    
    public NetworkSpeedTester(Context context, TextView resultText, String serverUrl) {
        this(context, resultText);
    }
    
    public String getUsbUrl() {
        return channelManager.getUsbUrl();
    }
    
    public String getWifiUrl() {
        return channelManager.getWifiUrl();
    }
    
    public String getServerUrl() {
        return channelManager.getServerUrl();
    }
    
    public void startDualTest(String usbUrl, String wifiUrl, SpeedTestCallback callback) {
        executor.execute(() -> {
            appendResult("══════════════════════════════\n");
            appendResult("  Network Speed Test (Dual)\n");
            appendResult("══════════════════════════════\n\n");
            
            runSingleTest("USB", usbUrl, callback);
            
            appendResult("\n");
            
            runSingleTest("WiFi", wifiUrl, callback);
            
            appendResult("══════════════════════════════\n");
            appendResult("  All tests completed!\n");
            appendResult("══════════════════════════════\n");
            
            if (callback != null) {
                mainHandler.post(callback::onComplete);
            }
        });
    }
    
    private void runSingleTest(String connType, String url, SpeedTestCallback callback) {
        appendResult("──────────────────────────────\n");
        appendResult("[" + connType + " Test]\n");
        appendResult("Server: " + url + "\n\n");
        
        try {
            appendResult("  Ping test...\n");
            PingResult pingResult = testPing(url, 5);
            if (pingResult != null) {
                String pingInfo = String.format(
                    "  Avg: %.2f ms | Min: %.2f ms | Max: %.2f ms | Jitter: %.2f ms\n\n",
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
                appendResult("  Ping test failed, " + connType + " not available\n\n");
                return;
            }
            
            appendResult("  Download test...\n");
            double downloadSpeed = testDownloadSpeed(url, 5);
            if (downloadSpeed > 0) {
                String downloadInfo = String.format(
                    "  Download: %.2f Mbps (%.2f MB/s)\n\n",
                    downloadSpeed, downloadSpeed / 8
                );
                appendResult(downloadInfo);
                if (callback != null) {
                    mainHandler.post(() -> callback.onDownloadResult(downloadSpeed));
                }
            } else {
                appendResult("  Download test failed\n\n");
                return;
            }
            
            appendResult("  Upload test...\n");
            double uploadSpeed = testUploadSpeed(url, 10);
            if (uploadSpeed > 0) {
                String uploadInfo = String.format(
                    "  Upload: %.2f Mbps (%.2f MB/s)\n\n",
                    uploadSpeed, uploadSpeed / 8
                );
                appendResult(uploadInfo);
                if (callback != null) {
                    mainHandler.post(() -> callback.onUploadResult(uploadSpeed));
                }
            } else {
                appendResult("  Upload test failed\n\n");
            }
            
            appendResult("  " + connType + " test completed\n");
        } catch (Exception e) {
            Log.e(TAG, connType + " test error", e);
            appendResult("  " + connType + " test error: " + e.getMessage() + "\n");
            if (callback != null) {
                mainHandler.post(() -> callback.onError(e.getMessage()));
            }
        }
    }
    
    public void startFullTest(SpeedTestCallback callback) {
        executor.execute(() -> {
            try {
                String url = getServerUrl();
                boolean isUsb = url.contains("localhost") || url.contains("127.0.0.1");
                String connType = isUsb ? "USB" : "WiFi";
                appendResult("Starting network speed test (" + connType + ")...\n");
                appendResult("Server: " + url + "\n\n");
                
                appendResult("Running Ping test...\n");
                PingResult pingResult = testPing(url, 5);
                if (pingResult != null) {
                    String pingInfo = String.format(
                        "  Avg: %.2f ms\n  Min: %.2f ms\n  Max: %.2f ms\n  Jitter: %.2f ms\n\n",
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
                    appendResult("  Ping test failed, check connection\n\n");
                }
                
                appendResult("Running Download test...\n");
                double downloadSpeed = testDownloadSpeed(url, 5);
                if (downloadSpeed > 0) {
                    String downloadInfo = String.format(
                        "  Download: %.2f Mbps (%.2f MB/s)\n\n",
                        downloadSpeed, downloadSpeed / 8
                    );
                    appendResult(downloadInfo);
                    
                    if (callback != null) {
                        mainHandler.post(() -> callback.onDownloadResult(downloadSpeed));
                    }
                } else {
                    appendResult("  Download test failed\n\n");
                }
                
                appendResult("Running Upload test...\n");
                double uploadSpeed = testUploadSpeed(url, 10);
                if (uploadSpeed > 0) {
                    String uploadInfo = String.format(
                        "  Upload: %.2f Mbps (%.2f MB/s)\n\n",
                        uploadSpeed, uploadSpeed / 8
                    );
                    appendResult(uploadInfo);
                    
                    if (callback != null) {
                        mainHandler.post(() -> callback.onUploadResult(uploadSpeed));
                    }
                } else {
                    appendResult("  Upload test failed\n\n");
                }
                
                appendResult("========================================\n");
                appendResult("Test completed! (" + connType + ")\n");
                
                if (callback != null) {
                    mainHandler.post(callback::onComplete);
                }
                
            } catch (Exception e) {
                Log.e(TAG, "Test error", e);
                String errorMsg = "Test error: " + e.getMessage() + "\n";
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
                Log.e(TAG, "Ping test error", e);
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
            
            Log.d(TAG, "Download completed: " + totalBytes + " bytes, elapsed: " + elapsed + "ms");
            
            return speedMbps;
            
        } catch (Exception e) {
            Log.e(TAG, "Download test error", e);
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
                
                Log.d(TAG, "Upload response: " + response.toString());
            }
            
            conn.disconnect();
            
            if (elapsed <= 0) {
                return 0;
            }
            
            double elapsedSeconds = elapsed / 1000.0;
            double speedBytesPerSec = data.length / elapsedSeconds;
            double speedMbps = (speedBytesPerSec * 8) / 1024 / 1024;
            
            Log.d(TAG, "Upload completed: " + data.length + " bytes, elapsed: " + elapsed + "ms");
            
            return speedMbps;
            
        } catch (Exception e) {
            Log.e(TAG, "Upload test error", e);
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
