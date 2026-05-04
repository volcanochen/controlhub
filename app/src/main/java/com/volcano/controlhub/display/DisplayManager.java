package com.volcano.controlhub.display;

import android.content.Context;
import android.util.Log;

import com.volcano.controlhub.network.ChannelManager;

public class DisplayManager {
    
    private static final String TAG = "DisplayManager";
    
    public static final int MODE_PRIMARY_ONLY = 1;
    public static final int MODE_SECONDARY_ONLY = 2;
    public static final int MODE_EXTENDED = 3;
    public static final int MODE_DUPLICATE = 4;
    
    private Context context;
    private ChannelManager channelManager;
    private DisplayController currentController;
    
    public DisplayManager(Context context) {
        this.context = context;
        this.channelManager = ChannelManager.getInstance(context);
    }
    
    public DisplayController getController() {
        if (currentController != null) {
            if (currentController.isAvailable()) {
                return currentController;
            }
            currentController.close();
            currentController = null;
        }
        
        int mode = channelManager.getMode();
        String wifiAddress = channelManager.getWifiAddress();
        int wifiPort = channelManager.getWifiPort();
        
        switch (mode) {
            case ChannelManager.MODE_USB:
                currentController = DisplayControllerImpl.createUsbController();
                Log.d(TAG, "Using USB channel");
                break;
            case ChannelManager.MODE_WIFI:
                currentController = DisplayControllerImpl.createWifiController(wifiAddress, wifiPort);
                Log.d(TAG, "Using WiFi channel: " + wifiAddress + ":" + wifiPort);
                break;
            case ChannelManager.MODE_AUTO:
            default:
                currentController = autoSelectController(wifiAddress, wifiPort);
                break;
        }
        
        return currentController;
    }
    
    private DisplayController autoSelectController(String wifiAddress, int wifiPort) {
        DisplayControllerImpl usbController = DisplayControllerImpl.createUsbController();
        if (usbController.isAvailable()) {
            Log.d(TAG, "AUTO mode: Using USB channel");
            return usbController;
        }
        
        DisplayControllerImpl wifiController = DisplayControllerImpl.createWifiController(wifiAddress, wifiPort);
        if (wifiController.isAvailable()) {
            Log.d(TAG, "AUTO mode: Using WiFi channel");
            return wifiController;
        }
        
        Log.d(TAG, "AUTO mode: No channel available, defaulting to USB");
        return usbController;
    }
    
    public void setPreferredMode(int mode) {
        channelManager.setMode(mode);
        currentController = null;
    }
    
    public int getPreferredMode() {
        return channelManager.getMode();
    }
    
    public void setWifiAddress(String address) {
        channelManager.setWifiAddress(address);
        currentController = null;
    }
    
    public String getWifiAddress() {
        return channelManager.getWifiAddress();
    }
    
    public void setWifiPort(int port) {
        channelManager.setWifiPort(port);
        currentController = null;
    }
    
    public int getWifiPort() {
        return channelManager.getWifiPort();
    }
    
    public boolean isUsbAvailable() {
        return DisplayControllerImpl.createUsbController().isAvailable();
    }
    
    public boolean isWifiAvailable() {
        String address = getWifiAddress();
        int port = getWifiPort();
        return DisplayControllerImpl.createWifiController(address, port).isAvailable();
    }
    
    public void resetController() {
        if (currentController != null) {
            currentController.close();
        }
        currentController = null;
    }
    
    public void close() {
        if (currentController != null) {
            currentController.close();
            currentController = null;
        }
    }
}
