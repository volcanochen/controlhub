package com.example.clockapp;

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
    private LinearLayout contentContainer;
    private Button viewLogButton;
    private TextView debugInfo;
    private Handler handler;
    private BroadcastReceiver batteryReceiver;
    private Handler statusHandler;
    private Runnable statusUpdateRunnable;
    private ExecutorService executorService;
    
    // 标志位：防止 CheckBox 更新时触发监听器
    private boolean isUpdatingCheckBoxes = false;

    private SimpleDateFormat timeFormat;
    private SimpleDateFormat dateFormat;
    private SimpleDateFormat dayFormat;

    private long lastCpuTime = 0;
    private long lastAppTime = 0;
    
    // OLED 防烧屏位移
    private int burnInOffsetX = 0;
    private int burnInOffsetY = 0;
    private int burnInDirection = 0; // 0:右下，1:左上，2:右上，3:左下
    private long lastBurnInUpdate = 0;
    private static final int BURN_IN_MAX_OFFSET = 10; // 最大位移像素
    private static final long BURN_IN_UPDATE_INTERVAL = 30000; // 每 30 秒位移一次

    // 在这里配置你的台灯 IP 和 Token
    private static final String LAMP_IP = "192.168.50.229";  // 改成你的台灯 IP
    private static final String LAMP_TOKEN = "f35a3dadd842eaf04e52f4e0781367b9";  // 改成你的 Token
    
    // 显示器状态更新间隔（毫秒）
    private static final long STATUS_UPDATE_INTERVAL = 10000; // 10 秒

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        // 初始化日期时间格式（使用 strings.xml 中的统一定义）
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
        viewLogButton = findViewById(R.id.view_log_button);
        debugInfo = findViewById(R.id.debug_info);
        contentContainer = findViewById(R.id.content_container);

        // 设置按钮点击事件
        settingsButton.setOnClickListener(v -> {
            Intent intent = new Intent(MainActivity.this, SettingsActivity.class);
            startActivity(intent);
        });

        // 状态按钮点击事件 - 手动检查服务器
        statusButton.setOnClickListener(v -> {
            debugInfo.setText("调试信息:\n正在检查服务器...");
            if (viewLogButton.getVisibility() == View.GONE) {
                viewLogButton.setVisibility(View.VISIBLE);
            }
            checkServerManually();
        });

        // 查看日志按钮点击事件
        viewLogButton.setOnClickListener(v -> {
            if (debugInfo.getVisibility() == View.GONE) {
                debugInfo.setVisibility(View.VISIBLE);
            } else {
                debugInfo.setVisibility(View.GONE);
            }
        });

        // CheckBox 监听逻辑 - 显示器切换
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
        
        // 启动状态更新（每 10 秒轮询）
        startStatusUpdate();

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

        // 初始化台灯控制按钮
        setupLampControls();

        handler = new Handler();
        updateClock();
        
        // 根据设置检查是否显示台灯控制
        checkFeatureSettings();
    }

    /**
     * 检查功能设置，隐藏已禁用的功能
     */
    private void checkFeatureSettings() {
        SharedPreferences prefs = getSharedPreferences("app_settings", MODE_PRIVATE);
        boolean lampEnabled = prefs.getBoolean("lamp_enabled", true);
        boolean displayEnabled = prefs.getBoolean("display_enabled", true);
        
        // 隐藏/显示台灯控制按钮
        if (btnLampOn != null && btnLampOff != null) {
            int lampVisibility = lampEnabled ? View.VISIBLE : View.GONE;
            btnLampOn.setVisibility(lampVisibility);
            btnLampOff.setVisibility(lampVisibility);
        }
        
        // 隐藏/显示器控制（包括文字和 checkbox）
        if (switchMonitor1 != null && switchMonitor2 != null) {
            int displayVisibility = displayEnabled ? View.VISIBLE : View.GONE;
            // 隐藏/显示第一屏（文字 + 复选框）
            View monitor1Layout = (View) switchMonitor1.getParent();
            monitor1Layout.setVisibility(displayVisibility);
            // 隐藏/显示第二屏（文字 + 复选框）
            View monitor2Layout = (View) switchMonitor2.getParent();
            monitor2Layout.setVisibility(displayVisibility);
            // 隐藏/显示状态按钮
            statusButton.setVisibility(displayVisibility);
        }
    }



    private void setupLampControls() {
        btnLampOn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                controlLamp(true);
            }
        });

        btnLampOff.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                controlLamp(false);
            }
        });
    }

    /**
     * 处理显示器开关切换
     */
    private void handleMonitorSwitch() {
        // 如果两个都未选中，强制选中第一个（不能全关）
        if (!switchMonitor1.isChecked() && !switchMonitor2.isChecked()) {
            switchMonitor1.setChecked(true);
        }

        // 执行显示器切换
        setMonitorMode(switchMonitor1.isChecked(), switchMonitor2.isChecked());
    }

    /**
     * 设置显示器模式
     */
    private void setMonitorMode(boolean monitor1On, boolean monitor2On) {
        executorService.execute(new Runnable() {
            @Override
            public void run() {
                try {
                    WindowsDisplayController controller = new WindowsDisplayController();
                    if (monitor1On && !monitor2On) {
                        // 仅第一屏
                        controller.setDisplayMode(WindowsDisplayController.MODE_PRIMARY_ONLY);
                    } else if (!monitor1On && monitor2On) {
                        // 仅第二屏
                        controller.setDisplayMode(WindowsDisplayController.MODE_SECONDARY_ONLY);
                    } else if (monitor1On && monitor2On) {
                        // 双屏扩展
                        controller.setDisplayMode(WindowsDisplayController.MODE_EXTENDED);
                    }
                    controller.close();
                    
                    runOnUiThread(new Runnable() {
                        @Override
                        public void run() {
                            Toast.makeText(MainActivity.this, "显示器模式已更新", Toast.LENGTH_SHORT).show();
                        }
                    });
                } catch (final Exception e) {
                    e.printStackTrace();
                    runOnUiThread(new Runnable() {
                        @Override
                        public void run() {
                            Toast.makeText(MainActivity.this, "切换失败：" + e.getMessage(), Toast.LENGTH_SHORT).show();
                        }
                    });
                }
            }
        });
    }

    private void switchMonitor(final int monitorId) {
        // 此方法已废弃，使用 handleMonitorSwitch 替代
    }

    private void controlLamp(final boolean on) {
        executorService.execute(new Runnable() {
            @Override
            public void run() {
                try {
                    MiioDevice device = new MiioDevice(LAMP_IP, LAMP_TOKEN);
                    
                    if (device.handshake()) {
                        String result = device.sendCommand("set_power", new Object[]{on ? "on" : "off"});
                        final String message = on ? "台灯已开启" : "台灯已关闭";
                        
                        runOnUiThread(new Runnable() {
                            @Override
                            public void run() {
                                Toast.makeText(MainActivity.this, message, Toast.LENGTH_SHORT).show();
                            }
                        });
                    } else {
                        runOnUiThread(new Runnable() {
                            @Override
                            public void run() {
                                Toast.makeText(MainActivity.this, "连接设备失败", Toast.LENGTH_SHORT).show();
                            }
                        });
                    }
                    
                    device.close();
                } catch (final Exception e) {
                    e.printStackTrace();
                    runOnUiThread(new Runnable() {
                        @Override
                        public void run() {
                            Toast.makeText(MainActivity.this, "控制失败: " + e.getMessage(), Toast.LENGTH_SHORT).show();
                        }
                    });
                }
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

        // 更新CPU使用率
        updateCpuUsage();
        
        // OLED防烧屏位移
        updateBurnInOffset();

        handler.postDelayed(new Runnable() {
            @Override
            public void run() {
                updateClock();
            }
        }, 1000);
    }
    
    private void updateBurnInOffset() {
        long currentTime = System.currentTimeMillis();
        if (currentTime - lastBurnInUpdate < BURN_IN_UPDATE_INTERVAL) {
            return;
        }
        lastBurnInUpdate = currentTime;
        
        // 随机或有规律地改变方向和偏移量
        burnInDirection = (burnInDirection + 1) % 4;
        
        // 随机生成新的偏移量（在最大范围内）
        java.util.Random random = new java.util.Random();
        burnInOffsetX = random.nextInt(BURN_IN_MAX_OFFSET * 2 + 1) - BURN_IN_MAX_OFFSET;
        burnInOffsetY = random.nextInt(BURN_IN_MAX_OFFSET * 2 + 1) - BURN_IN_MAX_OFFSET;
        
        // 应用位移
        contentContainer.setTranslationX(burnInOffsetX);
        contentContainer.setTranslationY(burnInOffsetY);
    }

    /**
     * 启动状态更新循环
     */
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

    /**
     * 更新服务器连接状态
     */
    private void updateServerStatus() {
        executorService.execute(new Runnable() {
            @Override
            public void run() {
                try {
                    // 先尝试获取状态，如果能获取到状态，说明服务器在线
                    WindowsDisplayController controller = new WindowsDisplayController();
                    int mode = controller.getCurrentMode();
                    controller.close();
                    
                    runOnUiThread(new Runnable() {
                        @Override
                        public void run() {
                            // 服务器连接成功 - 更新状态按钮为 Ready
                            statusButton.setText("Ready");
                            statusButton.setSelected(true); // 绿色背景
                            
                            // 根据显示器模式更新 CheckBox 状态
                            updateCheckBoxesFromMode(mode);
                        }
                    });
                } catch (Exception e) {
                    runOnUiThread(new Runnable() {
                        @Override
                        public void run() {
                            // 服务器未连接或不可达 - 更新状态按钮为 Not Ready
                            statusButton.setText("Not Ready");
                            statusButton.setSelected(false); // 灰色背景
                        }
                    });
                }
            }
        });
    }
    
    /**
     * 根据显示器模式更新 CheckBox 状态
     */
    private void updateCheckBoxesFromMode(int mode) {
        isUpdatingCheckBoxes = true;  // 禁用监听器
        
        switch (mode) {
            case WindowsDisplayController.MODE_PRIMARY_ONLY:
                // 仅第一屏
                switchMonitor1.setChecked(true);
                switchMonitor2.setChecked(false);
                break;
            case WindowsDisplayController.MODE_SECONDARY_ONLY:
                // 仅第二屏
                switchMonitor1.setChecked(false);
                switchMonitor2.setChecked(true);
                break;
            case WindowsDisplayController.MODE_EXTENDED:
                // 双屏扩展
                switchMonitor1.setChecked(true);
                switchMonitor2.setChecked(true);
                break;
            case WindowsDisplayController.MODE_DUPLICATE:
                // 复制模式（视为双屏）
                switchMonitor1.setChecked(true);
                switchMonitor2.setChecked(true);
                break;
            default:
                // 默认双屏扩展
                switchMonitor1.setChecked(true);
                switchMonitor2.setChecked(true);
                break;
        }
        
        isUpdatingCheckBoxes = false;  // 恢复监听器
    }

    /**
     * 手动检查服务器
     */
    private void checkServerManually() {
        executorService.execute(new Runnable() {
            @Override
            public void run() {
                StringBuilder debugMsg = new StringBuilder();
                debugMsg.append("调试信息:\n");
                debugMsg.append("1. 开始检查服务器...\n");
                
                try {
                    // 步骤 1: 检查网络连接
                    debugMsg.append("2. 尝试连接 http://localhost:8765/status\n");
                    runOnUiThread(() -> debugInfo.setText(debugMsg.toString()));
                    
                    WindowsDisplayController controller = new WindowsDisplayController();
                    int mode = controller.getCurrentMode();
                    controller.close();
                    
                    debugMsg.append("3. 连接成功!\n");
                    debugMsg.append("4. 服务器返回模式：").append(modeToString(mode)).append("\n");
                    debugMsg.append("5. 服务器状态：Ready ✓\n");
                    
                    final int finalMode = mode;
                    runOnUiThread(new Runnable() {
                        @Override
                        public void run() {
                            debugInfo.setText(debugMsg.toString());
                            // 更新状态按钮
                            statusButton.setText("Ready");
                            statusButton.setSelected(true);
                            // 根据显示器模式更新 CheckBox 状态
                            updateCheckBoxesFromMode(finalMode);
                        }
                    });
                    
                } catch (Exception e) {
                    debugMsg.append("3. 连接失败!\n");
                    debugMsg.append("错误：").append(e.getMessage()).append("\n");
                    debugMsg.append("4. 服务器状态：Not Ready ✗\n");
                    debugMsg.append("5. 请检查:\n");
                    debugMsg.append("   - USB 连接是否正常\n");
                    debugMsg.append("   - ADB reverse 是否设置\n");
                    debugMsg.append("   - 电脑端服务器是否运行");
                    
                    runOnUiThread(new Runnable() {
                        @Override
                        public void run() {
                            debugInfo.setText(debugMsg.toString());
                            // 更新状态按钮
                            statusButton.setText("Not Ready");
                            statusButton.setSelected(false);
                        }
                    });
                }
            }
        });
    }
    
    /**
     * 模式转换为字符串
     */
    private String modeToString(int mode) {
        switch (mode) {
            case WindowsDisplayController.MODE_PRIMARY_ONLY:
                return "第一屏 (internal)";
            case WindowsDisplayController.MODE_SECONDARY_ONLY:
                return "第二屏 (external)";
            case WindowsDisplayController.MODE_EXTENDED:
                return "扩展模式 (extend)";
            case WindowsDisplayController.MODE_DUPLICATE:
                return "复制模式 (clone)";
            default:
                return "未知模式";
        }
    }

    private void updateCpuUsage() {
        executorService.execute(new Runnable() {
            @Override
            public void run() {
                try {
                    final StringBuilder sb = new StringBuilder();
                    
                    // 获取内存信息（兼容性最好）
                    Runtime runtime = Runtime.getRuntime();
                    long usedMemory = (runtime.totalMemory() - runtime.freeMemory()) / 1024 / 1024;
                    long maxMemory = runtime.maxMemory() / 1024 / 1024;
                    
                    sb.append("内存: ").append(usedMemory).append("/").append(maxMemory).append("MB");
                    
                    // 尝试获取CPU信息
                    double cpuUsage = tryGetCpuUsage();
                    if (cpuUsage >= 0) {
                        sb.append(" | CPU: ").append(String.format(Locale.getDefault(), "%.1f%%", cpuUsage));
                    }
                    
                    final String result = sb.toString();
                    runOnUiThread(new Runnable() {
                        @Override
                        public void run() {
                            cpuText.setText(result);
                        }
                    });
                } catch (Exception e) {
                    e.printStackTrace();
                }
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
                    // 单位是时钟滴答，转换为纳秒（假设100滴答/秒）
                    return (utime + stime) * 10000000;
                }
            }
        } catch (Exception e) {
            // 忽略错误
        }
        return -1;
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
        // 刷新功能显示状态
        checkFeatureSettings();
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        handler.removeCallbacksAndMessages(null);
        
        // 停止状态更新
        if (statusHandler != null && statusUpdateRunnable != null) {
            statusHandler.removeCallbacks(statusUpdateRunnable);
        }
        
        if (batteryReceiver != null) {
            unregisterReceiver(batteryReceiver);
        }
        if (executorService != null) {
            executorService.shutdown();
        }
    }
}