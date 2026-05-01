# 检查、构建、测试和上机演示计划

## 1. 代码检查完成情况

### 已完成的检查
✅ **新增文件完整** - DisplayController、WifiDisplayController、DisplayManager 已正确实现
✅ **接口实现正确** - WindowsDisplayController 已完整实现 DisplayController 接口
✅ **Android权限已配置** - INTERNET、ACCESS_WIFI_STATE、ACCESS_NETWORK_STATE 权限已配置
✅ **使用明文流量已启用** - AndroidManifest.xml 中的 `usesCleartextTraffic="true"` 已设置
✅ **构建文件完整** - build.gradle、settings.gradle 配置正常
✅ **布局文件正确** - activity_settings.xml 已更新
✅ **服务器代码完整** - usb_display_control.py 支持 WiFi 连接
✅ **修复了 @Override 注解** - WindowsDisplayController 中缺失的注解已添加

### 代码结构
```
app/src/main/java/com/volcano/screen/display/
├── DisplayController.java (接口)
├── DisplayManager.java (管理器)
├── WifiDisplayController.java (WiFi实现)
└── WindowsDisplayController.java (USB实现)

app/src/main/java/com/volcano/screen/
├── settings/SettingsActivity.java (设置界面)
└── ui/MainActivity.java (主界面)
```

## 2. 项目构建

由于当前环境没有配置 Android SDK，需要在安装有 Android Studio 的环境中进行构建。

### 构建步骤

1. **打开项目**
   - 在 Android Studio 中打开项目
   - 等待 Gradle 同步完成

2. **配置 local.properties (如果需要)**
   - 在项目根目录创建 `local.properties` 文件
   - 添加 Android SDK 路径：
   ```
   sdk.dir=C:\\Android\\SDK
   ```

3. **构建 Debug 版本**
   - 在 Android Studio 中点击 Build > Build Bundle(s) / APK(s) > Build APK(s)
   - 或在命令行中运行：
   ```
   gradlew.bat assembleDebug
   ```

4. **构建位置**
   - APK 文件生成位置：`app/build/outputs/apk/debug/app-debug.apk`

## 3. 功能测试

### 3.1 USB 通信测试（原功能）
**测试目的：** 验证原有 USB 通信功能正常
**测试步骤：**
1. 用 USB 线连接手机和电脑
2. 手机开启 USB 调试
3. 启动电脑端服务器：`python server/usb_display_control.py`
4. 在 APP 中点击「测试服务器」按钮
5. 尝试切换显示模式

**预期结果：**
- 状态按钮显示「Ready (USB)」
- 显示模式能够正常切换
- Toast 消息显示「显示器模式已更新 (USB)」

### 3.2 WiFi 通信测试（新功能）
**测试目的：** 验证新增的 WiFi 通信功能
**测试步骤：**
1. 确保手机和电脑在同一局域网
2. 启动电脑端服务器：`python server/usb_display_control.py`
3. 记录服务器控制台显示的「Local IP address」
4. 打开 APP 进入设置界面
5. 在「通信方式」中选择「仅 WiFi」
6. 配置 WiFi 服务器地址为第 3 步记录的 IP
7. 保持端口为 8765
8. 点击「测试连接」按钮
9. 返回主界面测试显示模式切换

**预期结果：**
- 连接测试弹窗显示「USB 连接: ❌ 不可用」
- 连接测试弹窗显示「WiFi 连接: ✅ 可用」
- 连接测试弹窗显示「当前使用: WiFi」
- 主界面状态按钮显示「Ready (WiFi)」
- 显示模式能够正常切换
- Toast 消息显示「显示器模式已更新 (WiFi)」

### 3.3 自动选择测试
**测试目的：** 验证通信方式自动选择功能
**测试步骤：**
1. 同时连接 USB 并确保 WiFi 可用
2. 在 APP 设置中选择「自动选择」
3. 测试显示模式切换

**预期结果：**
- 系统优先使用 USB 连接
- 状态按钮显示「Ready (USB)」

### 3.4 通信方式切换测试
**测试目的：** 验证通信方式平滑切换
**测试步骤：**
1. 先用一种方式连接并测试功能
2. 在设置中切换到另一种方式
3. 验证新方式是否正常工作

**预期结果：**
- 切换后自动重新连接
- 功能正常工作，业务逻辑无感知

### 3.5 连接失败处理测试
**测试目的：** 验证异常情况的处理
**测试步骤：**
1. 不启动服务器，点击「测试服务器」
2. 配置错误的 WiFi 地址，测试连接

**预期结果：**
- 状态按钮显示「Not Ready」
- 调试信息显示连接失败原因

## 4. 上机演示流程

### 演示前准备
1. **设备准备**
   - 一台 Android 手机（已安装 APP）
   - 一台 Windows 电脑（双显示器）
   - USB 数据线
   - 确保手机和电脑在同一 WiFi 网络

2. **服务器准备**
   - 确保电脑已安装 Python 3
   - 准备服务器脚本：`server/usb_display_control.py`

### 演示步骤
**场景 1：USB 连接演示**
1. 用 USB 连接手机和电脑
2. 启动服务器：`python server/usb_display_control.py`
3. 展示：手机 APP 主界面状态显示「Ready (USB)」
4. 演示：切换显示器开关，显示模式正常切换

**场景 2：WiFi 连接演示**
1. 在设置界面选择「仅 WiFi」
2. 配置正确的服务器 IP 地址
3. 点击「测试连接」展示连接测试结果
4. 返回主界面
5. 展示：状态按钮显示「Ready (WiFi)」
6. 演示：切换显示器开关，显示模式正常切换

**场景 3：自动选择演示**
1. 同时保持 USB 连接和 WiFi 可用
2. 在设置中选择「自动选择」
3. 展示：系统自动选择 USB 连接

## 5. 注意事项

### 5.1 网络相关
- **防火墙设置**：使用 WiFi 连接时，需确保 Windows 防火墙允许 8765 端口的入站连接
- **同一网段**：手机和电脑需要在同一局域网段
- **IP 地址**：电脑 IP 可能变化，需要及时更新手机配置

### 5.2 USB 相关
- **USB 调试**：手机需要开启 USB 调试
- **ADB 驱动**：电脑需要安装手机的 ADB 驱动
- **授权提示**：首次连接手机需要授权 USB 调试

### 5.3 Android 相关
- **系统版本**：APP 支持 Android 5.0 (API 21) 及以上
- **屏幕方向**：APP 锁定为竖屏

## 6. 常见问题排查

### Q1: 构建时提示 SDK location not found
**解决方法**：在项目根目录创建 `local.properties` 文件，配置正确的 SDK 路径

### Q2: USB 连接失败
**排查步骤**：
1. 检查 USB 线是否正常
2. 检查手机是否开启 USB 调试
3. 检查电脑是否安装 ADB 驱动
4. 重新插拔 USB 线

### Q3: WiFi 连接失败
**排查步骤**：
1. 检查手机和电脑是否在同一网络
2. 检查电脑 IP 地址配置是否正确
3. 检查防火墙是否阻止了连接
4. 确认服务器已启动并监听 0.0.0.0:8765

### Q4: 状态按钮一直显示 Not Ready
**排查步骤**：
1. 检查服务器是否已启动
2. 检查通信方式配置是否正确
3. 查看调试信息了解具体错误原因

## 7. 交付物清单

1. **源代码**：完整的 Android 项目代码（Git 仓库）
2. **测试文档**：WIFI_COMMUNICATION_TEST.md
3. **计划文档**：本 CHECK_BUILD_TEST_PLAN.md
4. **APK 安装包**（构建后）：app-debug.apk
