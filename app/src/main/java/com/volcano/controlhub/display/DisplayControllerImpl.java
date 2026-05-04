package com.volcano.controlhub.display;

import android.content.Context;

import com.volcano.controlhub.network.ChannelManager;
import com.volcano.controlhub.network.ServerConnector;

public class DisplayControllerImpl implements DisplayController {
    
    public static final int MODE_PRIMARY_ONLY = 1;
    public static final int MODE_SECONDARY_ONLY = 2;
    public static final int MODE_EXTENDED = 3;
    public static final int MODE_DUPLICATE = 4;
    
    private ServerConnector connector;
    private String connectionType;
    
    public DisplayControllerImpl(ServerConnector connector, String connectionType) {
        this.connector = connector;
        this.connectionType = connectionType;
    }
    
    public static DisplayControllerImpl createUsbController() {
        return new DisplayControllerImpl(
            new ServerConnector(ChannelManager.getInstance(null).getUsbUrl()),
            "USB"
        );
    }
    
    public static DisplayControllerImpl createWifiController(String serverAddress, int serverPort) {
        return new DisplayControllerImpl(
            new ServerConnector("http://" + serverAddress + ":" + serverPort),
            "WiFi"
        );
    }
    
    public static DisplayControllerImpl createWifiController(String serverAddress) {
        return createWifiController(serverAddress, 8765);
    }
    
    public static DisplayControllerImpl createFromChannelManager(Context context) {
        ChannelManager cm = ChannelManager.getInstance(context);
        return new DisplayControllerImpl(
            new ServerConnector(cm.getServerUrl()),
            cm.getMode() == ChannelManager.MODE_USB ? "USB" : "WiFi"
        );
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
