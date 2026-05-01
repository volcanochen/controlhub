package com.volcano.screen.display;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

/**
 * WiFi Display Controller
 * Communicates with display server via WiFi network
 */
public class WifiDisplayController implements DisplayController {
    
    public static final int MODE_PRIMARY_ONLY = 1;
    public static final int MODE_SECONDARY_ONLY = 2;
    public static final int MODE_EXTENDED = 3;
    public static final int MODE_DUPLICATE = 4;
    
    private String serverAddress;
    private int serverPort;
    
    public WifiDisplayController(String serverAddress, int serverPort) {
        this.serverAddress = serverAddress;
        this.serverPort = serverPort;
    }
    
    public WifiDisplayController(String serverAddress) {
        this(serverAddress, 8765);
    }
    
    private String getBaseUrl() {
        return "http://" + serverAddress + ":" + serverPort;
    }
    
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
    
    private void sendHttpCommand(String command) throws Exception {
        URL url = new URL(getBaseUrl() + "/");
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        
        try {
            conn.setRequestMethod("POST");
            conn.setRequestProperty("Content-Type", "application/json");
            conn.setConnectTimeout(10000);
            conn.setReadTimeout(15000);
            conn.setDoOutput(true);
            
            String jsonBody = "{\"command\":\"" + command + "\"}";
            
            try (OutputStream os = conn.getOutputStream()) {
                byte[] input = jsonBody.getBytes(StandardCharsets.UTF_8);
                os.write(input, 0, input.length);
            }
            
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
    
    @Override
    public int getCurrentMode() throws Exception {
        URL url = new URL(getBaseUrl() + "/status");
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        
        try {
            conn.setRequestMethod("GET");
            conn.setConnectTimeout(10000);
            conn.setReadTimeout(10000);
            
            int responseCode = conn.getResponseCode();
            
            if (responseCode != 200) {
                throw new Exception("Server not reachable (HTTP " + responseCode + ")");
            }
            
            BufferedReader reader = new BufferedReader(
                new InputStreamReader(conn.getInputStream(), StandardCharsets.UTF_8)
            );
            StringBuilder response = new StringBuilder();
            String line;
            
            while ((line = reader.readLine()) != null) {
                response.append(line);
            }
            reader.close();
            
            String responseStr = response.toString();
            
            try {
                int modeStart = responseStr.indexOf("\"mode\":");
                if (modeStart != -1) {
                    int commaPos = responseStr.indexOf(",", modeStart);
                    String modePart = responseStr.substring(modeStart + 7, commaPos).trim();
                    int mode = Integer.parseInt(modePart);
                    
                    if (mode >= 0 && mode <= 4) {
                        return mode;
                    }
                }
            } catch (Exception e) {
                e.printStackTrace();
            }
            
            return MODE_EXTENDED;
            
        } finally {
            conn.disconnect();
        }
    }
    
    @Override
    public void close() {
    }
    
    @Override
    public boolean isAvailable() {
        try {
            getCurrentMode();
            return true;
        } catch (Exception e) {
            return false;
        }
    }
    
    @Override
    public String getConnectionType() {
        return "WiFi";
    }
    
    public String getServerAddress() {
        return serverAddress;
    }
    
    public int getServerPort() {
        return serverPort;
    }
}
