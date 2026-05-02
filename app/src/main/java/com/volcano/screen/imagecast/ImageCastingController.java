package com.volcano.screen.imagecast;

import android.util.Log;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

public class ImageCastingController {
    
    private static final String TAG = "ImageCasting";
    private static final String SERVER_URL = "http://localhost:8765";
    
    public ImageStatus getImageStatus() throws Exception {
        URL url = new URL(SERVER_URL + "/image/status");
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        
        try {
            conn.setRequestMethod("GET");
            conn.setConnectTimeout(5000);
            conn.setReadTimeout(5000);
            
            int responseCode = conn.getResponseCode();
            Log.d(TAG, "getStatus response: " + responseCode);
            
            if (responseCode != 200) {
                String errorBody = readErrorStream(conn);
                throw new Exception("getStatus failed (HTTP " + responseCode + "): " + errorBody);
            }
            
            String responseStr = readStream(conn);
            Log.d(TAG, "getStatus body: " + responseStr);
            return parseImageStatus(responseStr);
            
        } finally {
            conn.disconnect();
        }
    }
    
    public byte[] downloadImageBytes() throws Exception {
        URL url = new URL(SERVER_URL + "/image/data");
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        
        try {
            conn.setRequestMethod("GET");
            conn.setConnectTimeout(10000);
            conn.setReadTimeout(30000);
            
            int responseCode = conn.getResponseCode();
            Log.d(TAG, "downloadImage response: " + responseCode 
                + " type: " + conn.getContentType()
                + " length: " + conn.getContentLength());
            
            if (responseCode != 200) {
                String errorBody = readErrorStream(conn);
                throw new Exception("downloadImage failed (HTTP " + responseCode + "): " + errorBody);
            }
            
            String contentType = conn.getContentType();
            if (contentType != null && contentType.contains("application/json")) {
                String errorJson = readStream(conn);
                throw new Exception("Server returned JSON instead of image: " + errorJson);
            }
            
            InputStream inputStream = conn.getInputStream();
            java.io.ByteArrayOutputStream buffer = new java.io.ByteArrayOutputStream();
            int nRead;
            byte[] data = new byte[16384];
            while ((nRead = inputStream.read(data, 0, data.length)) != -1) {
                buffer.write(data, 0, nRead);
            }
            buffer.flush();
            inputStream.close();
            byte[] result = buffer.toByteArray();
            Log.d(TAG, "downloadImage size: " + result.length + " bytes");
            return result;
            
        } finally {
            conn.disconnect();
        }
    }
    
    public void setScale(float scale) throws Exception {
        URL url = new URL(SERVER_URL + "/image/scale");
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        
        try {
            conn.setRequestMethod("POST");
            conn.setRequestProperty("Content-Type", "application/json");
            conn.setConnectTimeout(5000);
            conn.setReadTimeout(5000);
            conn.setDoOutput(true);
            
            String jsonBody = "{\"scale\":" + scale + "}";
            
            try (OutputStream os = conn.getOutputStream()) {
                byte[] input = jsonBody.getBytes(StandardCharsets.UTF_8);
                os.write(input, 0, input.length);
            }
            
            int responseCode = conn.getResponseCode();
            if (responseCode != 200) {
                throw new Exception("setScale failed (HTTP " + responseCode + ")");
            }
            Log.d(TAG, "setScale: " + scale);
            
        } finally {
            conn.disconnect();
        }
    }
    
    public void zoomIn() throws Exception {
        sendSimplePost("/image/zoom-in");
    }
    
    public void zoomOut() throws Exception {
        sendSimplePost("/image/zoom-out");
    }
    
    public void resetZoom() throws Exception {
        sendSimplePost("/image/zoom-reset");
    }
    
    public void clearImage() throws Exception {
        sendSimplePost("/image/clear");
    }
    
    public PollResult pollUpdates(double lastKnownTime) throws Exception {
        URL url = new URL(SERVER_URL + "/image/poll?t=" + lastKnownTime);
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        
        try {
            conn.setRequestMethod("GET");
            conn.setConnectTimeout(5000);
            conn.setReadTimeout(5000);
            
            int responseCode = conn.getResponseCode();
            if (responseCode != 200) {
                throw new Exception("poll failed (HTTP " + responseCode + ")");
            }
            
            String responseStr = readStream(conn);
            return parsePollResult(responseStr);
            
        } finally {
            conn.disconnect();
        }
    }
    
    public void ackAutoPopup() throws Exception {
        sendSimplePost("/image/ack-popup");
        Log.d(TAG, "ackAutoPopup sent");
    }
    
    public void ackCloseWindow() throws Exception {
        sendSimplePost("/image/ack-close");
        Log.d(TAG, "ackCloseWindow sent");
    }
    
    private void sendSimplePost(String path) throws Exception {
        URL url = new URL(SERVER_URL + path);
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        
        try {
            conn.setRequestMethod("POST");
            conn.setConnectTimeout(5000);
            conn.setReadTimeout(5000);
            conn.setDoOutput(true);
            
            int responseCode = conn.getResponseCode();
            if (responseCode != 200) {
                throw new Exception("POST " + path + " failed (HTTP " + responseCode + ")");
            }
            
        } finally {
            conn.disconnect();
        }
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
            InputStream errorStream = conn.getErrorStream();
            if (errorStream == null) return "";
            BufferedReader reader = new BufferedReader(
                new InputStreamReader(errorStream, StandardCharsets.UTF_8)
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
    
    private ImageStatus parseImageStatus(String json) {
        ImageStatus status = new ImageStatus();
        if (json == null || json.isEmpty()) return status;
        
        int hasImageIdx = json.indexOf("\"has_image\":");
        if (hasImageIdx != -1) {
            int endIdx = json.indexOf(",", hasImageIdx);
            if (endIdx == -1) endIdx = json.indexOf("}", hasImageIdx);
            if (endIdx != -1) {
                String val = json.substring(hasImageIdx + 12, endIdx).trim();
                status.hasImage = "true".equalsIgnoreCase(val);
            }
        }
        
        int nameIdx = json.indexOf("\"image_name\":");
        if (nameIdx != -1) {
            int quote1 = json.indexOf("\"", nameIdx + 13);
            int quote2 = json.indexOf("\"", quote1 + 1);
            if (quote1 != -1 && quote2 != -1) {
                status.imageName = json.substring(quote1 + 1, quote2);
            }
        }
        
        int scaleIdx = json.indexOf("\"scale_level\":");
        if (scaleIdx != -1) {
            int endIdx = json.indexOf(",", scaleIdx);
            if (endIdx == -1) endIdx = json.indexOf("}", scaleIdx);
            if (endIdx != -1) {
                try {
                    status.scaleLevel = Float.parseFloat(
                        json.substring(scaleIdx + 14, endIdx).trim()
                    );
                } catch (NumberFormatException e) {
                    status.scaleLevel = 1.0f;
                }
            }
        }
        
        int updateIdx = json.indexOf("\"last_update\":");
        if (updateIdx != -1) {
            int endIdx = json.indexOf(",", updateIdx);
            if (endIdx == -1) endIdx = json.indexOf("}", updateIdx);
            if (endIdx != -1) {
                try {
                    String val = json.substring(updateIdx + 14, endIdx).trim();
                    if (!val.equals("null") && !val.isEmpty()) {
                        status.lastUpdate = Double.parseDouble(val);
                    }
                } catch (NumberFormatException e) {
                    status.lastUpdate = 0;
                }
            }
        }
        
        int autoPopupIdx = json.indexOf("\"auto_popup\":");
        if (autoPopupIdx != -1) {
            int endIdx = json.indexOf(",", autoPopupIdx);
            if (endIdx == -1) endIdx = json.indexOf("}", autoPopupIdx);
            if (endIdx != -1) {
                String val = json.substring(autoPopupIdx + 13, endIdx).trim();
                status.autoPopup = "true".equalsIgnoreCase(val);
            }
        }
        
        int closeWindowIdx = json.indexOf("\"close_window\":");
        if (closeWindowIdx != -1) {
            int endIdx = json.indexOf(",", closeWindowIdx);
            if (endIdx == -1) endIdx = json.indexOf("}", closeWindowIdx);
            if (endIdx != -1) {
                String val = json.substring(closeWindowIdx + 15, endIdx).trim();
                status.closeWindow = "true".equalsIgnoreCase(val);
            }
        }
        
        return status;
    }
    
    private PollResult parsePollResult(String json) {
        PollResult result = new PollResult();
        if (json == null || json.isEmpty()) return result;
        
        int updateIdx = json.indexOf("\"has_update\":");
        if (updateIdx != -1) {
            int endIdx = json.indexOf(",", updateIdx);
            if (endIdx == -1) endIdx = json.indexOf("}", updateIdx);
            if (endIdx != -1) {
                String val = json.substring(updateIdx + 12, endIdx).trim();
                result.hasUpdate = "true".equalsIgnoreCase(val);
            }
        }
        
        int stateIdx = json.indexOf("\"state\":");
        if (stateIdx != -1) {
            int startIdx = json.indexOf("{", stateIdx);
            int endIdx = json.lastIndexOf("}");
            if (startIdx != -1 && endIdx != -1 && endIdx > startIdx) {
                String stateJson = json.substring(startIdx, endIdx + 1);
                result.state = parseImageStatus(stateJson);
            }
        }
        
        return result;
    }
    
    public static class ImageStatus {
        public boolean hasImage = false;
        public String imageName = null;
        public float scaleLevel = 1.0f;
        public double lastUpdate = 0;
        public boolean autoPopup = false;
        public boolean closeWindow = false;
    }
    
    public static class PollResult {
        public boolean hasUpdate = false;
        public ImageStatus state = null;
    }
}
