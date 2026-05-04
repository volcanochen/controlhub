package com.volcano.controlhub.network;

import android.content.Context;
import android.content.SharedPreferences;
import android.util.Log;

/**
 * Channel Manager - Unified network channel selection for all modules
 * 
 * Provides USB, WiFi, and AUTO channel modes for communication with PC server.
 * All modules should use this class to get the current server URL.
 */
public class ChannelManager {
    
    private static final String TAG = "ChannelManager";
    
    private static final String PREFS_NAME = "channel_settings";
    private static final String PREF_MODE = "channel_mode";
    private static final String PREF_WIFI_ADDRESS = "wifi_address";
    private static final String PREF_WIFI_PORT = "wifi_port";
    
    public static final int MODE_AUTO = 0;
    public static final int MODE_USB = 1;
    public static final int MODE_WIFI = 2;
    
    private static final String DEFAULT_WIFI_ADDRESS = "192.168.50.111";
    private static final int DEFAULT_WIFI_PORT = 8765;
    private static final int DEFAULT_USB_PORT = 8765;
    
    private static ChannelManager instance;
    private final Context context;
    private final SharedPreferences prefs;
    
    private ChannelManager(Context context) {
        this.context = context.getApplicationContext();
        this.prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
    }
    
    public static synchronized ChannelManager getInstance(Context context) {
        if (instance == null) {
            instance = new ChannelManager(context);
        }
        return instance;
    }
    
    /**
     * Get current channel mode
     * @return MODE_AUTO, MODE_USB, or MODE_WIFI
     */
    public int getMode() {
        return prefs.getInt(PREF_MODE, MODE_AUTO);
    }
    
    /**
     * Set channel mode
     * @param mode MODE_AUTO, MODE_USB, or MODE_WIFI
     */
    public void setMode(int mode) {
        prefs.edit().putInt(PREF_MODE, mode).apply();
        Log.d(TAG, "Channel mode set to: " + modeName(mode));
    }
    
    /**
     * Get WiFi server address
     */
    public String getWifiAddress() {
        return prefs.getString(PREF_WIFI_ADDRESS, DEFAULT_WIFI_ADDRESS);
    }
    
    /**
     * Set WiFi server address
     */
    public void setWifiAddress(String address) {
        prefs.edit().putString(PREF_WIFI_ADDRESS, address).apply();
        Log.d(TAG, "WiFi address set to: " + address);
    }
    
    /**
     * Get WiFi server port
     */
    public int getWifiPort() {
        return prefs.getInt(PREF_WIFI_PORT, DEFAULT_WIFI_PORT);
    }
    
    /**
     * Set WiFi server port
     */
    public void setWifiPort(int port) {
        prefs.edit().putInt(PREF_WIFI_PORT, port).apply();
        Log.d(TAG, "WiFi port set to: " + port);
    }
    
    /**
     * Get USB server port
     */
    public int getUsbPort() {
        return DEFAULT_USB_PORT;
    }
    
    /**
     * Get current server URL based on channel mode
     * @return Server URL (e.g., "http://localhost:8765" or "http://192.168.50.111:8765")
     */
    public String getServerUrl() {
        int mode = getMode();
        String url;
        
        switch (mode) {
            case MODE_USB:
                url = getUsbUrl();
                break;
            case MODE_WIFI:
                url = getWifiUrl();
                break;
            case MODE_AUTO:
            default:
                // In AUTO mode, prefer USB for reliability
                url = getUsbUrl();
                break;
        }
        
        Log.d(TAG, "Server URL: " + url + " (mode=" + modeName(mode) + ")");
        return url;
    }
    
    /**
     * Get USB URL
     */
    public String getUsbUrl() {
        return "http://localhost:" + getUsbPort();
    }
    
    /**
     * Get WiFi URL
     */
    public String getWifiUrl() {
        return "http://" + getWifiAddress() + ":" + getWifiPort();
    }
    
    /**
     * Get server URL for specific mode
     * @param mode MODE_USB or MODE_WIFI
     */
    public String getServerUrlForMode(int mode) {
        switch (mode) {
            case MODE_USB:
                return getUsbUrl();
            case MODE_WIFI:
                return getWifiUrl();
            default:
                return getServerUrl();
        }
    }
    
    /**
     * Get mode name for logging
     */
    public static String modeName(int mode) {
        switch (mode) {
            case MODE_USB:
                return "USB";
            case MODE_WIFI:
                return "WiFi";
            case MODE_AUTO:
                return "Auto";
            default:
                return "Unknown";
        }
    }
    
    /**
     * Create a ServerConnector with current channel settings
     */
    public ServerConnector createConnector() {
        return new ServerConnector(getServerUrl());
    }
    
    /**
     * Create a ServerConnector with custom timeouts
     */
    public ServerConnector createConnector(int connectTimeout, int readTimeout) {
        return new ServerConnector(getServerUrl(), connectTimeout, readTimeout);
    }
    
    /**
     * Import settings from legacy display_settings (for migration)
     */
    public void importFromDisplaySettings(Context context) {
        SharedPreferences displayPrefs = context.getSharedPreferences("display_settings", Context.MODE_PRIVATE);
        
        int legacyMode = displayPrefs.getInt("preferred_mode", MODE_AUTO);
        String legacyAddress = displayPrefs.getString("wifi_address", DEFAULT_WIFI_ADDRESS);
        int legacyPort = displayPrefs.getInt("wifi_port", DEFAULT_WIFI_PORT);
        
        prefs.edit()
            .putInt(PREF_MODE, legacyMode)
            .putString(PREF_WIFI_ADDRESS, legacyAddress)
            .putInt(PREF_WIFI_PORT, legacyPort)
            .apply();
        
        Log.d(TAG, "Imported settings from display_settings: mode=" + modeName(legacyMode) + 
              ", address=" + legacyAddress + ", port=" + legacyPort);
    }
}
