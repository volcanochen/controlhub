# ControlHub Camera 模块方案说明书

## 1. 项目概述

### 1.1 背景
ControlHub 项目需要扩展摄像头功能，让 PC 端能够调用手机摄像头，实现以下场景：
- Teams/Zoom 视频会议使用手机摄像头
- 扫描二维码/条形码
- 录音录像功能

### 1.2 目标
- 在现有 ControlHub 架构上扩展摄像头模块
- 实现 MJPEG 视频流传输，PC 端可实时查看
- 支持 USB 和 WiFi 双通道传输
- 支持 OBS Virtual Camera 集成，供第三方应用（Teams 等）使用
- 提供扫码、录像等扩展功能

### 1.3 实现状态

| 功能 | 优先级 | 状态 | 说明 |
|------|--------|------|------|
| 前置摄像头预览 | P0 | ✅ 已完成 | CameraX 实现 |
| MJPEG 视频流服务 | P0 | ✅ 已完成 | NanoHTTPD 服务器 |
| USB 通道传输 | P0 | ✅ 已完成 | ADB 端口转发 |
| WiFi 通道传输 | P0 | ✅ 已完成 | 局域网直连 |
| 通道自动切换 | P1 | ✅ 已完成 | USB 优先，自动回退 WiFi |
| 扫码功能 | P1 | ✅ 已完成 | ML Kit 条码扫描 |
| 前后摄像头切换 | P1 | ✅ 已完成 | 支持动态切换，实时生效 |
| PC端托盘扫码 | P1 | ✅ 已完成 | 系统托盘集成 |
| PC端预览窗口 | P1 | ✅ 已完成 | Tkinter 实现，自适应屏幕，彩色按钮 |
| 手机端IP显示 | P2 | ✅ 已完成 | 设置界面显示 |
| 录像功能 | P2 | 📋 计划中 | 本地录制 + 流传输 |
| 音频传输 | P2 | 📋 计划中 | 麦克风音频 |
| OBS 集成 | P2 | 📋 计划中 | 虚拟摄像头 |

---

## 2. 技术架构

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        Android App                               │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    Camera Module                            │ │
│  │                                                             │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │ │
│  │  │  CameraX    │  │   ML Kit    │  │   NanoHTTPD │        │ │
│  │  │  Service    │  │  Scanner    │  │   Server    │        │ │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │ │
│  │         │                │                │                │ │
│  │         ▼                ▼                ▼                │ │
│  │  ┌─────────────────────────────────────────────────────┐  │ │
│  │  │              CameraController                        │  │ │
│  │  │  - 统一管理摄像头生命周期                             │  │ │
│  │  │  - 提供 UseCase 组合                                 │  │ │
│  │  │  - 处理摄像头切换                                    │  │ │
│  │  │  - 图像旋转和色彩处理                                │  │ │
│  │  └─────────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│                              ▼                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                   HTTP Server (Port 8766)                   │ │
│  │                                                             │ │
│  │  端点:                                                      │ │
│  │  GET  /camera/stream     - MJPEG 视频流                     │ │
│  │  GET  /camera/snapshot   - 获取单帧截图                     │ │
│  │  GET  /camera/status     - 摄像头状态                       │ │
│  │  POST /camera/open       - 打开摄像头界面                   │ │
│  │  POST /camera/close      - 关闭摄像头界面                   │ │
│  │  POST /camera/switch     - 切换前后摄像头                   │ │
│  │  POST /barcode/start     - 开始扫码                         │ │
│  │  POST /barcode/stop      - 停止扫码                         │ │
│  │  GET  /barcode/result    - 获取扫码结果                     │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
               USB (ADB)             WiFi (LAN)
                    │                     │
                    ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                         PC Server                                │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                   Tray Service (Control Hub Server)         │ │
│  │                                                             │ │
│  │  - 系统托盘图标                                             │ │
│  │  - 通道选择: USB / WiFi / Auto                              │ │
│  │  - Open Camera - 打开手机摄像头界面 + 预览窗口              │ │
│  │  - Close Camera - 关闭手机摄像头界面 + 预览窗口             │ │
│  │  - Scan QR Code - 扫码并复制到剪贴板                        │ │
│  │  - Cast Image - 图片投放                                    │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                   Camera Client                             │ │
│  │                                                             │ │
│  │  - 连接 Android HTTP Server                                 │ │
│  │  - 接收 MJPEG 流                                            │ │
│  │  - 显示预览窗口（自适应屏幕，无黑边）                        │ │
│  │  - 支持重试机制                                             │ │
│  │  - 推送到 OBS Virtual Camera                                │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 通信通道

#### 2.2.1 USB 通道（推荐）

```
┌──────────────┐                    ┌──────────────┐
│   Android    │                    │      PC      │
│   Port 8766  │◄────── USB ───────►│  ADB Forward │
│              │                    │  localhost   │
│              │                    │   :8766      │
└──────────────┘                    └──────────────┘

ADB 命令: adb forward tcp:8766 tcp:8766
```

**优点**：
- 稳定可靠，不受网络影响
- 延迟低，传输速度快
- 无需同一局域网

**缺点**：
- 需要USB线连接
- 需要开启USB调试

#### 2.2.2 WiFi 通道

```
┌──────────────┐                    ┌──────────────┐
│   Android    │                    │      PC      │
│ 192.168.x.x  │◄───── WiFi ───────►│ 192.168.x.x  │
│   :8766      │                    │              │
└──────────────┘                    └──────────────┘
```

**优点**：
- 无需物理连接
- 可远程使用

**缺点**：
- 需要同一局域网
- 受网络质量影响

#### 2.2.3 自动模式（Auto）

优先使用 USB，USB 不可用时自动切换到 WiFi。

### 2.3 数据流

```
┌──────────────┐     CameraX      ┌──────────────┐     MJPEG      ┌──────────────┐
│   Camera     │ ───────────────→ │  Frame       │ ─────────────→ │  HTTP        │
│   Hardware   │     Preview      │  Buffer      │     Stream     │  Server      │
└──────────────┘                  └──────────────┘                └──────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
                    ▼                   ▼                   ▼
            ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
            │  ML Kit      │    │  JPEG        │    │  Snapshot    │
            │  Scanner     │    │  Encoder     │    │  Service     │
            └──────────────┘    └──────────────┘    └──────────────┘
```

### 2.4 视频编码方案（软件 JPEG）

#### 2.4.1 方案选择

本项目采用 **软件 JPEG 编码** 方案：

| 对比项 | 软件 JPEG | 硬件 MediaCodec | libjpeg-turbo |
|--------|-----------|-----------------|---------------|
| 实现复杂度 | ⭐ 简单 | ⭐⭐⭐ 复杂 | ⭐⭐ 中等 |
| 性能 | 中等 | 高 | 很高 |
| 依赖 | 无额外依赖 | Android API | Native 库 |
| 720p 帧率 | 15-20 fps | 30 fps | 25-30 fps |
| **推荐度** | ⭐⭐⭐ 快速实现 | ⭐⭐⭐⭐ 高性能 | ⭐⭐⭐⭐⭐ 最佳 |

#### 2.4.2 实际性能

| 分辨率 | 帧率 | 延迟 | 帧大小 |
|--------|------|------|--------|
| 1440x1080 | 16-23 fps | 100-200ms | ~120KB |
| 1280x720 | 20-25 fps | 80-150ms | ~80KB |

---

## 3. 模块设计

### 3.1 Android 端模块

#### 3.1.1 目录结构

```
app/src/main/java/com/volcano/controlhub/
├── camera/
│   ├── CameraService.java           # 摄像头服务单例
│   ├── CameraController.java        # CameraX 控制器
│   ├── CameraActivity.java          # 摄像头界面
│   └── MJPEGStreamServer.java       # MJPEG 流服务器
├── ui/
│   ├── MainActivity.java            # 主界面
│   └── SettingsActivity.java        # 设置界面（含IP显示）
└── ...
```

#### 3.1.2 核心类设计

##### CameraService（单例模式）

```java
public class CameraService {
    private static CameraService instance;
    private CameraController cameraController;
    private MJPEGStreamServer streamServer;
    
    public static synchronized CameraService getInstance();
    public void initialize(Context context);
    public void startCamera(LifecycleOwner owner, PreviewView previewView);
    public void stopCamera();
    public void switchCamera();
    public void setBarcodeCallback(BarcodeCallback callback);
    public void setBarcodeScanningEnabled(boolean enabled);
    public boolean isBarcodeScanningEnabled();
}
```

##### MJPEGStreamServer

```java
public class MJPEGStreamServer extends NanoHTTPD {
    public static final int DEFAULT_PORT = 8766;
    
    // 摄像头控制
    public void setCameraController(CameraController controller);
    public void provideFrame(byte[] jpegData);
    
    // API 端点
    // GET  /camera/stream     - MJPEG 视频流
    // GET  /camera/snapshot   - 单帧截图
    // GET  /camera/status     - 状态信息
    // POST /camera/open       - 打开摄像头界面
    // POST /camera/close      - 关闭摄像头界面
    // POST /camera/switch     - 切换摄像头
    // POST /barcode/start     - 开始扫码
    // POST /barcode/stop      - 停止扫码
    // GET  /barcode/result    - 获取扫码结果
}
```

### 3.2 PC 端模块

#### 3.2.1 目录结构

```
server/
├── camera/
│   ├── camera_client.py         # 摄像头客户端
│   ├── test_camera_channel.py   # 通道测试脚本
│   └── config.json              # 摄像头配置（IP/端口/通道）
├── tray/
│   └── tray_service.py          # 系统托盘服务（Control Hub Server）
└── ...
```

#### 3.2.2 核心类设计

##### CameraClient

```python
class CameraClient:
    def __init__(self, host: str, port: int = 8766):
        self.host = host
        self.port = port
        self.stream_url = f"http://{host}:{port}/camera/stream"
    
    def get_stream(self) -> Generator[bytes, None, None]:
        """获取 MJPEG 流（支持重试）"""
        
    def get_snapshot(self) -> bytes:
        """获取单帧截图"""
        
    def switch_camera(self) -> bool:
        """切换摄像头"""
        
    def show_preview(self, window_name: str):
        """显示预览窗口（自适应屏幕，无黑边）"""
```

##### TrayService

```python
class TrayService:
    # 通道管理
    def _check_adb_devices(self) -> bool:
        """检查 USB 设备连接"""
        
    def _setup_adb_forward(self) -> bool:
        """设置 ADB 端口转发"""
        
    def _get_effective_camera_url(self) -> str:
        """获取有效的摄像头 URL"""
    
    # 摄像头控制
    def _open_camera(self):
        """打开手机摄像头界面 + 预览窗口"""
        
    def _close_camera(self):
        """关闭手机摄像头界面 + 预览窗口"""
        
    def _open_preview_window(self, camera_url):
        """打开预览窗口"""
        
    # 扫码功能
    def _start_scan(self):
        """开始扫码流程"""
```

---

## 4. API 设计

### 4.1 HTTP API

#### 4.1.1 获取视频流

```
GET /camera/stream

Response:
Content-Type: multipart/x-mixed-replace; boundary=ControlHubFrame

--ControlHubFrame
Content-Type: image/jpeg
Content-Length: 12345

<JPEG 数据>
--ControlHubFrame
...
```

#### 4.1.2 获取状态

```
GET /camera/status

Response:
{
    "status": "ok",
    "camera": "front",
    "resolution": "1280x720",
    "streaming": false,
    "cameraStarted": false
}
```

#### 4.1.3 打开摄像头界面

```
POST /camera/open

Response:
{
    "status": "ok",
    "message": "Camera activity opened"
}
```

#### 4.1.4 关闭摄像头界面

```
POST /camera/close

Response:
{
    "status": "ok",
    "message": "Camera close request sent"
}
```

#### 4.1.5 切换摄像头

```
POST /camera/switch

Response:
{
    "status": "ok",
    "camera": "back"
}
```

#### 4.1.6 扫码相关

```
POST /barcode/start   # 开始扫码
POST /barcode/stop    # 停止扫码
GET  /barcode/result  # 获取扫码结果
```

---

## 5. 配置文件

### 5.1 摄像头配置 (config.json)

```json
{
  "host": "192.168.50.132",
  "port": 8766,
  "channel": "auto"
}
```

| 字段 | 说明 | 可选值 |
|------|------|--------|
| host | WiFi 模式下的手机 IP | IP 地址 |
| port | 摄像头服务端口 | 默认 8766 |
| channel | 通信通道 | usb / wifi / auto |

---

## 6. 使用指南

### 6.1 手机端操作

1. **查看 IP 信息**
   - 进入设置界面
   - 显示本机 IP 地址和摄像头端口
   - 显示 USB 连接状态
   - 点击 IP 可复制

2. **打开摄像头界面**
   - 主界面右上角点击 📷 按钮
   - 或通过 PC 端托盘 "Open Camera"

3. **摄像头预览**
   - 信息面板在顶部（状态、URL）
   - 按钮面板在底部（切换、扫码、返回）

### 6.2 PC 端操作

#### 系统托盘 (Control Hub Server)

```
┌─────────────────────────────────────┐
│ Server: Running/Stopped             │
├─────────────────────────────────────┤
│ Start Server                        │
│ Stop Server                         │
├─────────────────────────────────────┤
│ Cast Image...                       │
│ Clear Image                         │
├─────────────────────────────────────┤
│ Open Camera                         │  ← 打开摄像头 + 预览窗口
│ Close Camera                        │  ← 关闭摄像头 + 预览窗口
│ Scan QR Code                        │  ← 扫码并复制到剪贴板
│ Camera: 192.168.50.132:8766         │
│ Channel: AUTO (USB Connected)       │
├─────────────────────────────────────┤
│ ✓ USB Channel                       │  ← 仅使用 USB
│ ✓ WiFi Channel                      │  ← 仅使用 WiFi
│ ✓ Auto Channel                      │  ← 自动选择（推荐）
├─────────────────────────────────────┤
│ Exit                                │
└─────────────────────────────────────┘
```

#### 预览窗口

- 自动适应屏幕大小（80% 屏幕尺寸）
- 根据视频帧比例调整，无黑边
- 快捷键：
  - `q` - 退出预览
  - `s` - 切换摄像头
  - `p` - 保存截图

### 6.3 通道选择建议

| 场景 | 推荐通道 | 说明 |
|------|----------|------|
| 日常使用 | Auto | 自动选择最佳通道 |
| 视频会议 | USB | 稳定性最好 |
| 远程使用 | WiFi | 无需物理连接 |

---

## 7. 实现进度

### 7.1 已完成功能

| 功能 | 完成日期 | 说明 |
|------|----------|------|
| CameraX 基础集成 | 2026-05-04 | 预览、生命周期管理 |
| MJPEG 流服务 | 2026-05-04 | NanoHTTPD 服务器 |
| 图像旋转处理 | 2026-05-04 | 自动旋转、前置镜像 |
| NV21 色彩修正 | 2026-05-04 | 正确处理 U/V 分量 |
| ML Kit 扫码 | 2026-05-04 | 支持所有主流条码格式 |
| PC 端客户端 | 2026-05-04 | 预览窗口、保持比例 |
| 托盘扫码集成 | 2026-05-04 | 自动打开摄像头、复制到剪贴板 |
| 远程控制 API | 2026-05-04 | 打开/关闭摄像头界面 |
| USB 通道支持 | 2026-05-04 | ADB 端口转发 |
| 通道自动切换 | 2026-05-04 | USB 优先，自动回退 |
| 预览窗口优化 | 2026-05-04 | 自适应屏幕，无黑边 |
| 设置界面 IP 显示 | 2026-05-04 | 显示 IP、端口、USB 状态 |

### 7.2 计划功能

| 功能 | 优先级 | 说明 |
|------|--------|------|
| 录像功能 | P2 | 本地录制 + 流传输 |
| 音频传输 | P2 | 麦克风音频 |
| OBS 自动集成 | P2 | 自动配置虚拟摄像头 |
| 分辨率调整 | P3 | 动态调整分辨率 |

---

## 8. 故障排除

### 8.1 常见问题

**Q: USB 通道显示 "device offline"**
A: 
1. 重新插拔 USB 线
2. 在手机上重新授权 USB 调试
3. 运行 `adb kill-server` 后重试

**Q: 预览窗口自动关闭**
A: 
1. 确保手机端 Camera 界面已打开
2. 检查 USB 连接是否稳定
3. 查看控制台错误信息

**Q: WiFi 通道无法连接**
A: 
1. 确保手机和 PC 在同一局域网
2. 检查手机 IP 是否正确
3. 关闭手机防火墙/VPN

**Q: 视频流画面方向不对**
A: 已修复，图像会根据设备旋转角度自动调整

**Q: 画面色彩异常（半边绿色）**
A: 已修复，NV21 格式的 U/V 分量处理已修正

---

## 9. 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2026-05-03 | 初始方案设计 |
| v1.1 | 2026-05-04 | 完成基础功能实现 |
| v1.2 | 2026-05-04 | 修复图像旋转和色彩问题 |
| v1.3 | 2026-05-04 | 完成托盘扫码集成 |
| v1.4 | 2026-05-04 | 添加集成测试框架 |
| v1.5 | 2026-05-05 | 完整功能发布：摄像头模块、Tkinter预览窗口、实时切换、网络优化 |

---

## 10. 集成测试

### 10.1 测试框架

项目包含完整的集成测试框架，位于 `test/integration/` 目录：

| 文件 | 说明 |
|------|------|
| `test_integration.py` | 基础集成测试（服务器、API、连接） |
| `test_ui_automation.py` | UI 自动化测试（模拟用户操作） |
| `run_tests.py` | 测试运行脚本 |

### 10.2 运行测试

```bash
# 运行所有集成测试
python test/integration/run_tests.py --all

# 仅运行基础集成测试
python test/integration/run_tests.py --server

# 仅运行 UI 自动化测试
python test/integration/run_tests.py --ui
```

### 10.3 测试内容

#### 基础集成测试

1. Setup - 检查 ADB、设备连接、APK 构建
2. Start Server - 启动 PC 服务器
3. Install App - 安装 Android 应用
4. Launch App - 启动应用
5. Server Status API - 测试服务器状态 API
6. Brightness Control - 测试亮度控制
7. App-Server Connection - 测试应用与服务器连接
8. UI Navigation - 测试 UI 导航
9. Camera Functionality - 测试摄像头功能

#### UI 自动化测试

1. Setup - 唤醒设备、解锁屏幕
2. Launch App - 启动应用
3. Main Screen - 验证主屏幕元素
4. Settings Navigation - 测试设置导航
5. Channel Selection - 测试通道选择
6. Brightness Toggle - 测试亮度开关
7. Server Status - 测试服务器状态显示

---

## 11. 发布流程

### 11.1 发布脚本

使用 `release/publish.py` 自动构建、测试和打包：

```bash
python release/publish.py
```

### 11.2 发布流程

```
============================================================
 控制屏 - 发布打包工具
============================================================

  清理完成

--- 构建 ---
  APK already exists: app-debug.apk (xxx KB)

--- 集成测试 ---
  运行集成测试...
  [测试输出...]
  集成测试通过

--- 复制文件 ---
  复制 APK...
  ...
============================================================
 发布完成！
============================================================
```

### 11.3 质量保证

发布流程包含以下质量检查：

1. **APK 构建** - 确保 APK 正确构建
2. **集成测试** - 运行完整测试套件
3. **测试失败处理** - 测试失败时中止发布

---

## 12. 参考资料

- [CameraX 官方文档](https://developer.android.com/training/camerax)
- [ML Kit 条码扫描](https://developers.google.com/ml-kit/vision/barcode-scanning)
- [NanoHTTPD GitHub](https://github.com/NanoHttpd/nanohttpd)
- [OBS Studio](https://obsproject.com/)
- [ADB 命令参考](https://developer.android.com/studio/command-line/adb)
