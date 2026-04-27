# USB 显示器控制功能使用说明

## 功能概述

通过 **USB 连接** 控制 Windows 电脑的显示器显示模式，无需 WiFi 网络。

## 架构原理

```
Android 手机
    ↓ (USB 连接)
ADB Reverse 通道
    ↓ (localhost:8765)
Windows 电脑 (usb_display_control.py)
    ↓ (执行命令)
DisplaySwitch.exe
    ↓
切换显示器
```

## 使用步骤

### 1️⃣ 准备工作

**在 Windows 电脑上：**

1. 安装 ADB 工具
   - 下载：https://developer.android.com/studio/releases/platform-tools
   - 解压到任意目录（如 `C:\platform-tools`）
   - 添加到系统 PATH 环境变量，或直接在目录中运行

2. 安装 Python 3（如果未安装）
   - 下载：https://www.python.org/downloads/

### 2️⃣ 连接手机

1. 用 USB 线连接手机到电脑
2. 在手机上开启 **USB 调试模式**：
   - 进入设置 → 关于手机
   - 连续点击"版本号"7 次，开启开发者选项
   - 返回设置 → 系统 → 开发者选项
   - 开启"USB 调试"
3. 手机上会弹出"允许 USB 调试"的提示，点击"允许"

### 3️⃣ 启动 Windows 服务端

```bash
# 打开命令提示符或 PowerShell
cd c:\VOLCANO\myws\andr

# 运行服务端脚本
python usb_display_control.py
```

你会看到类似输出：
```
============================================================
USB 显示器控制服务端
============================================================

📋 使用说明：
1. 手机通过 USB 连接电脑
2. 手机开启 USB 调试模式
3. 在 Android 应用中切换显示器模式

============================================================

📡 设置 ADB reverse 端口转发...
✅ ADB 已就绪
⏳ 等待设备连接...
✅ 设备已连接
🔄 设置端口转发：tcp:8765 -> tcp:8765
✅ 端口转发设置成功

============================================================
服务启动中...
============================================================

✅ 服务器已启动在端口 8765
📡 监听请求...
```

### 4️⃣ 在 Android 应用中控制

1. 打开 "控制屏" 应用
2. 找到 "Windows 显示器控制" 部分
3. 切换 Switch 按钮：
   - **仅第一屏**：开启 = 笔记本内置屏幕，关闭 = 不启用
   - **仅第二屏**：开启 = 仅外接显示器，关闭 = 不启用
   - 两个都开启 = 扩展模式（双屏同时使用）

### 5️⃣ 观察效果

Windows 电脑的显示器应该会立即切换显示模式！

## Switch 控制逻辑

| 仅第一屏 | 仅第二屏 | 显示模式 |
|---------|---------|----------|
| ✅ ON   | ❌ OFF  | 仅笔记本内置屏幕 |
| ❌ OFF  | ✅ ON   | 仅外接显示器 |
| ✅ ON   | ✅ ON   | 扩展模式（双屏） |
| ❌ OFF  | ❌ OFF  | 不允许（会自动开启第一个） |

## 故障排查

### ❌ "ADB 未安装或不在 PATH 中"

**解决方法：**
1. 下载 ADB 工具：https://developer.android.com/studio/releases/platform-tools
2. 解压后，将 `platform-tools` 目录添加到 PATH 环境变量
3. 或者直接在 `platform-tools` 目录中运行命令

### ❌ "没有检测到设备"

**检查清单：**
- [ ] 手机是否通过 USB 连接电脑
- [ ] 手机是否开启 USB 调试模式
- [ ] 手机上是否点击了"允许 USB 调试"
- [ ] 尝试重新插拔 USB 线
- [ ] 尝试更换 USB 端口

**验证连接：**
```bash
adb devices
```

应该能看到你的设备列表。

### ❌ "设置 ADB reverse 失败"

**可能原因：**
- 手机系统版本太低（需要 Android 5.0+）
- 某些 ROM 不支持 ADB reverse

**解决方法：**
尝试使用 WiFi 网络方案（windows_display_server.py）

### ❌ "命令执行失败"

**检查：**
- 确保是 Windows 系统（DisplaySwitch.exe 是 Windows 专用）
- 确保电脑连接了多个显示器

## 技术细节

### ADB Reverse 原理

`adb reverse` 命令将手机上的端口反向代理到电脑：

```bash
adb reverse tcp:8765 tcp:8765
```

这样，手机访问 `localhost:8765` 时，实际连接到的是电脑的 8765 端口。

### 服务端 API

**POST /**
切换显示器

请求体：
```json
{
  "command": "extend"
}
```

可用命令：
- `internal` - 仅第一屏
- `external` - 仅第二屏
- `extend` - 扩展模式
- `clone` - 复制模式

**GET /**
健康检查

## 安全提示

⚠️ **注意：**
- 这个服务只在 USB 连接时工作
- 不需要网络权限
- 不会暴露到外部网络
- 非常安全！

## 停止服务

在服务端脚本中按 `Ctrl+C` 即可停止服务。

## 开机自启动（可选）

如果需要每次开机自动启动服务端：

1. 创建一个批处理文件 `start_display_server.bat`：
```batch
@echo off
cd /d c:\VOLCANO\myws\andr
python usb_display_control.py
```

2. 将此批处理文件放入启动文件夹：
   - 按 `Win+R`
   - 输入：`shell:startup`
   - 将批处理文件复制到此文件夹

## 高级配置

### 修改端口

如果需要修改监听端口，编辑两个文件：

1. `usb_display_control.py`：
```python
PORT = 8765  # 改成你想要的端口
```

2. `WindowsDisplayController.java`：
```java
private static final String SERVER_URL = "http://localhost:8765";
```

然后重新编译 Android 应用。

---

**文档版本**: v1.1.0  
**最后更新**: 2026-04-27  
**维护者**: Volcano Chen
