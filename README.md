# 控制屏 - Desktop Control Hub

让你的旧手机成为桌面工作娱乐空间的便捷控制台，实现远程控制电脑显示器、投放图片、摄像头视频流、扫码等功能。

## 功能特性

### 🖥️ 显示器控制

- ✅ **实时状态检测** - 自动获取当前显示器配置状态
- ✅ **一键切换** - 支持 4 种显示模式切换（仅第一屏/仅第二屏/扩展/复制）
- ✅ **防止误操作** - 智能保护，防止双屏同时关闭

### 📱 图片投放

- ✅ **图片投放** - PC 端向手机端投放图片并全屏显示
- ✅ **手势控制** - 双指缩放、单指移动、双击切换尺寸
- ✅ **自动弹窗** - 投放图片时手机自动弹出显示界面
- ✅ **远程关闭** - 支持远程关闭手机端图片显示窗口
- ✅ **外部查看器** - 一键用系统默认图片浏览器查看

### 📷 摄像头功能（新增）

- ✅ **MJPEG 视频流** - 手机摄像头实时视频流传输到 PC
- ✅ **前后摄像头切换** - 支持动态切换前后摄像头
- ✅ **图像自动旋转** - 根据设备方向自动调整画面
- ✅ **PC 端预览** - 实时预览窗口，保持原始比例
- ✅ **OBS 集成** - 支持 OBS Virtual Camera，可用于 Teams/Zoom 会议

### 🔍 扫码功能（新增）

- ✅ **二维码扫描** - 支持 QR Code、EAN、UPC、Code128 等主流条码
- ✅ **托盘扫码** - PC 端托盘一键扫码，结果自动复制到剪贴板
- ✅ **远程控制** - PC 端可远程打开/关闭手机摄像头界面
- ✅ **扫码结果通知** - 扫码成功后显示通知

### 🛠️ 系统工具

- ✅ **系统托盘服务** - Windows 通知栏控制，支持投放、清除、扫码操作
- ✅ **亮度控制** - PC 端亮度调节，手机端光照传感器联动
- ✅ **网速测试** - USB/WiFi 连接速度测试
- ✅ **日志查看** - 实时查看系统日志

### 🎨 用户体验

- ✅ **USB 连接** - 通过 ADB reverse 建立稳定通信
- ✅ **WiFi 连接** - 通过局域网无线连接，支持自动选择通信方式
- ✅ **紧凑界面** - 一行式控制布局，简洁直观
- ✅ **黑色主题** - OLED 友好，省电防烧屏
- ✅ **设置功能** - 可启用/禁用各项功能，配置 WiFi 服务器地址

## 系统架构

```
┌─────────────────────┐      USB/ADB       ┌─────────────────────┐
│     Android App     │ ←─────────────────→ │     PC Server       │
│  ┌───────────────┐  │    tcp:8765        │  ┌───────────────┐   │
│  │ 显示控制界面   │  │                    │  │ 显示器控制     │   │
│  ├───────────────┤  │                    │  ├───────────────┤   │
│  │ 图片投放界面   │  │                    │  │ 图片投放服务   │   │
│  ├───────────────┤  │                    │  ├───────────────┤   │
│  │ 摄像头界面     │  │ ←── WiFi ─────────→ │  │ 摄像头客户端   │   │
│  │ (端口 8766)    │  │    tcp:8766        │  │ 系统托盘服务   │   │
│  └───────────────┘  │                    │  └───────────────┘   │
└─────────────────────┘                    └─────────────────────┘
                                                      │
                                               ┌──────▼──────┐
                                               │  Windows    │
                                               │   Display   │
                                               └─────────────┘
```

## 界面预览

![主界面](app_screenshot.png)

**界面说明**：

- **📷 摄像头按钮** - 右上角打开摄像头界面
- **🖼️ 图片按钮** - 图片投放功能
- **⚙️ 设置按钮** - 右上角配置入口
- **Ready/Not Ready** - 服务器连接状态（可点击手动检查）
- **第一屏 ☑** - 笔记本内置显示器开关
- **第二屏 ☑** - 外接显示器开关

## 构建方法

### 前置要求

- Android SDK（含 Build Tools 33.0.0）
- JDK 17（推荐使用 Android Studio 自带的 JBR）
- Python 3.8+（PC 服务器端）

### 构建 APK

**Windows（PowerShell）**：

```powershell
# 设置 JAVA_HOME（使用 Android Studio 自带的 JBR）
$env:JAVA_HOME = "C:\Program Files\Android\Android Studio\jbr"

# 构建 Debug APK
.\gradlew.bat assembleDebug

# 构建 Release APK
.\gradlew.bat assembleRelease
```

构建产物位于：
- Debug: `app\build\outputs\apk\debug\app-debug.apk`
- Release: `app\build\outputs\apk\release\app-release.apk`

**Linux/macOS**：

```bash
export JAVA_HOME=/path/to/jdk
./gradlew assembleDebug
```

### 安装 APK 到设备

```bash
adb install app/build/outputs/apk/debug/app-debug.apk
```

### 运行测试

```bash
# 运行完整测试套件并生成报告
python test/run_detailed_tests.py

# 运行集成测试
python test/integration/run_tests.py --all
```

### 一键发布

```bash
python release/publish.py
```

## 安装说明

### 1. PC 端（Windows）

**前置要求**：

- Python 3.8+
- Android SDK Platform Tools (ADB)
- Windows 系统（支持多显示器）

**安装步骤**：

```bash
# 1. 进入服务器目录
cd server

# 2. 安装依赖
pip install opencv-python requests pystray Pillow

# 3. 启动服务器
python tray/tray_service.py
```

**服务器功能**：

- 自动检测 ADB 设备
- 建立 ADB reverse 端口转发
- USB 断开后自动重连
- 监听端口 8765（主服务）、8766（摄像头）
- 执行显示器切换命令
- 图片投放服务
- 摄像头视频流接收
- 扫码控制
- 亮度控制
- 网速测试
- HTTP API 接口

### 2. Android 端

**安装 APK**：

```bash
# 通过 ADB 安装
adb install app/build/outputs/apk/debug/app-debug.apk
```

**或者手动安装**：

1. 将 APK 文件复制到手机
2. 在手机上点击安装

**权限要求**：

- 摄像头权限（扫码和视频流）
- 网络权限
- 不需要 ROOT

## 使用方法

### 快速开始

#### USB 连接方式（推荐）

1. **连接设备**
   - 使用 USB 线连接手机和电脑
   - 手机开启 USB 调试模式
2. **设置端口转发**
   ```bash
   adb reverse tcp:8765 tcp:8765
   adb reverse tcp:8766 tcp:8766
   ```
3. **启动 PC 服务器**
   ```bash
   cd server
   python tray/tray_service.py
   ```
4. **打开 Android 应用**
   - 启动 "控制屏" 应用
   - 查看状态按钮（应显示 "Ready (USB)"）

#### WiFi 连接方式

1. **准备工作**
   - 确保手机和电脑在同一局域网
   - 启动 PC 服务器，记录控制台显示的 IP 地址
2. **配置手机端**
   - 打开应用设置
   - 在「通信方式」中选择「仅 WiFi」或「自动选择」
   - 输入 WiFi 服务器地址
3. **测试连接**
   - 点击「测试连接」验证设置

### 摄像头功能

#### 手机端操作

1. **打开摄像头界面**
   - 主界面右上角点击 📷 按钮
   - 或通过 PC 端托盘 "Open Camera"

2. **摄像头预览**
   - 实时显示摄像头画面
   - 显示服务器地址和端口

3. **扫码功能**
   - 点击 "Scan QR" 按钮开始扫码
   - 扫码成功后显示结果
   - 点击结果面板可复制到剪贴板

4. **切换摄像头**
   - 点击 "Switch Camera" 切换前后摄像头

#### PC 端操作

**系统托盘菜单**：

```
┌─────────────────────────────┐
│ Server: Running/Stopped     │
├─────────────────────────────┤
│ Start Server                │
│ Stop Server                 │
├─────────────────────────────┤
│ Cast Image...               │
│ Clear Image                 │
├─────────────────────────────┤
│ Open Camera                 │  ← 打开手机摄像头界面
│ Close Camera                │  ← 关闭手机摄像头界面
│ Scan QR Code                │  ← 扫码并复制到剪贴板
│ Camera: 192.168.50.132:8766 │
├─────────────────────────────┤
│ Exit                        │
└─────────────────────────────┘
```

**命令行预览**：

```bash
# 启动预览窗口
python server/camera/camera_client.py --host 192.168.50.132 --preview

# 测试流连接
python server/camera/test_stream.py
```

#### OBS 集成（用于 Teams/Zoom）

1. 安装 [OBS Studio](https://obsproject.com/)
2. 添加"媒体源"，URL 填入：
   ```
   http://192.168.50.132:8766/camera/stream
   ```
3. 点击 OBS 的"启动虚拟摄像机"
4. 在 Teams/Zoom 中选择 "OBS Virtual Camera"

### 显示器控制

**切换显示器模式**：

- ✅ 第一屏 + ✅ 第二屏 = **扩展模式**
- ✅ 第一屏 + ☐ 第二屏 = **仅第一屏**
- ☐ 第一屏 + ✅ 第二屏 = **仅第二屏**
- ☐ 第一屏 + ☐ 第二屏 = **自动切换回仅第一屏**（防止全关）

### 图片投放功能

1. 在 PC 端系统托盘右键点击 "Cast Image..."
2. 选择要投放的图片文件
3. 手机端会自动弹出图片显示界面
4. 支持手势操作：双指缩放、单指移动、双击切换尺寸

## 技术细节

### 摄像头 API

```
GET /camera/stream       - MJPEG 视频流
GET /camera/snapshot     - 单帧截图
GET /camera/status       - 状态信息
POST /camera/open        - 打开摄像头界面
POST /camera/close       - 关闭摄像头界面
POST /camera/switch      - 切换摄像头
POST /barcode/start      - 开始扫码
POST /barcode/stop       - 停止扫码
GET /barcode/result      - 获取扫码结果
```

### 图片投放 API

```
GET /image/status        - 获取图片状态
GET /image/data          - 图片二进制数据
POST /image/cast         - 投放指定路径图片
POST /image/clear        - 清除图片
POST /image/zoom-in      - 放大
POST /image/zoom-out     - 缩小
```

### 显示器控制 API

```
GET /status              - 获取显示器状态
POST /                   - 切换显示模式
POST /brightness         - 亮度控制
```

## 项目结构

```
c:\VOLCANO\myws\controlhub_camera\
├── README.md                   # 本文档
├── build.gradle                # Gradle 构建配置
├── settings.gradle             # Gradle 设置
├── gradlew.bat                 # Gradle Wrapper (Windows)
│
├── app/                        # Android 应用
│   ├── build.gradle            # App 构建配置
│   └── src/main/
│       ├── java/com/volcano/controlhub/
│       │   ├── ui/                            # 界面层
│       │   │   ├── MainActivity.java          # 主界面
│       │   │   ├── SettingsActivity.java      # 设置界面
│       │   │   └── ...
│       │   ├── camera/                        # 摄像头模块（新增）
│       │   │   ├── CameraService.java         # 摄像头服务
│       │   │   ├── CameraController.java      # CameraX 控制器
│       │   │   ├── CameraActivity.java        # 摄像头界面
│       │   │   └── MJPEGStreamServer.java     # MJPEG 流服务器
│       │   ├── display/                       # 显示器控制
│       │   ├── imagecast/                     # 图片投放
│       │   └── network/                       # 网络层
│       ├── res/
│       │   └── layout/
│       │       ├── activity_main.xml          # 主界面布局
│       │       ├── activity_camera.xml        # 摄像头界面布局（新增）
│       │       └── ...
│       └── AndroidManifest.xml
│
├── server/                     # PC 服务器
│   ├── core/                   # 核心服务
│   │   └── usb_display_control.py
│   ├── camera/                 # 摄像头客户端（新增）
│   │   ├── camera_client.py    # 摄像头客户端
│   │   ├── test_stream.py      # 流测试脚本
│   │   └── config.json         # 摄像头配置
│   ├── tray/                   # 系统托盘服务
│   │   └── tray_service.py     # 含扫码功能
│   ├── display/                # 显示器相关
│   ├── imagecast/              # 图片投放工具
│   └── tools/                  # 工具脚本
│
├── docs/                       # 文档
│   └── CAMERA_MODULE_SPEC.md   # 摄像头模块说明书（新增）
│
└── test/                       # 测试套件
```

## 版本历史

### v1.5.0 (2026-05-05)

**新增功能与改进**：

- ✅ **集成测试** - 自动化测试框架，验证完整系统功能
- ✅ **发布流程集成测试** - 发布前自动运行测试，确保质量
- ✅ **UI 自动化测试** - 模拟用户操作验证功能
- ✅ **Tkinter 预览窗口** - 完全重写预览窗口，使用 Tkinter 替代 OpenCV，界面更美观，响应更流畅
- ✅ **彩色控制按钮** - 预览窗口按钮支持彩色显示，提升可用性
- ✅ **窗口大小自适应** - 预览窗口自动调整大小（屏幕的 90%），支持手动调整窗口大小
- ✅ **实时摄像头切换** - 切换摄像头立即生效，无需等待
- ✅ **图像比例保持** - 窗口调整时自动保持图像原始比例
- ✅ **黑色主题** - 预览窗口使用黑色主题，更符合视频查看需求
- ✅ **预览窗口旋转** - 按 r/e 键旋转画面，解决旋转不正确问题
- ✅ **摄像头模块优化** - MJPEG 视频流、二维码扫描、托盘扫码集成完善
- ✅ **网络稳定性改进** - USB/WiFi 双通道支持，自动重连机制优化
- ✅ **ADB 设备管理** - 自动检测设备状态，离线设备自动恢复
- ✅ **预览窗口改进** - 按 r/e 键旋转画面，支持重置、切换等操作

### v1.4.0 (2026-05-03)

**新增功能**：

- ✅ **图片投放** - PC 端向手机端投放图片并显示
- ✅ **手势控制** - 双指缩放、单指移动、双击切换尺寸
- ✅ **系统托盘服务** - Windows 通知栏控制
- ✅ **USB 自动重连** - USB 断开后自动检测并重建 ADB reverse
- ✅ **网速测试** - USB/WiFi 连接速度测试

### v1.3.0 (2026-05-02)

- ✅ 亮度控制功能
- ✅ 光照传感器支持

### v1.2.0 (2026-04-30)

- ✅ 亮度控制滑块
- ✅ 主机亮度联动开关

### v1.1.0 (2026-04-27)

- ✅ 实时显示器状态检测
- ✅ 4 种显示模式切换
- ✅ ADB reverse 通信
- ✅ 黑色主题

**应用信息**：

- 应用名称：控制屏
- 版本号：v1.5.0
- 开发者：Volcano Chen
- GitHub：<https://github.com/volcanochen/controlhub>
- 🤖 AI 开发

## 相关文档

- [摄像头模块说明书](docs/CAMERA_MODULE_SPEC.md) - 摄像头功能详细说明
- [服务器文档](server/README.md) - PC 服务器详细说明
- [集成测试说明](test/integration/README.md) - 集成测试使用指南

## 集成测试

项目包含完整的集成测试，在发布前自动运行。

### 运行测试

```bash
# 运行所有集成测试
python test/integration/run_tests.py --all

# 仅运行基础集成测试
python test/integration/run_tests.py --server

# 仅运行 UI 自动化测试
python test/integration/run_tests.py --ui
```

### 测试内容

| 测试类型 | 说明 |
|----------|------|
| 基础集成测试 | 服务器启动、APK 安装、API 功能、连接验证 |
| UI 自动化测试 | 模拟用户操作，验证界面导航和功能 |

## 发布流程

使用发布脚本自动构建、测试和打包：

```bash
# 运行发布脚本（包含集成测试）
python release/publish.py
```

发布流程：
1. 清理 release 目录
2. 构建 APK
3. **运行集成测试**（测试失败则中止发布）
4. 复制文件到 release 目录

## 贡献

欢迎提交问题和改进建议！

## 许可证

本项目仅供学习和个人使用。

## 开发者

- **开发者**: Volcano Chen
- **GitHub**: <https://github.com/volcanochen/controlhub>
- **🤖 AI 开发**: 本应用由 AI 助手辅助开发

***

**最后更新**: 2026-05-04\
**维护者**: Volcano Chen\
**版本**: v1.5.0
