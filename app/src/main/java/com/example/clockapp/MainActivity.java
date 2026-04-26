package com.example.clockapp;

import androidx.appcompat.app.AppCompatActivity;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.BatteryManager;
import android.os.Bundle;
import android.os.Handler;
import android.view.View;
import android.view.WindowManager;
import android.widget.TextView;

import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.Locale;

public class MainActivity extends AppCompatActivity {

    private TextView timeText;
    private TextView dateText;
    private TextView dayText;
    private TextView batteryText;
    private Handler handler;
    private BroadcastReceiver batteryReceiver;

    private SimpleDateFormat timeFormat = new SimpleDateFormat("HH:mm:ss", Locale.getDefault());
    private SimpleDateFormat dateFormat = new SimpleDateFormat("yyyy年MM月dd日", Locale.getDefault());
    private SimpleDateFormat dayFormat = new SimpleDateFormat("EEEE", Locale.getDefault());

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        timeText = findViewById(R.id.time_text);
        dateText = findViewById(R.id.date_text);
        dayText = findViewById(R.id.day_text);
        batteryText = findViewById(R.id.battery_text);

        // 沉浸式模式
        getWindow().getDecorView().setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_LAYOUT_STABLE |
                View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION |
                View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN |
                View.SYSTEM_UI_FLAG_HIDE_NAVIGATION |
                View.SYSTEM_UI_FLAG_FULLSCREEN |
                View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
        );

        // 保持屏幕常亮
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);

        // 初始化电量监听
        setupBatteryReceiver();

        handler = new Handler();
        updateClock();
    }

    private void setupBatteryReceiver() {
        batteryReceiver = new BroadcastReceiver() {
            @Override
            public void onReceive(Context context, Intent intent) {
                int level = intent.getIntExtra(BatteryManager.EXTRA_LEVEL, -1);
                int scale = intent.getIntExtra(BatteryManager.EXTRA_SCALE, -1);
                int percentage = -1;
                if (level != -1 && scale != -1) {
                    percentage = (int) ((level / (float) scale) * 100);
                }
                
                int status = intent.getIntExtra(BatteryManager.EXTRA_STATUS, -1);
                boolean isCharging = status == BatteryManager.BATTERY_STATUS_CHARGING ||
                        status == BatteryManager.BATTERY_STATUS_FULL;
                
                String batteryStatus = isCharging ? "⚡" : "";
                batteryText.setText("电量: " + percentage + "%" + batteryStatus);
            }
        };
        
        IntentFilter filter = new IntentFilter(Intent.ACTION_BATTERY_CHANGED);
        registerReceiver(batteryReceiver, filter);
    }

    private void updateClock() {
        Calendar calendar = Calendar.getInstance();
        timeText.setText(timeFormat.format(calendar.getTime()));
        dateText.setText(dateFormat.format(calendar.getTime()));
        dayText.setText(dayFormat.format(calendar.getTime()));

        handler.postDelayed(new Runnable() {
            @Override
            public void run() {
                updateClock();
            }
        }, 1000);
    }

    @Override
    protected void onResume() {
        super.onResume();
        // 恢复沉浸式模式
        getWindow().getDecorView().setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_LAYOUT_STABLE |
                View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION |
                View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN |
                View.SYSTEM_UI_FLAG_HIDE_NAVIGATION |
                View.SYSTEM_UI_FLAG_FULLSCREEN |
                View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
        );
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        handler.removeCallbacksAndMessages(null);
        if (batteryReceiver != null) {
            unregisterReceiver(batteryReceiver);
        }
    }
}