# USB Display Control - 服务器端

本目录包含所有 PC 服务器端的代码和脚本。

## 目录结构

```
server/
├── core/                       # 核心服务
│   ├── usb_display_control.py  # 主服务器（HTTP API + 显示器控制 + 图片投放）
│   └── windows_display_server.py # Windows 显示器控制（Flask 备用方案）
├── display/                    # 显示器相关
│   ├── get_displays.ps1        # 获取显示器信息
│   └── brightness_control.ps1  # 亮度控制脚本
├── imagecast/                  # 图片投放工具
│   ├── image_uploader.py       # 图片上传处理
│   ├── upload_real_image.py    # 上传真实图片
│   ├── upload_test_image.py    # 上传测试图片
│   ├── demo_image_casting.py   # 演示脚本
│   └── demo_simple.py          # 简单演示
├── tray/                       # 系统托盘服务
│   └── tray_service.py         # 系统托盘控制
├── tools/                      # 工具脚本
│   ├── setup_adb.py            # ADB 端口转发设置
│   ├── adb_display_server.py   # ADB 显示服务器
│   └── adb_listener.py         # ADB 事件监听器
├── scripts/                    # 启动脚本
│   └── start_usb_display.bat   # Windows 启动脚本
├── static/                     # 静态资源
│   └── test_cast.jpg           # 测试图片
└── README.md                   # 本文档
```

## 快速开始

### 方式 1: 使用启动脚本（推荐）

双击运行 `start.bat` 即可启动系统托盘服务：

```
server\start.bat
```

或命令行运行：
```bash
cd server
start.bat
```

### 方式 2: 手动启动命令行服务

```bash
cd server
python core/usb_display_control.py
```

### 方式 3: 手动启动系统托盘

```bash
cd server
python tray/tray_service.py
```

## 服务器功能

### 1. HTTP API

**端口**: 8765

#### 显示器控制 API

| API 路径 | 方法 | 功能描述 |
|---------|------|---------|
| `/status` | GET | 获取当前显示器状态 |
| `/` | POST | 切换显示器模式 |

```bash
# 获取状态
curl http://localhost:8765/status

# 切换模式
curl -X POST http://localhost:8765/ -H "Content-Type: application/json" -d '{"command": "extend"}'
```

#### 图片投放 API

| API 路径 | 方法 | 功能描述 |
|---------|------|---------|
| `/image/status` | GET | 获取当前图片状态 |
| `/image/data` | GET | 获取图片二进制数据 |
| `/image/upload` | POST | 上传图片文件 |
| `/image/cast` | POST/GET | 投放指定路径图片 |
| `/image/clear` | POST | 清除图片并关闭窗口 |
| `/image/scale` | POST | 设置缩放比例 |
| `/image/zoom-in` | POST | 放大图片 |
| `/image/zoom-out` | POST | 缩小图片 |
| `/image/zoom-reset` | POST | 重置缩放 |
| `/image/poll` | GET | 轮询更新 |
| `/image/ack-popup` | POST | 确认自动弹窗 |
| `/image/ack-close` | POST | 确认关闭窗口 |
| `/image/list` | GET | 列出目录中的图片 |

```bash
# 投放图片
curl "http://localhost:8765/image/cast?file=C:/Users/photo.jpg"

# 获取状态
curl http://localhost:8765/image/status

# 清除图片
curl -X POST http://localhost:8765/image/clear

# 缩放
curl -X POST http://localhost:8765/image/scale -H "Content-Type: application/json" -d '{"scale": 1.5}'
curl -X POST http://localhost:8765/image/zoom-in
curl -X POST http://localhost:8765/image/zoom-out
```

#### 其他 API

| API 路径 | 方法 | 功能描述 |
|---------|------|---------|
| `/brightness` | POST | 亮度控制 |
| `/ping` | GET | 健康检查 |
| `/download` | GET | 下载速度测试 |
| `/upload` | POST | 上传速度测试 |
| `/api` | GET | API 文档 |

```bash
# 亮度控制
curl -X POST http://localhost:8765/brightness -H "Content-Type: application/json" -d '{"brightness": 50}'

# 健康检查
curl http://localhost:8765/ping

# 速度测试
curl http://localhost:8765/download -o /dev/null
```

### 2. 显示器状态检测

使用 PowerShell 查询 Windows 显示配置：

```python
def get_current_display_mode():
    """
    获取当前显示器模式
    返回:
        0 - 未知
        1 - 仅第一屏
        2 - 仅第二屏
        3 - 扩展模式
        4 - 复制模式
    """
```

**检测逻辑**:
- 查询 `System.Windows.Forms.Screen.AllScreens`
- 统计活动显示器数量
- 检查主显示器是否存在
- 判断显示模式

### 3. ADB 管理

**自动功能**:
- 检测 ADB 设备连接
- 设置 ADB reverse 端口转发
- USB 断开后自动重连（后台监控线程，每 3 秒检查）
- reverse 丢失后自动重建

**ADB reverse 命令**:
```bash
adb reverse tcp:8765 tcp:8765
```

### 4. 亮度控制

通过 PowerShell 调用 Windows Gamma Ramp API 控制亮度：

```bash
powershell -ExecutionPolicy Bypass -File display/brightness_control.ps1 -Brightness 50
```

## 依赖要求

### Python 环境

- Python 3.8+
- 标准库：`http.server`, `json`, `subprocess`, `threading`
- 系统托盘（可选）：`pip install pystray Pillow`

### 系统要求

- Windows 10/11
- 支持多显示器
- Android SDK Platform Tools (ADB)

## 日志和调试

### 查看服务器日志

服务器运行时会输出：
- ADB 设备检测信息
- ADB Monitor 状态变化
- HTTP 请求日志
- 显示器状态变化
- PowerShell 检测结果

### 常见问题

**Q: 端口 8765 被占用**
```bash
netstat -ano | findstr :8765
taskkill /F /PID <进程 ID>
```

**Q: ADB 设备未识别**
```bash
adb devices
adb kill-server
adb start-server
```

**Q: USB 重连后无法恢复**
- 服务器会自动检测并重建 ADB reverse
- 检查 ADB Monitor 日志输出
- 手动执行：`adb reverse tcp:8765 tcp:8765`

**Q: 显示器状态检测失败**
- 确保显示器驱动正常
- 检查 Windows 显示设置
- 更新显卡驱动

## 安全注意事项

1. **网络访问**: 服务器监听 `0.0.0.0:8765`，支持 WiFi 连接
2. **无认证**: 当前版本无需认证（仅本地使用）
3. **权限**: 需要普通用户权限即可运行

---

**最后更新**: 2026-05-03  
**版本**: v1.4.0
