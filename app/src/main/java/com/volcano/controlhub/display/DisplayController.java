package com.volcano.controlhub.display;

public interface DisplayController {
    void setDisplayMode(int mode) throws Exception;
    
    int getCurrentMode() throws Exception;
    
    void close();
    
    boolean isAvailable();
    
    String getConnectionType();
}
