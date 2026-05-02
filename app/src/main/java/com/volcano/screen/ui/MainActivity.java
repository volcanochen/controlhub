package com.volcano.screen.ui;

import com.volcano.screen.R;
import androidx.appcompat.app.AppCompatActivity;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.SharedPreferences;
import android.os.BatteryManager;
import android.os.Bundle;
import android.os.Handler;
import android.view.View;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;
import com.volcano.screen.settings.SettingsActivity;
import com.volcano.screen.ui.LogActivity;
import com.volcano.screen.imagecast.ImageDisplayActivity;
import com.volcano.screen.display.DisplayController;
import com.volcano.screen.display.DisplayManager;
import com.volcano.screen.display.ImageCastingController;
import com.volcano.screen.display.BrightnessController;
import com.volcano.screen.miio.MiioDevice;

import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class MainActivity extends AppCompatActivity {

    private TextView timeText;
    private TextView dateText;
    private TextView dayText;
    private TextView batteryText;
    private TextView cpuText;
    private Button btnLampOn;
    private Button btnLampOff;
    private CheckBox switchMonitor1, switchMonitor2;
    private Button statusButton;
    private Button settingsButton;
    private Button imageDisplayButton;
    private LinearLayout contentContainer;
    private Button viewLogButton;
    private TextView debugInfo;
    private Handler handler;
    private BroadcastReceiver batteryReceiver;
    private Handler statusHandler;
    private Runnable statusUpdateRunnable;
    private ExecutorService executorService;
    
    private Handler autoPopupHandler;
    private Runnable autoPopupRunnable;
    private ImageCastingController imageCastingController;
    private boolean imageDisplayActivityOpen = false;
    private static final long AUTO_POPUP_INTERVAL = 2000;
    
    private DisplayManager displayManager;
    private BrightnessController brightnessController;
    
    private LinearLayout brightnessContainer;
    private TextView brightnessText;
    private TextView luxText;
    private CheckBox switchAutoBrightness;
    
    private boolean isUpdatingCheckBoxes = false;

    private SimpleDateFormat timeFormat;
    private SimpleDateFormat dateFormat;
    private SimpleDateFormat dayFormat;

    private long lastCpuTime = 0;
    private long lastAppTime = 0;
    
    private int burnInOffsetX = 0;
    private int burnInOffsetY = 0;
    private int burnInDirection = 0;
    private long lastBurnInUpdate = 0;
    private static final int BURN_IN_MAX_OFFSET = 10;
    private static final long BURN_IN_UPDATE_INTERVAL = 30000;

    private static final String LAMP_IP = "192.168.50.229";
    private static final String LAMP_TOKEN = "f35a3dadd842eaf04e52f4e0781367b9";
    
    private static final long STATUS_UPDATE_INTERVAL = 10000;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        
        displayManager = new DisplayManager(this);

        brightnessController = new BrightnessController(this, new BrightnessController.BrightnessCallback() {
            @Override
            public void onBrightnessChanged(float lux, int brightnessPercent) {
                runOnUiThread(() -> {
                    brightnessText.setText("亮度: " + brightnessPercent + "%");
                    luxText.setText(String.format("光照: %.0f lux", lux));
                });
            }

            @Override
            public void onSensorUnavailable() {
                runOnUiThread(() -> {
                    brightnessContainer.setVisibility(View.GONE);
                    Toast.makeText(MainActivity.this, "此设备没有光线传感器", Toast.LENGTH_SHORT).show();
                });
            }
        });

        String timeFormatStr = getString(R.string.time_format);
        String dateFormatStr = getString(R.string.date_format);
        String dayFormatStr = getString(R.string.day_format);
        timeFormat = new SimpleDateFormat(timeFormatStr, Locale.getDefault());
        dateFormat = new SimpleDateFormat(dateFormatStr, Locale.getDefault());
        dayFormat = new SimpleDateFormat(dayFormatStr, Locale.getDefault());

        timeText = findViewById(R.id.time_text);
        dateText = findViewById(R.id.date_text);
        dayText = findViewById(R.id.day_text);
        batteryText = findViewById(R.id.battery_text);
        cpuText = findViewById(R.id.cpu_text);
        btnLampOn = findViewById(R.id.btn_lamp_on);
        btnLampOff = findViewById(R.id.btn_lamp_off);
        switchMonitor1 = findViewById(R.id.switch_monitor1);
        switchMonitor2 = findViewById(R.id.switch_monitor2);
        statusButton = findViewById(R.id.status_button);
        settingsButton = findViewById(R.id.settings_button);
        imageDisplayButton = findViewById(R.id.image_display_btn);
        viewLogButton = findViewById(R.id.view_log_button);
        debugInfo = findViewById(R.id.debug_info);
        contentContainer = findViewById(R.id.content_container);
        
        brightnessContainer = findViewById(R.id.brightness_container);
        brightnessText = findViewById(R.id.brightness_text);
        luxText = findViewById(R.id.lux_text);
        switchAutoBrightness = findViewById(R.id.switch_auto_brightness);
        
        settingsButton.setOnClickListener(v -> {
            Intent intent = new Intent(MainActivity.this, SettingsActivity.class);
            startActivity(intent);
        });
        
        imageDisplayButton.setOnClickListener(v -> {
            Intent intent = new Intent(MainActivity.this, ImageDisplayActivity.class);
            startActivity(intent);
        });

        statusButton.setOnClickListener(v -> {
            debugInfo.setText("调试信息:\n正在检查服务器...");
            if (viewLogButton.getVisibility() == View.GONE) {
                viewLogButton.setVisibility(View.VISIBLE);
            }
            checkServerManually();
        });

        viewLogButton.setOnClickListener(v -> {
            if (debugInfo.getVisibility() == View.GONE) {
                debugInfo.setVisibility(View.VISIBLE);
            } else {
                debugInfo.setVisibility(View.GONE);
            }
        });

        switchMonitor1.setOnCheckedChangeListener((buttonView, isChecked) -> {
            if (!isUpdatingCheckBoxes) {
                handleMonitorSwitch();
            }
        });

        switchMonitor2.setOnCheckedChangeListener((buttonView, isChecked) -> {
            if (!isUpdatingCheckBoxes) {
                handleMonitorSwitch();
            }
        });

        executorService = Executors.newSingleThreadExecutor();
        statusHandler = new Handler();
        autoPopupHandler = new Handler();
        imageCastingController = new ImageCastingController();
        
        startStatusUpdate();
        startAutoPopupPolling();

        getWindow().getDecorView().setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_LAYOUT_STABLE |
                View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION |
                View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN |
                View.SYSTEM_UI_FLAG_HIDE_NAVIGATION |
                View.SYSTEM_UI_FLAG_FULLSCREEN |
                View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
        );

        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);

        setupBatteryReceiver();
        setupLampControls();

        switchAutoBrightness.setOnCheckedChangeListener((buttonView, isChecked) -> {
            brightnessController.setEnabled(isChecked);
            if (isChecked) {
                Toast.makeText(MainActivity.this, "自动亮度已开启", Toast.LENGTH_SHORT).show();
            } else {
                Toast.makeText(MainActivity.this, "自动亮度已关闭", Toast.LENGTH_SHORT).show();
            }
        });

        handler = new Handler();
        updateClock();
        
        checkFeatureSettings();
    }

    private void checkFeatureSettings() {
        SharedPreferences prefs = getSharedPreferences("app_settings", MODE_PRIVATE);
        boolean lampEnabled = prefs.getBoolean("lamp_enabled", true);
        boolean displayEnabled = prefs.getBoolean("display_enabled", true);
        boolean brightnessEnabled = prefs.getBoolean("brightness_enabled", true);
        
        if (btnLampOn != null && btnLampOff != null) {
            int lampVisibility = lampEnabled ? View.VISIBLE : View.GONE;
            btnLampOn.setVisibility(lampVisibility);
            btnLampOff.setVisibility(lampVisibility);
        }
        
        if (switchMonitor1 != null && switchMonitor2 != null) {
            int displayVisibility = displayEnabled ? View.VISIBLE : View.GONE;
            View monitor1Layout = (View) switchMonitor1.getParent();
            monitor1Layout.setVisibility(displayVisibility);
            View monitor2Layout = (View) switchMonitor2.getParent();
            monitor2Layout.setVisibility(displayVisibility);
            statusButton.setVisibility(displayVisibility);
        }

        if (brightnessContainer != null) {
            if (brightnessEnabled && brightnessController.isSensorAvailable()) {
                brightnessContainer.setVisibility(View.VISIBLE);
                switchAutoBrightness.setChecked(brightnessController.isEnabled());
            } else {
                brightnessContainer.setVisibility(View.GONE);
            }
        }
    }

    private void setupLampControls() {
        btnLampOn.setOnClickListener(v -> controlLamp(true));
        btnLampOff.setOnClickListener(v -> controlLamp(false));
    }

    private void handleMonitorSwitch() {
        if (!switchMonitor1.isChecked() && !switchMonitor2.isChecked()) {
            switchMonitor1.setChecked(true);
        }
        setMonitorMode(switchMonitor1.isChecked(), switchMonitor2.isChecked());
    }

    private void setMonitorMode(boolean monitor1On, boolean monitor2On) {
        executorService.execute(() -> {
            try {
                DisplayController controller = displayManager.getController();
                if (monitor1On && !monitor2On) {
                    controller.setDisplayMode(DisplayManager.MODE_PRIMARY_ONLY);
                } else if (!monitor1On && monitor2On) {
                    controller.setDisplayMode(DisplayManager.MODE_SECONDARY_ONLY);
                } else if (monitor1On && monitor2On) {
                    controller.setDisplayMode(DisplayManager.MODE_EXTENDED);
                }
                
                runOnUiThread(() -> Toast.makeText(MainActivity.this, "显示器模式已更新 (" + controller.getConnectionType() + ")", Toast.LENGTH_SHORT).show());
            } catch (final Exception e) {
                e.printStackTrace();
                runOnUiThread(() -> Toast.makeText(MainActivity.this, "切换失败：" + e.getMessage(), Toast.LENGTH_SHORT).show());
            }
        });
    }

    private void controlLamp(final boolean on) {
        executorService.execute(() -> {
            try {
                MiioDevice device = new MiioDevice(LAMP_IP, LAMP_TOKEN);
                
                if (device.handshake()) {
                    device.sendCommand("set_power", new Object[]{on ? "on" : "off"});
                    final String message = on ? "台灯已开启" : "台灯已关闭";
                    runOnUiThread(() -> Toast.makeText(MainActivity.this, message, Toast.LENGTH_SHORT).show());
                } else {
                    runOnUiThread(() -> Toast.makeText(MainActivity.this, "连接设备失败", Toast.LENGTH_SHORT).show());
                }
                
                device.close();
            } catch (final Exception e) {
                e.printStackTrace();
                runOnUiThread(() -> Toast.makeText(MainActivity.this, "控制失败：" + e.getMessage(), Toast.LENGTH_SHORT).show());
            }
        });
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

        updateCpuUsage();
        updateBurnInOffset();

        handler.postDelayed(this::updateClock, 1000);
    }
    
    private void updateBurnInOffset() {
        long currentTime = System.currentTimeMillis();
        if (currentTime - lastBurnInUpdate < BURN_IN_UPDATE_INTERVAL) {
            return;
        }
        lastBurnInUpdate = currentTime;
        
        burnInDirection = (burnInDirection + 1) % 4;
        
        java.util.Random random = new java.util.Random();
        burnInOffsetX = random.nextInt(BURN_IN_MAX_OFFSET * 2 + 1) - BURN_IN_MAX_OFFSET;
        burnInOffsetY = random.nextInt(BURN_IN_MAX_OFFSET * 2 + 1) - BURN_IN_MAX_OFFSET;
        
        contentContainer.setTranslationX(burnInOffsetX);
        contentContainer.setTranslationY(burnInOffsetY);
    }

    private void startStatusUpdate() {
        statusUpdateRunnable = new Runnable() {
            @Override
            public void run() {
                updateServerStatus();
                statusHandler.postDelayed(this, STATUS_UPDATE_INTERVAL);
            }
        };
        statusHandler.post(statusUpdateRunnable);
    }
    
    private void startAutoPopupPolling() {
        autoPopupRunnable = new Runnable() {
            @Override
            public void run() {
                checkAutoPopup();
                autoPopupHandler.postDelayed(this, AUTO_POPUP_INTERVAL);
            }
        };
        autoPopupHandler.post(autoPopupRunnable);
    }
    
    private void stopAutoPopupPolling() {
        if (autoPopupHandler != null && autoPopupRunnable != null) {
            autoPopupHandler.removeCallbacks(autoPopupRunnable);
        }
    }
    
    private void checkAutoPopup() {
        if (imageDisplayActivityOpen) {
            return;
        }
        
        executorService.execute(() -> {
            try {
                ImageCastingController.ImageStatus status = imageCastingController.getImageStatus();
                
                if (status.hasImage && status.autoPopup) {
                    imageCastingController.ackAutoPopup();
                    
                    runOnUiThread(() -> {
                        if (!imageDisplayActivityOpen) {
                            Intent intent = new Intent(MainActivity.this, ImageDisplayActivity.class);
                            startActivity(intent);
                            imageDisplayActivityOpen = true;
                        }
                    });
                }
            } catch (Exception e) {
            }
        });
    }
    
    private void updateServerStatus() {
        executorService.execute(() -> {
            try {
                DisplayController controller = displayManager.getController();
                int mode = controller.getCurrentMode();
                final String connectionType = controller.getConnectionType();
                
                runOnUiThread(() -> {
                    statusButton.setText("Ready (" + connectionType + ")");
                    statusButton.setSelected(true);
                    updateCheckBoxesFromMode(mode);
                });
            } catch (Exception e) {
                runOnUiThread(() -> {
                    statusButton.setText("Not Ready");
                    statusButton.setSelected(false);
                });
            }
        });
    }
    
    private void updateCheckBoxesFromMode(int mode) {
        isUpdatingCheckBoxes = true;
        
        switch (mode) {
            case DisplayManager.MODE_PRIMARY_ONLY:
                switchMonitor1.setChecked(true);
                switchMonitor2.setChecked(false);
                break;
            case DisplayManager.MODE_SECONDARY_ONLY:
                switchMonitor1.setChecked(false);
                switchMonitor2.setChecked(true);
                break;
            case DisplayManager.MODE_EXTENDED:
            case DisplayManager.MODE_DUPLICATE:
                switchMonitor1.setChecked(true);
                switchMonitor2.setChecked(true);
                break;
            default:
                switchMonitor1.setChecked(true);
                switchMonitor2.setChecked(true);
                break;
        }
        
        isUpdatingCheckBoxes = false;
    }

    private void checkServerManually() {
        executorService.execute(() -> {
            StringBuilder debugMsg = new StringBuilder();
            debugMsg.append("调试信息:\n");
            debugMsg.append("1. 开始检查服务器...\n");
            
            try {
                debugMsg.append("2. 尝试连接...\n");
                runOnUiThread(() -> debugInfo.setText(debugMsg.toString()));
                
                DisplayController controller = displayManager.getController();
                int mode = controller.getCurrentMode();
                
                debugMsg.append("3. 连接成功！(").append(controller.getConnectionType()).append(")\n");
                debugMsg.append("4. 服务器返回模式：").append(modeToString(mode)).append("\n");
                debugMsg.append("5. 服务器状态：Ready ✓\n");
                
                final int finalMode = mode;
                final String finalConnectionType = controller.getConnectionType();
                runOnUiThread(() -> {
                    debugInfo.setText(debugMsg.toString());
                    statusButton.setText("Ready (" + finalConnectionType + ")");
                    statusButton.setSelected(true);
                    updateCheckBoxesFromMode(finalMode);
                });
                
            } catch (Exception e) {
                debugMsg.append("3. 连接失败！\n");
                debugMsg.append("错误：").append(e.getMessage()).append("\n");
                debugMsg.append("4. 服务器状态：Not Ready ✗\n");
                debugMsg.append("5. 请检查连接设置\n");
                
                runOnUiThread(() -> {
                    debugInfo.setText(debugMsg.toString());
                    statusButton.setText("Not Ready");
                    statusButton.setSelected(false);
                });
            }
        });
    }
    
    private String modeToString(int mode) {
        switch (mode) {
            case DisplayManager.MODE_PRIMARY_ONLY:
                return "第一屏 (internal)";
            case DisplayManager.MODE_SECONDARY_ONLY:
                return "第二屏 (external)";
            case DisplayManager.MODE_EXTENDED:
                return "扩展模式 (extend)";
            case DisplayManager.MODE_DUPLICATE:
                return "复制模式 (clone)";
            default:
                return "未知模式";
        }
    }

    private void updateCpuUsage() {
        executorService.execute(() -> {
            try {
                final StringBuilder sb = new StringBuilder();
                
                Runtime runtime = Runtime.getRuntime();
                long usedMemory = (runtime.totalMemory() - runtime.freeMemory()) / 1024 / 1024;
                long maxMemory = runtime.maxMemory() / 1024 / 1024;
                
                sb.append("内存: ").append(usedMemory).append("/").append(maxMemory).append("MB");
                
                double cpuUsage = tryGetCpuUsage();
                if (cpuUsage >= 0) {
                    sb.append(" | CPU: ").append(String.format(Locale.getDefault(), "%.1f%%", cpuUsage));
                }
                
                final String result = sb.toString();
                runOnUiThread(() -> cpuText.setText(result));
            } catch (Exception e) {
                e.printStackTrace();
            }
        });
    }

    private double tryGetCpuUsage() {
        try {
            if (lastCpuTime == 0) {
                lastCpuTime = System.nanoTime();
                lastAppTime = readAppCpuTime();
                return -1;
            }

            long currentTime = System.nanoTime();
            long currentAppTime = readAppCpuTime();

            long timeDiff = currentTime - lastCpuTime;
            long appTimeDiff = currentAppTime - lastAppTime;

            if (timeDiff > 0 && appTimeDiff >= 0) {
                double usage = (appTimeDiff * 100.0) / timeDiff;
                lastCpuTime = currentTime;
                lastAppTime = currentAppTime;
                return Math.min(usage, 100.0);
            }
            return -1;
        } catch (Exception e) {
            return -1;
        }
    }

    private long readAppCpuTime() {
        try {
            int pid = android.os.Process.myPid();
            java.io.BufferedReader reader = new java.io.BufferedReader(
                    new java.io.FileReader("/proc/" + pid + "/stat"));
            String line = reader.readLine();
            reader.close();

            if (line != null) {
                String[] parts = line.split("\\s+");
                if (parts.length > 16) {
                    long utime = Long.parseLong(parts[13]);
                    long stime = Long.parseLong(parts[14]);
                    return (utime + stime) * 10000000;
                }
            }
        } catch (Exception e) {
        }
        return -1;
    }

    @Override
    protected void onResume() {
        super.onResume();
        getWindow().getDecorView().setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_LAYOUT_STABLE |
                View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION |
                View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN |
                View.SYSTEM_UI_FLAG_HIDE_NAVIGATION |
                View.SYSTEM_UI_FLAG_FULLSCREEN |
                View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
        );
        checkFeatureSettings();
        displayManager.resetController();
        if (brightnessController.isEnabled() && brightnessController.isSensorAvailable()) {
            brightnessController.start();
        }
        imageDisplayActivityOpen = false;
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        handler.removeCallbacksAndMessages(null);
        
        if (statusHandler != null && statusUpdateRunnable != null) {
            statusHandler.removeCallbacks(statusUpdateRunnable);
        }
        
        stopAutoPopupPolling();
        
        if (batteryReceiver != null) {
            unregisterReceiver(batteryReceiver);
        }
        if (executorService != null) {
            executorService.shutdown();
        }
        displayManager.close();
        brightnessController.destroy();
    }
}
