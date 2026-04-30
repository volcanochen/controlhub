package com.volcano.screen.settings;

import com.volcano.screen.R;
import android.app.AlertDialog;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.widget.Button;
import android.widget.Switch;
import android.widget.TextView;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import com.volcano.screen.ui.LogActivity;
import com.volcano.screen.ui.AboutActivity;
import com.volcano.screen.speedtest.NetworkSpeedTester;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class SettingsActivity extends AppCompatActivity {
    
    private Switch switchLamp;
    private Switch switchDisplay;
    private Button viewLogButton;
    private Button aboutButton;
    private Button backButton;
    private Button networkSpeedButton;
    
    private SharedPreferences prefs;
    private NetworkSpeedTester speedTester;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_settings);
        
        // Initialize preferences
        prefs = getSharedPreferences("app_settings", MODE_PRIVATE);
        
        // Bind views
        switchLamp = findViewById(R.id.switch_lamp);
        switchDisplay = findViewById(R.id.switch_display);
        viewLogButton = findViewById(R.id.view_log_button);
        aboutButton = findViewById(R.id.about_button);
        backButton = findViewById(R.id.back_button);
        networkSpeedButton = findViewById(R.id.network_speed_button);
        
        // Load saved settings
        loadSettings();
        
        // Setup listeners
        setupListeners();
    }
    
    private void loadSettings() {
        // Load lamp control setting
        boolean lampEnabled = prefs.getBoolean("lamp_enabled", true);
        switchLamp.setChecked(lampEnabled);
        
        // Load display control setting
        boolean displayEnabled = prefs.getBoolean("display_enabled", true);
        switchDisplay.setChecked(displayEnabled);
    }
    
    private void setupListeners() {
        // View log button
        viewLogButton.setOnClickListener(v -> {
            Intent intent = new Intent(SettingsActivity.this, LogActivity.class);
            startActivity(intent);
        });
        
        // About button
        aboutButton.setOnClickListener(v -> {
            Intent intent = new Intent(SettingsActivity.this, AboutActivity.class);
            startActivity(intent);
        });
        
        // Lamp switch
        switchLamp.setOnCheckedChangeListener((buttonView, isChecked) -> {
            prefs.edit().putBoolean("lamp_enabled", isChecked).apply();
            Toast.makeText(this, 
                isChecked ? "台灯控制已启用" : "台灯控制已禁用", 
                Toast.LENGTH_SHORT).show();
        });
        
        // Display switch
        switchDisplay.setOnCheckedChangeListener((buttonView, isChecked) -> {
            prefs.edit().putBoolean("display_enabled", isChecked).apply();
            Toast.makeText(this, 
                isChecked ? "显示器控制已启用" : "显示器控制已禁用", 
                Toast.LENGTH_SHORT).show();
        });
        
        // Back button
        backButton.setOnClickListener(v -> {
            finish();
        });
        
        // Network speed test button
        networkSpeedButton.setOnClickListener(v -> {
            startNetworkSpeedTest();
        });
    }
    
    /**
     * 启动网速测试
     */
    private void startNetworkSpeedTest() {
        // 创建对话框
        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setTitle("网络速度测试 (USB连接)");
        
        // 创建结果显示TextView
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
        
        // 启动测试
        speedTester = new NetworkSpeedTester(resultText);
        speedTester.startFullTest(new NetworkSpeedTester.SpeedTestCallback() {
            @Override
            public void onPingResult(double avgLatency, double minLatency, double maxLatency) {
                // Ping测试结果已由NetworkSpeedTester处理
            }
            
            @Override
            public void onDownloadResult(double speedMbps) {
                // 下载测试结果已由NetworkSpeedTester处理
            }
            
            @Override
            public void onUploadResult(double speedMbps) {
                // 上传测试结果已由NetworkSpeedTester处理
            }
            
            @Override
            public void onError(String error) {
                // 错误已由NetworkSpeedTester处理
            }
            
            @Override
            public void onComplete() {
                // 测试完成
            }
        });
    }
    
    @Override
    protected void onDestroy() {
        super.onDestroy();
        // Save settings on destroy
        prefs.edit()
            .putBoolean("lamp_enabled", switchLamp.isChecked())
            .putBoolean("display_enabled", switchDisplay.isChecked())
            .apply();
    }
}
