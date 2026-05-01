# Display Control - 测试套件

本目录包含所有测试相关的文件和脚本，按功能分为 display 和 network 两类。

## 目录结构

```
test/
├── display/                          # 显示器相关测试
│   ├── test_display_control.py       # 完整的显示器控制自动化测试套件
│   └── test_displays.py              # 显示器信息检测脚本
├── network/                          # 网络相关测试
│   ├── test_adb.py                   # ADB 连接和设备检测测试
│   ├── test_usb_speed.py             # USB 网络速度测试
│   └── README.md                     # 网络测试说明
├── README.md                         # 本文档
└── TEST_SPEC.md                      # 产品测试规范文档
```

## 运行测试

### 显示器控制测试

```bash
cd test/display
python test_display_control.py
```

### 显示器信息检测

```bash
cd test/display
python test_displays.py
```

### ADB 连接测试

```bash
cd test/network
python test_adb.py
```

### USB 网络速度测试

前置条件：先启动服务器
```bash
cd server
python usb_display_control.py
```

然后运行测试：
```bash
cd test/network
python test_usb_speed.py
```

## 测试覆盖

### 显示器测试 (display/)

1. **服务器基础功能** — 端口监听、HTTP 请求处理、响应格式验证
2. **显示器状态检测** — 实时检测、模式值范围、PowerShell 脚本执行
3. **显示器切换控制** — 切换到仅第一屏/第二屏/扩展模式
4. **Android 端通信** — ADB 设备连接、ADB reverse、应用安装
5. **错误处理** — 无效命令、非法 HTTP 方法、超时处理
6. **集成测试** — 完整工作流程

### 网络测试 (network/)

1. **ADB 连接** — ADB 版本检测、设备连接、reverse 端口转发
2. **USB 速度测试** — Ping 延迟、下载速度、上传速度

## 注意事项

1. **运行环境** — Windows 10/11, Python 3.8+, ADB 已安装
2. **测试前准备** — 确保 USB 调试已启用，显示器驱动正常
3. **通信方式** — 支持 USB (ADB reverse) 和 WiFi 两种通信方式
4. **服务器端口** — 统一使用 8765 端口

---

**最后更新**: 2026-05-01
