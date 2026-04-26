package com.example.clockapp;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

/**
 * Windows 显示器控制器（ADB Reverse 通道版本）
 * 通过 ADB reverse 功能建立手机到电脑的通信通道
 * 
 * 工作原理：
 * 1. 手机通过 USB 连接 Windows 电脑
 * 2. 电脑运行 usb_display_control.py 建立 ADB reverse
 * 3. 手机通过 localhost:8765 发送 HTTP 请求
 * 4. ADB reverse 将请求转发到电脑
 * 5. 电脑接收请求并执行 DisplaySwitch.exe
 */
public class WindowsDisplayController {
    
    // 显示模式常量
    public static final int MODE_PRIMARY_ONLY = 1;      // 仅第一屏
    public static final int MODE_SECONDARY_ONLY = 2;    // 仅第二屏
    public static final int MODE_EXTENDED = 3;          // 扩展模式（双屏）
    public static final int MODE_DUPLICATE = 4;         // 复制模式
    
    // 服务端地址（通过 ADB reverse 连接到电脑）
    private static final String SERVER_URL = "http://localhost:8765";
    
    /**
     * 设置显示器模式
     * @param mode 显示模式
     */
    public void setDisplayMode(int mode) throws Exception {
        String command = "";
        
        switch (mode) {
            case MODE_PRIMARY_ONLY:
                command = "internal";
                break;
            case MODE_SECONDARY_ONLY:
                command = "external";
                break;
            case MODE_EXTENDED:
                command = "extend";
                break;
            case MODE_DUPLICATE:
                command = "clone";
                break;
        }
        
        if (!command.isEmpty()) {
            sendHttpCommand(command);
        }
    }
    
    /**
     * 发送 HTTP 命令到电脑
     * 通过 ADB reverse 通道，localhost 会连接到电脑
     */
    private void sendHttpCommand(String command) throws Exception {
        URL url = new URL(SERVER_URL + "/");
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        
        try {
            conn.setRequestMethod("POST");
            conn.setRequestProperty("Content-Type", "application/json");
            conn.setConnectTimeout(5000);
            conn.setReadTimeout(5000);
            conn.setDoOutput(true);
            
            // 构建 JSON 请求体
            String jsonBody = "{\"command\":\"" + command + "\"}";
            
            try (OutputStream os = conn.getOutputStream()) {
                byte[] input = jsonBody.getBytes(StandardCharsets.UTF_8);
                os.write(input, 0, input.length);
            }
            
            // 获取响应
            int responseCode = conn.getResponseCode();
            
            if (responseCode != 200) {
                BufferedReader errorReader = new BufferedReader(
                    new InputStreamReader(conn.getErrorStream(), StandardCharsets.UTF_8)
                );
                StringBuilder error = new StringBuilder();
                String line;
                
                while ((line = errorReader.readLine()) != null) {
                    error.append(line);
                }
                errorReader.close();
                
                throw new Exception("命令执行失败 (HTTP " + responseCode + "): " + error.toString());
            }
            
            // 读取成功响应
            BufferedReader reader = new BufferedReader(
                new InputStreamReader(conn.getInputStream(), StandardCharsets.UTF_8)
            );
            StringBuilder response = new StringBuilder();
            String line;
            
            while ((line = reader.readLine()) != null) {
                response.append(line);
            }
            reader.close();
            
        } finally {
            conn.disconnect();
        }
    }
    
    /**
     * 获取当前显示器模式
     * @return 当前模式
     */
    public int getCurrentMode() throws Exception {
        // 先发送简单的 GET 请求检查服务器是否可达
        URL url = new URL(SERVER_URL + "/status");
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        
        try {
            conn.setRequestMethod("GET");
            conn.setConnectTimeout(5000);  // 5 秒超时
            conn.setReadTimeout(5000);
            
            int responseCode = conn.getResponseCode();
            
            if (responseCode != 200) {
                throw new Exception("Server not reachable (HTTP " + responseCode + ")");
            }
            
            // 读取响应
            BufferedReader reader = new BufferedReader(
                new InputStreamReader(conn.getInputStream(), StandardCharsets.UTF_8)
            );
            StringBuilder response = new StringBuilder();
            String line;
            
            while ((line = reader.readLine()) != null) {
                response.append(line);
            }
            reader.close();
            
            // 解析 JSON 响应
            String responseStr = response.toString();
            
            // 解析 mode 字段（整数格式）
            // 响应格式：{"status": "ok", "mode": 1, "mode_name": "internal", ...}
            try {
                // 简单字符串匹配提取 mode 值
                int modeStart = responseStr.indexOf("\"mode\":");
                if (modeStart != -1) {
                    int commaPos = responseStr.indexOf(",", modeStart);
                    String modePart = responseStr.substring(modeStart + 7, commaPos).trim();
                    int mode = Integer.parseInt(modePart);
                    
                    // 验证模式值范围
                    if (mode >= 0 && mode <= 4) {
                        return mode;
                    }
                }
            } catch (Exception e) {
                e.printStackTrace();
            }
            
            // 默认返回扩展模式
            return MODE_EXTENDED;
            
        } finally {
            conn.disconnect();
        }
    }
    
    /**
     * 关闭控制器
     */
    public void close() {
        // 无状态，不需要特别处理
    }
}
