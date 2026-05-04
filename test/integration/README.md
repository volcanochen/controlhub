# Integration Tests

集成测试用于验证 ControlHub Camera 的完整功能。

## 前提条件

1. **硬件**
   - Windows PC
   - Android 设备（通过 USB 连接）
   - 至少一台显示器

2. **软件**
   - Python 3.8+
   - Android SDK (ADB)
   - 已配置 ADB 环境变量

## 测试文件

| 文件 | 说明 |
|------|------|
| `test_integration.py` | 基础集成测试（服务器、API、连接） |
| `test_ui_automation.py` | UI 自动化测试（模拟用户操作） |
| `run_tests.py` | 测试运行脚本 |

## 运行测试

### 运行所有测试
```bash
cd test/integration
python run_tests.py
```

### 运行特定测试
```bash
# 仅运行基础集成测试
python run_tests.py --server

# 仅运行 UI 自动化测试
python run_tests.py --ui
```

### 单独运行测试文件
```bash
# 基础集成测试
python test_integration.py

# UI 自动化测试
python test_ui_automation.py
```

## 发布流程集成

集成测试已集成到发布流程中。运行发布脚本时会自动执行测试：

```bash
# 发布脚本会自动运行集成测试
python release/publish.py
```

发布流程：
1. 清理 release 目录
2. 构建 APK
3. **运行集成测试**（测试失败则中止发布）
4. 复制文件到 release 目录

## 测试内容

### 基础集成测试 (`test_integration.py`)

1. **Setup** - 检查 ADB、设备连接、APK 构建
2. **Start Server** - 启动 PC 服务器
3. **Install App** - 安装 Android 应用
4. **Launch App** - 启动应用
5. **Server Status API** - 测试服务器状态 API
6. **Brightness Control** - 测试亮度控制
7. **App-Server Connection** - 测试应用与服务器连接
8. **UI Navigation** - 测试 UI 导航
9. **Camera Functionality** - 测试摄像头功能

### UI 自动化测试 (`test_ui_automation.py`)

1. **Setup** - 唤醒设备、解锁屏幕
2. **Launch App** - 启动应用
3. **Main Screen** - 验证主屏幕元素
4. **Settings Navigation** - 测试设置导航
5. **Channel Selection** - 测试通道选择（USB/WiFi/Auto）
6. **Brightness Toggle** - 测试亮度开关
7. **Server Status** - 测试服务器状态显示

## 测试输出

测试结果会以彩色输出显示：
- 🟢 `[PASS]` - 测试通过
- 🔴 `[FAIL]` - 测试失败
- 🟡 `[WARN]` - 警告
- 🔵 `[INFO]` - 信息

## 故障排除

### ADB 连接问题
```bash
# 检查设备连接
adb devices

# 重启 ADB 服务
adb kill-server
adb start-server
```

### 端口占用
```bash
# 检查端口占用
netstat -ano | findstr :8765

# 结束占用进程
python ../../server/cleanup.py
```

### 应用安装失败
```bash
# 卸载旧版本
adb uninstall com.volcano.controlhub

# 重新安装
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

## 持续集成

可以将这些测试集成到 CI/CD 流程中：

```yaml
# GitHub Actions 示例
- name: Run Integration Tests
  run: |
    cd test/integration
    python run_tests.py
```

## 注意事项

1. 测试前确保设备已解锁
2. 首次运行可能需要授权 USB 调试
3. 某些 UI 测试可能因屏幕分辨率不同而失败
4. 建议在测试前重启 ADB 服务
5. 发布前测试失败会中止发布流程
