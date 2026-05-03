# 控制屏 - Desktop Control Hub v1.4.0
让你的旧手机成为桌面工作娱乐空间的便捷控制台。

## 快速开始

### 1. 安装 Android 应用

将 `app-debug.apk` 传到手机上并安装：
- USB 连接手机，运行 `adb install app-debug.apk`
- 或直接在手机文件管理器中打开 APK 文件安装

### 2. 启动 PC 服务器

**方式 A：双击启动（推荐）**
```
双击 scripts\start.bat
```

**方式 B：命令行启动**
```bash
python server/usb_display_control.py
```

**前提条件：**
- Python 3.8+ 已安装
- 手机通过 USB 连接电脑，开启 USB 调试模式

### 3. 使用

1. 打开手机上的「控制屏」应用
2. 状态显示 **Ready (USB)** 即表示连接成功
3. 勾选/取消显示器开关即可切换屏幕模式

## 功能说明

- 显示器控制：4 种模式切换（仅第一屏/仅第二屏/扩展/复制）
- 图片投放：PC 端向手机投放图片，支持手势控制
- 系统托盘：Windows 右下角托盘图标控制
- 亮度控制：PC 端亮度调节
- WiFi 连接：支持局域网无线连接（可选）

## 目录结构

```
release/
├── app-debug.apk              # Android 应用安装包
├── server/
│   ├── usb_display_control.py # 主服务器程序
│   ├── windows_display_server.py # 备用服务器 (Flask)
│   └── tray_service.py        # 系统托盘服务
├── display/
│   ├── brightness_control.ps1 # 亮度控制脚本
│   └── get_displays.ps1       # 显示器检测脚本
├── scripts/
│   └── start.bat               # Windows 一键启动脚本
├── README.md                   # 本文档
└── docs/
    └── DESIGN.md                # 设计文档
```

## 图片投放使用方法

1. 运行系统托盘服务：
```bash
python server/tray_service.py
```

2. 在托盘图标右键选择 **Cast Image...** 选择图片
3. 手机端自动弹出图片显示界面
4. 支持手势操作：双指缩放、单指移动、双击切换尺寸

## WiFi 连接（可选）

如果不想用 USB 线：

1. 启动服务器后查看控制台输出的 IP 地址
2. 打开手机应用 -> 设置 -> 选择「仅 WiFi」或「自动选择」
3. 输入 IP 地址和端口 8765
4. 点击测试连接

## 故障解决

| 问题 | 解决方案 |
|------|---------|
| 手机显示 Not Ready | 检查 USB 连接、确认服务器正在运行 |
| 切换显示器失败 | 以管理员身份运行服务器、更新显卡驱动 |
| 托盘服务报错 | 需要安装依赖：`pip install pystray Pillow` |
| 亮度控制不生效 | 可能需要管理员权限或特定显卡驱动 |

## 依赖安装（可选）

如需使用系统托盘功能：
```bash
pip install pystray Pillow
```

## 版本信息

- 版本号：v1.4.0
- 发布日期：2026-05-03
- 开发者：Volcano Chen
