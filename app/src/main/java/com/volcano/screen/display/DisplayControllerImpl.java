package com.volcano.screen.display;

import com.volcano.screen.network.ServerConnector;

/**
 * Display Controller Implementation
 * Uses ServerConnector for network communication
 * Supports both USB (ADB reverse) and WiFi connections
 */
public class DisplayControllerImpl implements DisplayController {
    
    public static final int MODE_PRIMARY_ONLY = 1;
    public static final int MODE_SECONDARY_ONLY = 2;
    public static final int MODE_EXTENDED = 3;
    public static final int MODE_DUPLICATE = 4;
    
    private ServerConnector connector;
    private String connectionType;
    
    /**
     * Create display controller with custom connector
     * @param connector ServerConnector instance
     * @param connectionType "USB" or "WiFi"
     */
    public DisplayControllerImpl(ServerConnector connector, String connectionType) {
        this.connector = connector;
        this.connectionType = connectionType;
    }
    
    /**
     * Create USB controller (ADB reverse to localhost)
     */
    public static DisplayControllerImpl createUsbController() {
        return new DisplayControllerImpl(
            new ServerConnector("http://localhost:8765"),
            "USB"
        );
    }
    
    /**
     * Create WiFi controller
     * @param serverAddress WiFi server IP address
     * @param serverPort WiFi server port
     */
    public static DisplayControllerImpl createWifiController(String serverAddress, int serverPort) {
        return new DisplayControllerImpl(
            new ServerConnector("http://" + serverAddress + ":" + serverPort),
            "WiFi"
        );
    }
    
    /**
     * Create WiFi controller with default port 8765
     * @param serverAddress WiFi server IP address
     */
    public static DisplayControllerImpl createWifiController(String serverAddress) {
        return createWifiController(serverAddress, 8765);
    }
    
    @Override
    public void setDisplayMode(int mode) throws Exception {
        String command = modeToCommand(mode);
        if (!command.isEmpty()) {
            connector.post("/", "{\"command\":\"" + command + "\"}");
        }
    }
    
    private String modeToCommand(int mode) {
        switch (mode) {
            case MODE_PRIMARY_ONLY:
                return "internal";
            case MODE_SECONDARY_ONLY:
                return "external";
            case MODE_EXTENDED:
                return "extend";
            case MODE_DUPLICATE:
                return "clone";
            default:
                return "";
        }
    }
    
    @Override
    public int getCurrentMode() throws Exception {
        String responseStr = connector.get("/status");
        
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
        return connectionType;
    }
    
    public ServerConnector getConnector() {
        return connector;
    }
}