package com.volcano.screen.ui;

import com.volcano.screen.R;
import com.volcano.screen.display.DisplayManager;
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
import com.volcano.screen.ui.LogActivity;
import com.volcano.screen.ui.AboutActivity;
import com.volcano.screen.network.NetworkSpeedTester;
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
            case DisplayManager.MODE_USB:
                radioUsb.setChecked(true);
                break;
            case DisplayManager.MODE_WIFI:
                radioWifi.setChecked(true);
                break;
            case DisplayManager.MODE_AUTO:
            default:
                radioAuto.setChecked(true);
                break;
        }
        
        String wifiAddress = displayManager.getWifiAddress();
        wifiAddressEdit.setText(wifiAddress);
        
        int wifiPort = displayManager.getWifiPort();
        wifiPortEdit.setText(String.valueOf(wifiPort));
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
        
        communicationModeGroup.setOnCheckedChangeListener((group, checkedId) -> {
            if (checkedId == R.id.radio_auto) {
                displayManager.setPreferredMode(DisplayManager.MODE_AUTO);
                Toast.makeText(this, "已设置为自动选择", Toast.LENGTH_SHORT).show();
            } else if (checkedId == R.id.radio_usb) {
                displayManager.setPreferredMode(DisplayManager.MODE_USB);
                Toast.makeText(this, "已设置为仅 USB", Toast.LENGTH_SHORT).show();
            } else if (checkedId == R.id.radio_wifi) {
                displayManager.setPreferredMode(DisplayManager.MODE_WIFI);
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
        
        String usbUrl = "http://localhost:8765";
        String wifiAddress = displayManager.getWifiAddress();
        int wifiPort = displayManager.getWifiPort();
        String wifiUrl = "http://" + wifiAddress + ":" + wifiPort;
        
        speedTester = new NetworkSpeedTester(resultText);
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
