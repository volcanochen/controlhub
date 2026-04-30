package com.volcano.screen.display;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

/**
 * Windows显示控制器 - 通过ADB Reverse进行通信
 * 使用ADB reverse端口转发技术
 * 
 * 工作原理:
 * 1. 手机通过USB连接到Windows电脑
 * 2. 电脑端usb_display_control.py建立ADB reverse
 * 3. 手机通过localhost:8765进行HTTP请求
 * 4. 通过ADB reverse转发请求到电脑
 * 5. 电脑调用DisplaySwitch.exe切换显示
 */
public class WindowsDisplayController {
    
    // 显示模式
    public static final int MODE_PRIMARY_ONLY = 1;      // 仅主屏
    public static final int MODE_SECONDARY_ONLY = 2;    // 仅副屏
    public static final int MODE_EXTENDED = 3;          // 扩展模式
    public static final int MODE_DUPLICATE = 4;         // 复制模式
    
    // 手机通过ADB reverse连接到电脑服务器
    private static final String SERVER_URL = "http://localhost:8765";
    
    /**
     * 设置显示模式
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
     * 发送HTTP命令到电脑
     * 通过ADB reverse转发到localhost
     */
    private void sendHttpCommand(String command) throws Exception {
        URL url = new URL(SERVER_URL + "/");
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        
        try {
            conn.setRequestMethod("POST");
            conn.setRequestProperty("Content-Type", "application/json");
            conn.setConnectTimeout(10000);  // 10秒超时
            conn.setReadTimeout(15000);     // 15秒PC端操作超时
            conn.setDoOutput(true);
            
            // 构建JSON请求体
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
                
                throw new Exception("命令失败 (HTTP " + responseCode + "): " + error.toString());
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
            
        } finally {
            conn.disconnect();
        }
    }
    
    /**
     * 获取当前显示模式
     * @return 当前模式
     */
    public int getCurrentMode() throws Exception {
        // GET请求获取状态
        URL url = new URL(SERVER_URL + "/status");
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        
        try {
            conn.setRequestMethod("GET");
            conn.setConnectTimeout(10000);  // 10秒超时
            conn.setReadTimeout(10000);     // 10秒超时
            
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
            
            // 解析JSON响应
            String responseStr = response.toString();
            
            // 提取mode字段
            // {"status": "ok", "mode": 1, "mode_name": "internal", ...}
            try {
                // 简单解析mode值
                int modeStart = responseStr.indexOf("\"mode\":");
                if (modeStart != -1) {
                    int commaPos = responseStr.indexOf(",", modeStart);
                    String modePart = responseStr.substring(modeStart + 7, commaPos).trim();
                    int mode = Integer.parseInt(modePart);
                    
                    // 验证模式是否有效
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
     * 关闭连接
     */
    public void close() {
        // 不需要特殊清理
    }
}
