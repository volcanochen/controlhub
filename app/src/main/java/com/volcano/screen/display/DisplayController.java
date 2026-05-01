package com.volcano.screen.display;

/**
 * Display Controller Interface
 * Abstracts communication for both USB (ADB reverse) and WiFi modes
 */
public interface DisplayController {
    /**
     * Set display mode
     * @param mode display mode (MODE_PRIMARY_ONLY, MODE_SECONDARY_ONLY, MODE_EXTENDED, MODE_DUPLICATE)
     */
    void setDisplayMode(int mode) throws Exception;
    
    /**
     * Get current display mode
     * @return current mode
     */
    int getCurrentMode() throws Exception;
    
    /**
     * Close connection and clean up resources
     */
    void close();
    
    /**
     * Check if connection is available
     * @return true if connected
     */
    boolean isAvailable();
    
    /**
     * Get connection type name
     * @return connection type (e.g., "USB", "WiFi")
     */
    String getConnectionType();
}
