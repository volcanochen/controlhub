# Display Control - 产品测试规范

## 1. 概述

本文档定义了 Display Control 系统的测试规范，用于确保产品质量和功能完整性。

### 1.1 测试范围
- Python 服务器端功能
- 显示器状态检测
- 显示器切换控制
- Android 客户端通信（USB 和 WiFi）
- 错误处理和边界条件
- 系统集成

### 1.2 系统架构
```
┌─────────────┐   USB/ADB    ┌─────────────┐
│  Android    │ ←──────────→ │   PC Server │
│    App      │  tcp:8765    │  (Python)   │
│             │              │             │
│  WiFi/LAN   │ ←──────────→ │  0.0.0.0    │
│             │  tcp:8765    │             │
└─────────────┘              └──────┬──────┘
                                    │
                             ┌──────▼──────┐
                             │  Windows    │
                             │   Display   │
                             └─────────────┘
```

## 2. 测试环境要求

### 2.1 硬件要求
- Windows PC（支持多显示器）
- Android 设备
- USB 数据线
- 至少 2 个显示器（用于完整测试）

### 2.2 软件要求
- Python 3.8+
- Android SDK (ADB)
- Android 应用已安装 (com.volcano.screen)
- 显示器驱动正常

### 2.3 前置检查
```bash
adb devices
adb reverse --list
netstat -ano | findstr :8765
```

## 3. 测试用例详细规范

### 3.1 服务器基础功能测试 (TEST-001)

#### TEST-001-01: 服务器进程运行
- **目的**: 验证服务器进程正常运行
- **步骤**: 启动 usb_display_control.py，检查进程列表
- **预期**: python.exe 进程存在

#### TEST-001-02: 服务器端口监听
- **目的**: 验证服务器正确监听端口
- **预期**: 端口 8765 处于 LISTENING 状态

#### TEST-001-03: 健康检查 API
- **目的**: 验证 /status API 正常工作
- **预期**: HTTP 200, JSON 包含 status: "ok"

#### TEST-001-04: 响应格式验证
- **必需字段**: status, mode, mode_name, server, realtime

### 3.2 显示器状态检测测试 (TEST-002)

#### TEST-002-01: 实时检测标记
- **预期**: realtime = true

#### TEST-002-02: 模式值范围
- **有效值**: 0 (unknown), 1 (primary only), 2 (secondary only), 3 (extended), 4 (duplicate)

#### TEST-002-03: PowerShell 检测脚本
- **预期**: 执行时间 < 10 秒，返回有效模式值
- **脚本位置**: server/get_displays.ps1

### 3.3 显示器切换控制测试 (TEST-003)

#### TEST-003-01: 切换到仅第一屏
- **步骤**: POST / {"command": "internal"}, 等待 8 秒, 查询状态
- **预期**: mode = 1

#### TEST-003-02: 切换到仅第二屏
- **步骤**: POST / {"command": "external"}, 等待 8 秒, 查询状态
- **预期**: mode = 2

#### TEST-003-03: 切换到扩展模式
- **步骤**: POST / {"command": "extend"}, 等待 8 秒, 查询状态
- **预期**: mode = 3

### 3.4 通信方式测试 (TEST-004)

#### TEST-004-01: USB 通信 (ADB reverse)
- **步骤**: adb reverse tcp:8765 tcp:8765, 从手机访问 localhost:8765
- **预期**: 连接成功

#### TEST-004-02: WiFi 通信
- **步骤**: 手机访问 http://<PC_IP>:8765
- **预期**: 连接成功

#### TEST-004-03: 通信方式自动选择
- **步骤**: 在设置中选择"自动选择"
- **预期**: 优先 USB，USB 不可用时尝试 WiFi

#### TEST-004-04: Android 应用安装
- **步骤**: adb shell pm list packages com.volcano.screen
- **预期**: 包名存在

### 3.5 错误处理测试 (TEST-005)

#### TEST-005-01: 无效命令处理
- **步骤**: POST / {"command": "invalid"}
- **预期**: success = false

#### TEST-005-02: 服务器不可达
- **步骤**: 不启动服务器，从手机请求
- **预期**: 连接超时，状态显示 "Not Ready"

#### TEST-005-03: WiFi 地址错误
- **步骤**: 配置错误的 WiFi 地址
- **预期**: 连接测试显示 WiFi 不可用

### 3.6 集成测试 (TEST-006)

#### TEST-006-01: 完整工作流程 (USB)
- **步骤**: 获取状态 → 切换模式 → 验证 → 恢复
- **预期**: 所有步骤成功

#### TEST-006-02: 完整工作流程 (WiFi)
- **步骤**: 同上，使用 WiFi 连接
- **预期**: 所有步骤成功

#### TEST-006-03: 通信方式切换
- **步骤**: 在设置中切换 USB ↔ WiFi
- **预期**: 切换后功能正常

## 4. 测试执行

### 4.1 自动化测试脚本
```bash
cd test/display
python test_display_control.py
```

### 4.2 网络速度测试
```bash
# 先启动服务器
cd server
python usb_display_control.py

# 运行速度测试
cd test/network
python test_usb_speed.py
```

## 5. 模式映射表

| 模式值 | 模式名称 | 说明 |
|--------|---------|------|
| 0 | unknown | 未知状态 |
| 1 | internal | 仅第一屏 |
| 2 | external | 仅第二屏 |
| 3 | extend | 扩展模式 |
| 4 | clone | 复制模式 |

## 6. API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| / | GET | 健康检查 |
| /status | GET | 获取显示器状态 |
| / | POST | 执行显示器切换 |
| /ping | GET | Ping 测试 |
| /download | GET | 下载速度测试 |
| /upload | POST | 上传速度测试 |

## 7. 相关文件

- `server/usb_display_control.py` - 服务器主程序
- `server/get_displays.ps1` - PowerShell 显示器检测脚本
- `app/src/main/java/com/volcano/screen/ui/MainActivity.java` - Android 主程序
- `app/src/main/java/com/volcano/screen/display/DisplayManager.java` - 通信方式管理器
- `app/src/main/java/com/volcano/screen/display/WindowsDisplayController.java` - USB 通信控制器
- `app/src/main/java/com/volcano/screen/display/WifiDisplayController.java` - WiFi 通信控制器

---

**文档版本**: 2.0
**最后更新**: 2026-05-01
