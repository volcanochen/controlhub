package com.example.clockapp;

import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.widget.Button;
import android.widget.Switch;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;

public class SettingsActivity extends AppCompatActivity {
    
    private Switch switchLamp;
    private Switch switchDisplay;
    private Button viewLogButton;
    private Button aboutButton;
    private Button backButton;
    
    private SharedPreferences prefs;
    
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
