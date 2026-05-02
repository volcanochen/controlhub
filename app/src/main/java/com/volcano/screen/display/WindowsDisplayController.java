package com.volcano.screen.display;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

/**
 * USB Display Controller - via ADB Reverse
 * Uses ADB reverse port forwarding technique
 * 
 * How it works:
 * 1. Phone connects to Windows via USB
 * 2. Windows side usb_display_control.py establishes ADB reverse
 * 3. Phone makes HTTP requests to localhost:8765
 * 4. Requests are forwarded via ADB reverse to Windows
 * 5. Windows calls DisplaySwitch.exe to change display
 */
public class WindowsDisplayController implements DisplayController {
    
    // Display modes
    public static final int MODE_PRIMARY_ONLY = 1;      // Primary display only
    public static final int MODE_SECONDARY_ONLY = 2;    // Secondary display only
    public static final int MODE_EXTENDED = 3;          // Extended mode
    public static final int MODE_DUPLICATE = 4;         // Duplicate mode
    
    // Phone connects via ADB reverse to Windows server
    private static final String SERVER_URL = "http://localhost:8765";
    
    /**
     * Set display mode
     * @param mode display mode
     */
    @Override
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
     * Send HTTP command to Windows
     * Forwarded via ADB reverse to localhost
     */
    private void sendHttpCommand(String command) throws Exception {
        URL url = new URL(SERVER_URL + "/");
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        
        try {
            conn.setRequestMethod("POST");
            conn.setRequestProperty("Content-Type", "application/json");
            conn.setConnectTimeout(10000);  // 10 second timeout
            conn.setReadTimeout(15000);     // 15 second PC operation timeout
            conn.setDoOutput(true);
            
            // Build JSON request body
            String jsonBody = "{\"command\":\"" + command + "\"}";
            
            try (OutputStream os = conn.getOutputStream()) {
                byte[] input = jsonBody.getBytes(StandardCharsets.UTF_8);
                os.write(input, 0, input.length);
            }
            
            // Get response
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
                
                throw new Exception("Command failed (HTTP " + responseCode + "): " + error.toString());
            }
            
            // Read response
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
     * Get current display mode
     * @return current mode
     */
    @Override
    public int getCurrentMode() throws Exception {
        // GET request to get status
        URL url = new URL(SERVER_URL + "/status");
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        
        try {
            conn.setRequestMethod("GET");
            conn.setConnectTimeout(10000);  // 10 second timeout
            conn.setReadTimeout(10000);     // 10 second timeout
            
            int responseCode = conn.getResponseCode();
            
            if (responseCode != 200) {
                throw new Exception("Server not reachable (HTTP " + responseCode + ")");
            }
            
            // Read response
            BufferedReader reader = new BufferedReader(
                new InputStreamReader(conn.getInputStream(), StandardCharsets.UTF_8)
            );
            StringBuilder response = new StringBuilder();
            String line;
            
            while ((line = reader.readLine()) != null) {
                response.append(line);
            }
            reader.close();
            
            // Parse JSON response
            String responseStr = response.toString();
            
            // Extract mode field
            // {"status": "ok", "mode": 1, "mode_name": "internal", ...}
            try {
                // Simple mode value parsing
                int modeStart = responseStr.indexOf("\"mode\":");
                if (modeStart != -1) {
                    int commaPos = responseStr.indexOf(",", modeStart);
                    String modePart = responseStr.substring(modeStart + 7, commaPos).trim();
                    int mode = Integer.parseInt(modePart);
                    
                    // Validate mode
                    if (mode >= 0 && mode <= 4) {
                        return mode;
                    }
                }
            } catch (Exception e) {
                e.printStackTrace();
            }
            
            // Default to extended mode
            return MODE_EXTENDED;
            
        } finally {
            conn.disconnect();
        }
    }
    
    /**
     * Close connection
     */
    @Override
    public void close() {
        // No special cleanup needed
    }
    
    /**
     * Check if USB connection is available
     * @return true if connected
     */
    @Override
    public boolean isAvailable() {
        try {
            getCurrentMode();
            return true;
        } catch (Exception e) {
            return false;
        }
    }
    
    /**
     * Get connection type name
     * @return "USB"
     */
    @Override
    public String getConnectionType() {
        return "USB";
    }
    
    /**
     * 检查USB连接是否可用
     * @return true if connected
     */
    @Override
    public boolean isAvailable() {
        try {
            getCurrentMode();
            return true;
        } catch (Exception e) {
            return false;
        }
    }
    
    /**
     * 获取连接类型名称
     * @return "USB"
     */
    @Override
    public String getConnectionType() {
        return "USB";
    }
}
