package com.volcano.screen.display;

import android.content.Context;
import android.content.SharedPreferences;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.os.Handler;
import android.os.Looper;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

public class BrightnessController implements SensorEventListener {

    public interface BrightnessCallback {
        void onBrightnessChanged(float lux, int brightnessPercent);
        void onSensorUnavailable();
    }

    private static final String PREFS_NAME = "brightness_settings";
    private static final String PREF_ENABLED = "brightness_enabled";
    private static final String PREF_MIN_BRIGHTNESS = "min_brightness";
    private static final String PREF_MAX_BRIGHTNESS = "max_brightness";

    private static final int DEFAULT_MIN_BRIGHTNESS = 10;
    private static final int DEFAULT_MAX_BRIGHTNESS = 100;
    private static final long SEND_INTERVAL_MS = 3000;
    private static final int BRIGHTNESS_CHANGE_THRESHOLD = 5;

    private Context context;
    private SensorManager sensorManager;
    private Sensor lightSensor;
    private BrightnessCallback callback;
    private Handler handler;

    private boolean isRunning = false;
    private float currentLux = -1;
    private int currentBrightnessPercent = -1;
    private int lastSentBrightness = -1;
    private long lastSendTime = 0;

    private String serverUrl;
    private SharedPreferences prefs;

    public BrightnessController(Context context, BrightnessCallback callback) {
        this.context = context;
        this.callback = callback;
        this.handler = new Handler(Looper.getMainLooper());
        this.prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);

        sensorManager = (SensorManager) context.getSystemService(Context.SENSOR_SERVICE);
        lightSensor = sensorManager.getDefaultSensor(Sensor.TYPE_LIGHT);

        serverUrl = "http://localhost:8765";
    }

    public void setServerUrl(String url) {
        this.serverUrl = url;
    }

    public boolean isSensorAvailable() {
        return lightSensor != null;
    }

    public boolean isEnabled() {
        return prefs.getBoolean(PREF_ENABLED, true);
    }

    public void setEnabled(boolean enabled) {
        prefs.edit().putBoolean(PREF_ENABLED, enabled).apply();
        if (enabled) {
            start();
        } else {
            stop();
        }
    }

    public int getMinBrightness() {
        return prefs.getInt(PREF_MIN_BRIGHTNESS, DEFAULT_MIN_BRIGHTNESS);
    }

    public void setMinBrightness(int min) {
        prefs.edit().putInt(PREF_MIN_BRIGHTNESS, min).apply();
    }

    public int getMaxBrightness() {
        return prefs.getInt(PREF_MAX_BRIGHTNESS, DEFAULT_MAX_BRIGHTNESS);
    }

    public void setMaxBrightness(int max) {
        prefs.edit().putInt(PREF_MAX_BRIGHTNESS, max).apply();
    }

    public void start() {
        if (isRunning) return;

        if (lightSensor == null) {
            if (callback != null) {
                callback.onSensorUnavailable();
            }
            return;
        }

        sensorManager.registerListener(this, lightSensor, SensorManager.SENSOR_DELAY_NORMAL);
        isRunning = true;
    }

    public void stop() {
        if (!isRunning) return;

        sensorManager.unregisterListener(this);
        isRunning = false;
        currentLux = -1;
        currentBrightnessPercent = -1;
        lastSentBrightness = -1;

        sendBrightnessToServer(100);
    }

    public boolean isRunning() {
        return isRunning;
    }

    public float getCurrentLux() {
        return currentLux;
    }

    public int getCurrentBrightnessPercent() {
        return currentBrightnessPercent;
    }

    @Override
    public void onSensorChanged(SensorEvent event) {
        if (event.sensor.getType() != Sensor.TYPE_LIGHT) return;

        float lux = event.values[0];
        currentLux = lux;

        int brightness = luxToBrightness(lux);
        currentBrightnessPercent = brightness;

        if (callback != null) {
            callback.onBrightnessChanged(lux, brightness);
        }

        long now = System.currentTimeMillis();
        boolean shouldSend = false;

        if (lastSentBrightness < 0) {
            shouldSend = true;
        } else if (Math.abs(brightness - lastSentBrightness) >= BRIGHTNESS_CHANGE_THRESHOLD) {
            shouldSend = true;
        } else if (now - lastSendTime >= SEND_INTERVAL_MS && brightness != lastSentBrightness) {
            shouldSend = true;
        }

        if (shouldSend && isEnabled()) {
            lastSentBrightness = brightness;
            lastSendTime = now;
            sendBrightnessToServer(brightness);
        }
    }

    @Override
    public void onAccuracyChanged(Sensor sensor, int accuracy) {
    }

    int luxToBrightness(float lux) {
        int minB = getMinBrightness();
        int maxB = getMaxBrightness();

        if (lux <= 0) return minB;
        if (lux >= 1000) return maxB;

        double normalizedLux = Math.log10(lux + 1) / Math.log10(1001);
        int brightness = (int) (minB + normalizedLux * (maxB - minB));

        return Math.max(minB, Math.min(maxB, brightness));
    }

    private void sendBrightnessToServer(int brightness) {
        new Thread(() -> {
            try {
                URL url = new URL(serverUrl + "/brightness");
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                try {
                    conn.setRequestMethod("POST");
                    conn.setRequestProperty("Content-Type", "application/json");
                    conn.setConnectTimeout(5000);
                    conn.setReadTimeout(5000);
                    conn.setDoOutput(true);

                    String jsonBody = "{\"brightness\":" + brightness + "}";

                    try (OutputStream os = conn.getOutputStream()) {
                        byte[] input = jsonBody.getBytes(StandardCharsets.UTF_8);
                        os.write(input, 0, input.length);
                    }

                    int responseCode = conn.getResponseCode();
                    if (responseCode != 200) {
                        System.err.println("Brightness send failed: HTTP " + responseCode);
                    }
                } finally {
                    conn.disconnect();
                }
            } catch (Exception e) {
                System.err.println("Brightness send error: " + e.getMessage());
            }
        }).start();
    }

    public void destroy() {
        stop();
    }
}
