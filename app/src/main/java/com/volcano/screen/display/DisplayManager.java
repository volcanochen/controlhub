package com.volcano.screen.display;

import android.content.Context;
import android.content.SharedPreferences;

/**
 * Display Manager
 * Manages communication mode selection and provides unified interface
 */
public class DisplayManager {
    
    private static final String PREFS_NAME = "display_settings";
    private static final String PREF_PREFERRED_MODE = "preferred_mode";
    private static final String PREF_WIFI_ADDRESS = "wifi_address";
    private static final String PREF_WIFI_PORT = "wifi_port";
    
    public static final int MODE_AUTO = 0;
    public static final int MODE_USB = 1;
    public static final int MODE_WIFI = 2;
    
    // Display mode constants
    public static final int MODE_PRIMARY_ONLY = 1;
    public static final int MODE_SECONDARY_ONLY = 2;
    public static final int MODE_EXTENDED = 3;
    public static final int MODE_DUPLICATE = 4;
    
    private Context context;
    private SharedPreferences prefs;
    private DisplayController currentController;
    
    public DisplayManager(Context context) {
        this.context = context;
        this.prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
    }
    
    /**
     * Get display controller based on current settings
     * Automatically detects and handles USB reconnect scenarios
     * @return display controller instance
     */
    public DisplayController getController() {
        // If we have a cached controller, check if it's still available
        // This handles the case when USB is disconnected and reconnected
        if (currentController != null) {
            // Check if current controller is available
            if (currentController.isAvailable()) {
                return currentController;
            }
            // Controller became unavailable, reset and try to reconnect
            currentController.close();
            currentController = null;
        }
        
        int preferredMode = prefs.getInt(PREF_PREFERRED_MODE, MODE_AUTO);
        String wifiAddress = prefs.getString(PREF_WIFI_ADDRESS, "192.168.50.111");
        int wifiPort = prefs.getInt(PREF_WIFI_PORT, 8765);
        
        switch (preferredMode) {
            case MODE_USB:
                currentController = DisplayControllerImpl.createUsbController();
                break;
            case MODE_WIFI:
                currentController = DisplayControllerImpl.createWifiController(wifiAddress, wifiPort);
                break;
            case MODE_AUTO:
            default:
                currentController = autoSelectController(wifiAddress, wifiPort);
                break;
        }
        
        return currentController;
    }
    
    /**
     * Auto select best available controller
     */
    private DisplayController autoSelectController(String wifiAddress, int wifiPort) {
        DisplayControllerImpl usbController = DisplayControllerImpl.createUsbController();
        if (usbController.isAvailable()) {
            return usbController;
        }
        
        DisplayControllerImpl wifiController = DisplayControllerImpl.createWifiController(wifiAddress, wifiPort);
        if (wifiController.isAvailable()) {
            return wifiController;
        }
        
        return usbController;
    }
    
    /**
     * Set preferred communication mode
     */
    public void setPreferredMode(int mode) {
        prefs.edit().putInt(PREF_PREFERRED_MODE, mode).apply();
        currentController = null;
    }
    
    /**
     * Get preferred communication mode
     */
    public int getPreferredMode() {
        return prefs.getInt(PREF_PREFERRED_MODE, MODE_AUTO);
    }
    
    /**
     * Set WiFi server address
     */
    public void setWifiAddress(String address) {
        prefs.edit().putString(PREF_WIFI_ADDRESS, address).apply();
        currentController = null;
    }
    
    /**
     * Get WiFi server address
     */
    public String getWifiAddress() {
        return prefs.getString(PREF_WIFI_ADDRESS, "192.168.50.111");
    }
    
    /**
     * Set WiFi server port
     */
    public void setWifiPort(int port) {
        prefs.edit().putInt(PREF_WIFI_PORT, port).apply();
        currentController = null;
    }
    
    /**
     * Get WiFi server port
     */
    public int getWifiPort() {
        return prefs.getInt(PREF_WIFI_PORT, 8765);
    }
    
    /**
     * Check if USB is available
     */
    public boolean isUsbAvailable() {
        return DisplayControllerImpl.createUsbController().isAvailable();
    }
    
    /**
     * Check if WiFi is available
     */
    public boolean isWifiAvailable() {
        String address = getWifiAddress();
        int port = getWifiPort();
        return DisplayControllerImpl.createWifiController(address, port).isAvailable();
    }
    
    /**
     * Reset controller (force re-selection)
     */
    public void resetController() {
        if (currentController != null) {
            currentController.close();
        }
        currentController = null;
    }
    
    /**
     * Close manager
     */
    public void close() {
        if (currentController != null) {
            currentController.close();
            currentController = null;
        }
    }
}
