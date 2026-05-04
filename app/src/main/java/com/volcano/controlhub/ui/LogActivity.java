package com.volcano.controlhub.ui;

import com.volcano.controlhub.R;
import android.os.Bundle;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

public class LogActivity extends AppCompatActivity {
    
    private TextView logContent;
    private Button clearLogButton;
    private Button backButton;
    
    private static final String LOG_TAG = "ClockApp";
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_log);
        
        logContent = findViewById(R.id.log_content);
        clearLogButton = findViewById(R.id.clear_log_button);
        backButton = findViewById(R.id.back_button);
        
        displayLogs();
        
        clearLogButton.setOnClickListener(v -> {
            clearLogs();
            displayLogs();
            Toast.makeText(this, "日志已清空", Toast.LENGTH_SHORT).show();
        });
        
        backButton.setOnClickListener(v -> {
            finish();
        });
    }
    
    private void displayLogs() {
        StringBuilder logs = new StringBuilder();
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault());
        
        try {
            Process process = Runtime.getRuntime().exec("logcat -d");
            BufferedReader bufferedReader = new BufferedReader(
                new InputStreamReader(process.getInputStream())
            );
            
            String line;
            int count = 0;
            int maxLines = 200;
            
            while ((line = bufferedReader.readLine()) != null) {
                if (line.contains(LOG_TAG) || line.contains("ClockApp")) {
                    logs.append(line).append("\n");
                    count++;
                    if (count >= maxLines) break;
                }
            }
            
            if (logs.length() == 0) {
                logs.append("暂无相关日志\n");
                logs.append("\n提示：操作应用后会在这里显示日志");
            }
            
        } catch (Exception e) {
            logs.append("读取日志失败：").append(e.getMessage()).append("\n");
        }
        
        logContent.setText(logs.toString());
    }
    
    private void clearLogs() {
        try {
            Runtime.getRuntime().exec("logcat -c");
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
