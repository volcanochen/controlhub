package com.example.clockapp;

import android.os.Bundle;
import android.widget.Button;
import android.widget.TextView;
import androidx.appcompat.app.AppCompatActivity;

public class AboutActivity extends AppCompatActivity {
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_about);
        
        // Display version
        TextView versionText = findViewById(R.id.version_text);
        String versionName = getString(R.string.app_version);
        versionText.setText("版本：" + versionName);
        
        // Back button
        Button backButton = findViewById(R.id.back_button);
        backButton.setOnClickListener(v -> {
            finish();
        });
    }
}
