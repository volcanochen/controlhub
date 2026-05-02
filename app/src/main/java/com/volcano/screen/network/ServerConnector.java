package com.volcano.screen.network;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

public class ServerConnector {
    
    private String baseUrl;
    private int connectTimeout;
    private int readTimeout;
    
    public ServerConnector(String baseUrl) {
        this(baseUrl, 10000, 15000);
    }
    
    public ServerConnector(String baseUrl, int connectTimeout, int readTimeout) {
        this.baseUrl = baseUrl;
        this.connectTimeout = connectTimeout;
        this.readTimeout = readTimeout;
    }
    
    public String get(String path) throws Exception {
        URL url = new URL(baseUrl + path);
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        
        try {
            conn.setRequestMethod("GET");
            conn.setConnectTimeout(connectTimeout);
            conn.setReadTimeout(readTimeout);
            
            int responseCode = conn.getResponseCode();
            
            if (responseCode != 200) {
                throw new Exception("GET " + path + " failed (HTTP " + responseCode + "): " + readErrorStream(conn));
            }
            
            return readStream(conn);
            
        } finally {
            conn.disconnect();
        }
    }
    
    public String post(String path, String jsonBody) throws Exception {
        URL url = new URL(baseUrl + path);
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        
        try {
            conn.setRequestMethod("POST");
            conn.setRequestProperty("Content-Type", "application/json");
            conn.setConnectTimeout(connectTimeout);
            conn.setReadTimeout(readTimeout);
            conn.setDoOutput(true);
            
            if (jsonBody != null && !jsonBody.isEmpty()) {
                try (OutputStream os = conn.getOutputStream()) {
                    byte[] input = jsonBody.getBytes(StandardCharsets.UTF_8);
                    os.write(input, 0, input.length);
                }
            }
            
            int responseCode = conn.getResponseCode();
            
            if (responseCode != 200) {
                throw new Exception("POST " + path + " failed (HTTP " + responseCode + "): " + readErrorStream(conn));
            }
            
            return readStream(conn);
            
        } finally {
            conn.disconnect();
        }
    }
    
    public String post(String path) throws Exception {
        return post(path, null);
    }
    
    private String readStream(HttpURLConnection conn) throws Exception {
        BufferedReader reader = new BufferedReader(
            new InputStreamReader(conn.getInputStream(), StandardCharsets.UTF_8)
        );
        StringBuilder response = new StringBuilder();
        String line;
        while ((line = reader.readLine()) != null) {
            response.append(line);
        }
        reader.close();
        return response.toString();
    }
    
    private String readErrorStream(HttpURLConnection conn) {
        try {
            if (conn.getErrorStream() == null) return "";
            BufferedReader reader = new BufferedReader(
                new InputStreamReader(conn.getErrorStream(), StandardCharsets.UTF_8)
            );
            StringBuilder sb = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                sb.append(line);
            }
            reader.close();
            return sb.toString();
        } catch (Exception e) {
            return "";
        }
    }
    
    public String getBaseUrl() {
        return baseUrl;
    }
    
    public void setBaseUrl(String baseUrl) {
        this.baseUrl = baseUrl;
    }
}