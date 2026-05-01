# WiFi 通信功能测试说明

## 功能概述

本次开发为显示控制应用添加了 WiFi 通信功能，现在用户可以通过以下方式连接服务器：

1. **USB 连接**（原有的方式，通过 ADB reverse）
2. **WiFi 连接**（新增的方式，通过局域网）
3. **自动选择**（默认，优先 USB，失败时尝试 WiFi）

## 测试场景

### 场景 1：仅 USB 连接
**步骤：**
1. 用 USB 连接手机和电脑
2. 启动电脑端服务器 `python server/usb_display_control.py`
3. 在手机应用的设置中选择「仅 USB」
4. 测试显示器控制功能

**预期结果：**
- 状态按钮显示「Ready (USB)」
- 能够正常切换显示模式

### 场景 2：仅 WiFi 连接
**步骤：**
1. 确保手机和电脑在同一局域网
2. 启动电脑端服务器，记录显示的 IP 地址
3. 在手机应用的设置中选择「仅 WiFi」
4. 配置 WiFi 服务器地址为步骤 2 记录的 IP，端口保持 8765
5. 点击「测试连接」验证连接
6. 测试显示器控制功能

**预期结果：**
- 连接测试显示 WiFi 可用
- 状态按钮显示「Ready (WiFi)」
- 能够正常切换显示模式

### 场景 3：两者同时存在（自动选择）
**步骤：**
1. 同时连接 USB 和确保 WiFi 可用
2. 在设置中选择「自动选择」
3. 测试显示器控制功能

**预期结果：**
- 系统优先使用 USB 连接
- 状态按钮显示「Ready (USB)」

### 场景 4：通信方式切换
**步骤：**
1. 先使用一种方式连接并测试功能
2. 在设置中切换到另一种方式
3. 验证新方式是否正常工作

**预期结果：**
- 切换后能够自动重新连接
- 功能正常工作，上层业务逻辑无感知

## 修改文件列表

### Android 端（Java）

1. **新建文件：**
   - `app/src/main/java/com/volcano/screen/display/DisplayController.java` - 通信接口抽象
   - `app/src/main/java/com/volcano/screen/display/WifiDisplayController.java` - WiFi 通信实现
   - `app/src/main/java/com/volcano/screen/display/DisplayManager.java` - 通信方式管理器

2. **修改文件：**
   - `app/src/main/java/com/volcano/screen/display/WindowsDisplayController.java` - 实现 DisplayController 接口
   - `app/src/main/java/com/volcano/screen/settings/SettingsActivity.java` - 添加通信方式设置界面
   - `app/src/main/java/com/volcano/screen/ui/MainActivity.java` - 使用 DisplayManager 统一管理通信
   - `app/src/main/res/layout/activity_settings.xml` - 更新设置界面布局

### 服务器端（Python）

1. **修改文件：**
   - `server/usb_display_control.py` - 支持监听所有网络接口，显示本机 IP

## 架构设计

### 通信接口层
```
DisplayController (接口)
    ├── WindowsDisplayController (USB 实现)
    └── WifiDisplayController (WiFi 实现)
```

### 管理层
```
DisplayManager
    ├── 管理首选通信方式设置
    ├── 自动选择可用的通信方式
    ├── 提供统一的 DisplayController 实例
```

### 业务层
```
MainActivity
    └── 通过 DisplayManager 获取控制器
        └── 对通信方式完全透明
```

## 使用说明

### 配置 WiFi 连接

1. 启动电脑端服务器，查看控制台显示的「Local IP address」
2. 打开手机应用，点击右上角设置按钮
3. 在「通信方式」中选择「仅 WiFi」或「自动选择」
4. 在「WiFi 服务器地址」中输入步骤 1 看到的 IP 地址
5. 保持端口为 8765（或根据服务器配置修改）
6. 点击「测试连接」验证设置是否正确

### 通信方式优先级

- **自动选择模式：** 优先 USB，USB 不可用时尝试 WiFi
- **仅 USB 模式：** 只尝试 USB 连接
- **仅 WiFi 模式：** 只尝试 WiFi 连接

## 注意事项

1. **网络防火墙：** 使用 WiFi 连接时，确保电脑防火墙允许 8765 端口的入站连接
2. **同一网段：** 手机和电脑需要在同一局域网段
3. **IP 地址变化：** 电脑 IP 地址可能变化，变化时需要更新手机端设置
4. **USB 优先：** 在自动模式下，即使配置了 WiFi，只要 USB 可用就会优先使用 USB
