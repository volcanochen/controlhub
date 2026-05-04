package com.volcano.controlhub.miio;

import java.io.IOException;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.Arrays;

import javax.crypto.Cipher;
import javax.crypto.spec.IvParameterSpec;
import javax.crypto.spec.SecretKeySpec;

public class MiioDevice {
    private static final int PORT = 54321;
    private static final int PACKET_SIZE = 1024;
    
    private String ip;
    private String token;
    private byte[] tokenBytes;
    private DatagramSocket socket;
    private int deviceId;
    private int stamp;
    private byte[] key;
    private byte[] iv;
    
    public MiioDevice(String ip, String token) {
        this.ip = ip;
        this.token = token;
        this.tokenBytes = hexStringToByteArray(token);
        this.deviceId = 0;
        this.stamp = 0;
        generateKeyIv();
    }
    
    private void generateKeyIv() {
        try {
            MessageDigest md = MessageDigest.getInstance("MD5");
            key = md.digest(tokenBytes);
            
            md.reset();
            md.update(key);
            md.update(tokenBytes);
            iv = md.digest();
        } catch (NoSuchAlgorithmException e) {
            e.printStackTrace();
        }
    }
    
    public boolean handshake() throws IOException {
        byte[] hello = new byte[32];
        hello[0] = 0x21;
        hello[1] = 0x31;
        hello[2] = 0x00;
        hello[3] = 0x20;
        Arrays.fill(hello, 4, 16, (byte) 0xFF);
        
        byte[] response = sendPacket(hello);
        if (response != null && response.length >= 32) {
            deviceId = ((response[15] & 0xFF) << 24) | ((response[14] & 0xFF) << 16) | 
                      ((response[13] & 0xFF) << 8) | (response[12] & 0xFF);
            
            stamp = ((response[19] & 0xFF) << 24) | ((response[18] & 0xFF) << 16) | 
                   ((response[17] & 0xFF) << 8) | (response[16] & 0xFF);
            return true;
        }
        return false;
    }
    
    public String sendCommand(String method, Object[] params) throws Exception {
        String id = String.valueOf(System.currentTimeMillis() / 1000);
        String json = "{\"id\":" + id + ",\"method\":\"" + method + "\",\"params\":" + 
                      toJson(params) + "}";
        
        return send(json);
    }
    
    private String toJson(Object[] array) {
        if (array == null || array.length == 0) return "[]";
        StringBuilder sb = new StringBuilder("[");
        for (int i = 0; i < array.length; i++) {
            if (i > 0) sb.append(",");
            if (array[i] instanceof String) {
                sb.append("\"").append(array[i]).append("\"");
            } else {
                sb.append(array[i]);
            }
        }
        sb.append("]");
        return sb.toString();
    }
    
    private String send(String json) throws Exception {
        stamp++;
        
        byte[] data = json.getBytes("UTF-8");
        byte[] encrypted = encrypt(data);
        
        byte[] packet = new byte[32 + encrypted.length];
        packet[0] = 0x21;
        packet[1] = 0x31;
        int len = 32 + encrypted.length;
        packet[2] = (byte) ((len >> 8) & 0xFF);
        packet[3] = (byte) (len & 0xFF);
        
        packet[4] = (byte) 0xFF;
        packet[5] = (byte) 0xFF;
        packet[6] = (byte) 0xFF;
        packet[7] = (byte) 0xFF;
        
        packet[8] = (byte) ((deviceId >> 24) & 0xFF);
        packet[9] = (byte) ((deviceId >> 16) & 0xFF);
        packet[10] = (byte) ((deviceId >> 8) & 0xFF);
        packet[11] = (byte) (deviceId & 0xFF);
        
        packet[12] = (byte) ((stamp >> 24) & 0xFF);
        packet[13] = (byte) ((stamp >> 16) & 0xFF);
        packet[14] = (byte) ((stamp >> 8) & 0xFF);
        packet[15] = (byte) (stamp & 0xFF);
        
        System.arraycopy(new byte[16], 0, packet, 16, 16);
        System.arraycopy(encrypted, 0, packet, 32, encrypted.length);
        
        MessageDigest md = MessageDigest.getInstance("MD5");
        md.update(Arrays.copyOfRange(packet, 0, 16));
        md.update(tokenBytes);
        md.update(Arrays.copyOfRange(packet, 32, packet.length));
        byte[] digest = md.digest();
        System.arraycopy(digest, 0, packet, 16, 16);
        
        byte[] response = sendPacket(packet);
        if (response != null && response.length >= 32) {
            byte[] encryptedResponse = Arrays.copyOfRange(response, 32, response.length);
            byte[] decrypted = decrypt(encryptedResponse);
            return new String(decrypted, "UTF-8");
        }
        return null;
    }
    
    private byte[] sendPacket(byte[] packet) throws IOException {
        if (socket == null) {
            socket = new DatagramSocket();
            socket.setSoTimeout(10000);
        }
        
        try {
            InetAddress address = InetAddress.getByName(ip);
            DatagramPacket sendPacket = new DatagramPacket(packet, packet.length, address, PORT);
            socket.send(sendPacket);
            
            byte[] buffer = new byte[PACKET_SIZE];
            DatagramPacket receivePacket = new DatagramPacket(buffer, buffer.length);
            socket.receive(receivePacket);
            
            return Arrays.copyOfRange(buffer, 0, receivePacket.getLength());
        } catch (java.net.SocketTimeoutException e) {
            throw new IOException("Cannot connect to device " + ip + ", check IP");
        } catch (Exception e) {
            throw new IOException("Communication error: " + e.getMessage());
        }
    }
    
    private byte[] encrypt(byte[] data) throws Exception {
        int padding = 16 - (data.length % 16);
        byte[] padded = new byte[data.length + padding];
        System.arraycopy(data, 0, padded, 0, data.length);
        for (int i = data.length; i < padded.length; i++) {
            padded[i] = (byte) padding;
        }
        
        Cipher cipher = Cipher.getInstance("AES/CBC/NoPadding");
        SecretKeySpec secretKeySpec = new SecretKeySpec(key, "AES");
        IvParameterSpec ivParameterSpec = new IvParameterSpec(iv);
        cipher.init(Cipher.ENCRYPT_MODE, secretKeySpec, ivParameterSpec);
        return cipher.doFinal(padded);
    }
    
    private byte[] decrypt(byte[] data) throws Exception {
        Cipher cipher = Cipher.getInstance("AES/CBC/NoPadding");
        SecretKeySpec secretKeySpec = new SecretKeySpec(key, "AES");
        IvParameterSpec ivParameterSpec = new IvParameterSpec(iv);
        cipher.init(Cipher.DECRYPT_MODE, secretKeySpec, ivParameterSpec);
        byte[] decrypted = cipher.doFinal(data);
        
        int padding = decrypted[decrypted.length - 1] & 0xFF;
        return Arrays.copyOfRange(decrypted, 0, decrypted.length - padding);
    }
    
    private byte[] hexStringToByteArray(String s) {
        int len = s.length();
        byte[] data = new byte[len / 2];
        for (int i = 0; i < len; i += 2) {
            data[i / 2] = (byte) ((Character.digit(s.charAt(i), 16) << 4)
                                 + Character.digit(s.charAt(i+1), 16));
        }
        return data;
    }
    
    public void close() {
        if (socket != null) {
            socket.close();
            socket = null;
        }
    }
}
