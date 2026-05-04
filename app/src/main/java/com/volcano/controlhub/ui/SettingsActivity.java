package com.volcano.controlhub.ui;

import com.volcano.controlhub.R;
import com.volcano.controlhub.display.DisplayManager;
import com.volcano.controlhub.camera.MJPEGStreamServer;
import com.volcano.controlhub.network.ChannelManager;

import android.content.ClipData;
import android.content.ClipboardManager;
import android.net.wifi.WifiInfo;
import android.net.wifi.WifiManager;
import android.widget.SeekBar;
import android.app.AlertDialog;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.RadioButton;
import android.widget.RadioGroup;
import android.widget.Switch;
import android.widget.TextView;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import com.volcano.controlhub.ui.LogActivity;
import com.volcano.controlhub.ui.AboutActivity;
import com.volcano.controlhub.network.NetworkSpeedTester;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class SettingsActivity extends AppCompatActivity {
    
    private Switch switchLamp;
    private Switch switchDisplay;
    private Switch switchBrightness;
    private SeekBar homeBrightnessSeek;
    private TextView homeBrightnessValue;
    private LinearLayout brightnessSettingsDetail;
    private EditText minBrightnessEdit;
    private EditText maxBrightnessEdit;
    private Button viewLogButton;
    private Button aboutButton;
    private Button backButton;
    private Button networkSpeedButton;
    private Button testConnectionButton;
    private RadioGroup communicationModeGroup;
    private RadioButton radioAuto;
    private RadioButton radioUsb;
    private RadioButton radioWifi;
    private EditText wifiAddressEdit;
    private EditText wifiPortEdit;
    private TextView deviceIpText;
    private TextView cameraPortText;
    private TextView usbStatusText;
    
    private SharedPreferences prefs;
    private DisplayManager displayManager;
    private NetworkSpeedTester speedTester;
    private ExecutorService executorService;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_settings);
        
        prefs = getSharedPreferences("app_settings", MODE_PRIVATE);
        displayManager = new DisplayManager(this);
        executorService = Executors.newSingleThreadExecutor();
        
        initViews();
        loadSettings();
        setupListeners();
    }
    
    private void initViews() {
        switchLamp = findViewById(R.id.switch_lamp);
        switchDisplay = findViewById(R.id.switch_display);
        switchBrightness = findViewById(R.id.switch_brightness);
        homeBrightnessSeek = findViewById(R.id.home_brightness_seek);
        homeBrightnessValue = findViewById(R.id.home_brightness_value);
        brightnessSettingsDetail = findViewById(R.id.brightness_settings_detail);
        minBrightnessEdit = findViewById(R.id.min_brightness_edit);
        maxBrightnessEdit = findViewById(R.id.max_brightness_edit);
        viewLogButton = findViewById(R.id.view_log_button);
        aboutButton = findViewById(R.id.about_button);
        backButton = findViewById(R.id.back_button);
        networkSpeedButton = findViewById(R.id.network_speed_button);
        testConnectionButton = findViewById(R.id.test_connection_button);
        communicationModeGroup = findViewById(R.id.communication_mode_group);
        radioAuto = findViewById(R.id.radio_auto);
        radioUsb = findViewById(R.id.radio_usb);
        radioWifi = findViewById(R.id.radio_wifi);
        wifiAddressEdit = findViewById(R.id.wifi_address_edit);
        wifiPortEdit = findViewById(R.id.wifi_port_edit);
        deviceIpText = findViewById(R.id.device_ip_text);
        cameraPortText = findViewById(R.id.camera_port_text);
        usbStatusText = findViewById(R.id.usb_status_text);
    }
    
    private void loadSettings() {
        boolean lampEnabled = prefs.getBoolean("lamp_enabled", true);
        switchLamp.setChecked(lampEnabled);
        
        boolean displayEnabled = prefs.getBoolean("display_enabled", true);
        switchDisplay.setChecked(displayEnabled);
        
        boolean brightnessEnabled = prefs.getBoolean("brightness_enabled", true);
        switchBrightness.setChecked(brightnessEnabled);
        brightnessSettingsDetail.setVisibility(brightnessEnabled ? View.VISIBLE : View.GONE);
        
        int homeBrightness = prefs.getInt("home_brightness", 50);
        homeBrightnessSeek.setProgress(homeBrightness);
        homeBrightnessValue.setText(homeBrightness + "%");
        
        int minBrightness = prefs.getInt("min_brightness", 10);
        minBrightnessEdit.setText(String.valueOf(minBrightness));
        
        int maxBrightness = prefs.getInt("max_brightness", 100);
        maxBrightnessEdit.setText(String.valueOf(maxBrightness));
        
        int preferredMode = displayManager.getPreferredMode();
        switch (preferredMode) {
            case ChannelManager.MODE_USB:
                radioUsb.setChecked(true);
                break;
            case ChannelManager.MODE_WIFI:
                radioWifi.setChecked(true);
                break;
            case ChannelManager.MODE_AUTO:
            default:
                radioAuto.setChecked(true);
                break;
        }
        
        String wifiAddress = displayManager.getWifiAddress();
        wifiAddressEdit.setText(wifiAddress);
        
        int wifiPort = displayManager.getWifiPort();
        wifiPortEdit.setText(String.valueOf(wifiPort));
        
        updateDeviceIp();
        cameraPortText.setText(String.valueOf(MJPEGStreamServer.DEFAULT_PORT));
        updateUsbStatus();
    }
    
    private void updateUsbStatus() {
        android.content.Intent batteryIntent = registerReceiver(null, new android.content.IntentFilter(android.content.Intent.ACTION_BATTERY_CHANGED));
        if (batteryIntent != null) {
            int plugged = batteryIntent.getIntExtra(android.os.BatteryManager.EXTRA_PLUGGED, -1);
            boolean usbConnected = plugged == android.os.BatteryManager.BATTERY_PLUGGED_USB;
            if (usbConnected) {
                usbStatusText.setText("已连接 (ADB 可用)");
                usbStatusText.setTextColor(android.graphics.Color.parseColor("#4CAF50"));
            } else {
                usbStatusText.setText("未连接");
                usbStatusText.setTextColor(android.graphics.Color.parseColor("#FF9800"));
            }
        } else {
            usbStatusText.setText("无法检测");
            usbStatusText.setTextColor(android.graphics.Color.parseColor("#888888"));
        }
    }
    
    private void updateDeviceIp() {
        String ipAddress = getDeviceIpAddress();
        if (ipAddress != null && !ipAddress.isEmpty()) {
            deviceIpText.setText(ipAddress);
        } else {
            deviceIpText.setText("未连接 WiFi");
        }
    }
    
    private String getDeviceIpAddress() {
        try {
            WifiManager wifiManager = (WifiManager) getApplicationContext().getSystemService(WIFI_SERVICE);
            if (wifiManager != null) {
                WifiInfo wifiInfo = wifiManager.getConnectionInfo();
                int ipInt = wifiInfo.getIpAddress();
                if (ipInt != 0) {
                    return String.format("%d.%d.%d.%d",
                            (ipInt & 0xff),
                            (ipInt >> 8 & 0xff),
                            (ipInt >> 16 & 0xff),
                            (ipInt >> 24 & 0xff));
                }
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
        return null;
    }
    
    private void setupListeners() {
        viewLogButton.setOnClickListener(v -> {
            Intent intent = new Intent(SettingsActivity.this, LogActivity.class);
            startActivity(intent);
        });
        
        aboutButton.setOnClickListener(v -> {
            Intent intent = new Intent(SettingsActivity.this, AboutActivity.class);
            startActivity(intent);
        });
        
        switchLamp.setOnCheckedChangeListener((buttonView, isChecked) -> {
            prefs.edit().putBoolean("lamp_enabled", isChecked).apply();
            Toast.makeText(this, 
                isChecked ? "台灯控制已启用" : "台灯控制已禁用", 
                Toast.LENGTH_SHORT).show();
        });
        
        switchDisplay.setOnCheckedChangeListener((buttonView, isChecked) -> {
            prefs.edit().putBoolean("display_enabled", isChecked).apply();
            Toast.makeText(this, 
                isChecked ? "显示器控制已启用" : "显示器控制已禁用", 
                Toast.LENGTH_SHORT).show();
        });
        
        switchBrightness.setOnCheckedChangeListener((buttonView, isChecked) -> {
            prefs.edit().putBoolean("brightness_enabled", isChecked).apply();
            brightnessSettingsDetail.setVisibility(isChecked ? View.VISIBLE : View.GONE);
            Toast.makeText(this, 
                isChecked ? "亮度控制已启用" : "亮度控制已禁用", 
                Toast.LENGTH_SHORT).show();
        });
        
        homeBrightnessSeek.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
            @Override
            public void onProgressChanged(SeekBar seekBar, int progress, boolean fromUser) {
                homeBrightnessValue.setText(progress + "%");
                if (fromUser) {
                    applyBrightness(progress);
                }
            }
            
            @Override
            public void onStartTrackingTouch(SeekBar seekBar) {
            }
            
            @Override
            public void onStopTrackingTouch(SeekBar seekBar) {
                int progress = seekBar.getProgress();
                prefs.edit().putInt("home_brightness", progress).apply();
            }
        });
        
        backButton.setOnClickListener(v -> {
            saveSettings();
            finish();
        });
        
        networkSpeedButton.setOnClickListener(v -> {
            startNetworkSpeedTest();
        });
        
        testConnectionButton.setOnClickListener(v -> {
            saveWifiSettings();
            testConnection();
        });
        
        deviceIpText.setOnClickListener(v -> {
            String ip = deviceIpText.getText().toString();
            if (!ip.isEmpty() && !ip.equals("未连接 WiFi") && !ip.equals("正在获取...")) {
                ClipboardManager clipboard = (ClipboardManager) getSystemService(CLIPBOARD_SERVICE);
                ClipData clip = ClipData.newPlainText("device_ip", ip);
                clipboard.setPrimaryClip(clip);
                Toast.makeText(this, "IP 已复制: " + ip, Toast.LENGTH_SHORT).show();
            }
        });
        
        communicationModeGroup.setOnCheckedChangeListener((group, checkedId) -> {
            if (checkedId == R.id.radio_auto) {
                displayManager.setPreferredMode(ChannelManager.MODE_AUTO);
                Toast.makeText(this, "已设置为自动选择", Toast.LENGTH_SHORT).show();
            } else if (checkedId == R.id.radio_usb) {
                displayManager.setPreferredMode(ChannelManager.MODE_USB);
                Toast.makeText(this, "已设置为仅 USB", Toast.LENGTH_SHORT).show();
            } else if (checkedId == R.id.radio_wifi) {
                displayManager.setPreferredMode(ChannelManager.MODE_WIFI);
                Toast.makeText(this, "已设置为仅 WiFi", Toast.LENGTH_SHORT).show();
            }
        });
    }
    
    private void saveSettings() {
        saveWifiSettings();
        
        try {
            String minStr = minBrightnessEdit.getText().toString().trim();
            if (!minStr.isEmpty()) {
                int minBrightness = Integer.parseInt(minStr);
                prefs.edit().putInt("min_brightness", Math.max(0, Math.min(100, minBrightness))).apply();
            }
        } catch (NumberFormatException e) {
            e.printStackTrace();
        }
        
        try {
            String maxStr = maxBrightnessEdit.getText().toString().trim();
            if (!maxStr.isEmpty()) {
                int maxBrightness = Integer.parseInt(maxStr);
                prefs.edit().putInt("max_brightness", Math.max(0, Math.min(100, maxBrightness))).apply();
            }
        } catch (NumberFormatException e) {
            e.printStackTrace();
        }
    }
    
    private void applyBrightness(int brightnessPercent) {
        WindowManager.LayoutParams params = getWindow().getAttributes();
        params.screenBrightness = brightnessPercent / 100f;
        getWindow().setAttributes(params);
    }
    
    private void saveWifiSettings() {
        String address = wifiAddressEdit.getText().toString().trim();
        if (!address.isEmpty()) {
            displayManager.setWifiAddress(address);
        }
        
        try {
            String portStr = wifiPortEdit.getText().toString().trim();
            if (!portStr.isEmpty()) {
                int port = Integer.parseInt(portStr);
                displayManager.setWifiPort(port);
            }
        } catch (NumberFormatException e) {
            e.printStackTrace();
        }
    }
    
    private void testConnection() {
        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setTitle("连接测试");
        
        final TextView resultText = new TextView(this);
        resultText.setPadding(50, 50, 50, 50);
        resultText.setTextSize(14);
        resultText.setTextColor(Color.BLACK);
        resultText.setMovementMethod(android.text.method.ScrollingMovementMethod.getInstance());
        resultText.setMinHeight(400);
        
        builder.setView(resultText);
        builder.setPositiveButton("关闭", null);
        
        final AlertDialog dialog = builder.create();
        resultText.setText("正在测试连接...\n");
        dialog.show();
        
        executorService.execute(() -> {
            StringBuilder result = new StringBuilder();
            result.append("连接测试结果\n");
            result.append("================\n\n");
            
            boolean usbAvailable = displayManager.isUsbAvailable();
            result.append("USB 连接: ").append(usbAvailable ? "✅ 可用" : "❌ 不可用").append("\n\n");
            
            boolean wifiAvailable = displayManager.isWifiAvailable();
            result.append("WiFi 连接: ").append(wifiAvailable ? "✅ 可用" : "❌ 不可用").append("\n\n");
            
            String currentMode = displayManager.getController().getConnectionType();
            result.append("当前使用: ").append(currentMode).append("\n");
            
            new Handler(Looper.getMainLooper()).post(() -> {
                resultText.setText(result.toString());
            });
        });
    }
    
    private void startNetworkSpeedTest() {
        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setTitle("网络速度测试");
        
        final TextView resultText = new TextView(this);
        resultText.setPadding(50, 50, 50, 50);
        resultText.setTextSize(14);
        resultText.setTextColor(Color.BLACK);
        resultText.setMovementMethod(android.text.method.ScrollingMovementMethod.getInstance());
        resultText.setMinHeight(400);
        
        builder.setView(resultText);
        builder.setPositiveButton("关闭", (dialog, which) -> {
            if (speedTester != null) {
                speedTester.destroy();
            }
        });
        
        final AlertDialog dialog = builder.create();
        resultText.setText("正在初始化测试...\n\n请稍候...");
        dialog.show();
        
        speedTester = new NetworkSpeedTester(this, resultText);
        String usbUrl = speedTester.getUsbUrl();
        String wifiUrl = speedTester.getWifiUrl();
        
        speedTester.startDualTest(usbUrl, wifiUrl, new NetworkSpeedTester.SpeedTestCallback() {
            @Override
            public void onPingResult(double avgLatency, double minLatency, double maxLatency) {
            }
            
            @Override
            public void onDownloadResult(double speedMbps) {
            }
            
            @Override
            public void onUploadResult(double speedMbps) {
            }
            
            @Override
            public void onError(String error) {
            }
            
            @Override
            public void onComplete() {
            }
        });
    }
    
    @Override
    protected void onDestroy() {
        super.onDestroy();
        prefs.edit()
            .putBoolean("lamp_enabled", switchLamp.isChecked())
            .putBoolean("display_enabled", switchDisplay.isChecked())
            .putBoolean("brightness_enabled", switchBrightness.isChecked())
            .apply();
        displayManager.close();
        if (executorService != null) {
            executorService.shutdown();
        }
    }
}
