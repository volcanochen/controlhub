# USB Display Control - 服务器端

本目录包含所有 PC 服务器端的代码和脚本。

## 文件说明

### 核心服务器

| 文件名 | 说明 | 用途 |
|--------|------|------|
| `usb_display_control.py` | 主服务器 | HTTP 服务器 + 显示器控制 |
| `windows_display_server.py` | 显示服务 | Windows 显示器状态检测 |
| `adb_display_server.py` | ADB 服务 | ADB 设备监听和管理 |
| `adb_listener.py` | ADB 监听器 | ADB 事件监听 |

### 启动脚本

| 文件名 | 说明 | 用途 |
|--------|------|------|
| `start_usb_display.bat` | 启动脚本 | 一键启动服务器 |

## 快速开始

### 方式 1: 使用启动脚本（推荐）

```bash
cd server
start_usb_display.bat
```

### 方式 2: 手动启动

```bash
cd server
python usb_display_control.py
```

## 服务器功能

### 1. HTTP API

**端口**: 8765

**API 端点**:

#### GET /status
获取当前显示器状态

```bash
curl http://localhost:8765/status
```

**响应示例**:
```json
{
  "status": "ok",
  "mode": 1,
  "mode_name": "internal",
  "server": "running",
  "realtime": true
}
```

#### POST /
切换显示器模式

```bash
curl -X POST http://localhost:8765/ \
  -H "Content-Type: application/json" \
  -d '{"command": "extend"}'
```

**请求参数**:
- `command`: 显示模式
  - `internal` - 仅第一屏
  - `external` - 仅第二屏
  - `extend` - 扩展模式
  - `clone` - 复制模式

**响应示例**:
```json
{
  "success": true,
  "message": "[OK] Display switched to: extend"
}
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
- 监听设备断开事件
- 自动重连机制

**ADB reverse 命令**:
```bash
adb reverse tcp:8765 tcp:8765
```

## 依赖要求

### Python 环境

- Python 3.8+
- 无需额外 pip 包（使用标准库）

### 系统要求

- Windows 10/11
- 支持多显示器
- Android SDK Platform Tools (ADB)

### 可选依赖

如需更高级的功能，可以安装：

```bash
pip install -r requirements.txt
```

## 技术细节

### 显示器切换实现

调用 Windows 系统命令：

```python
import subprocess

def switch_display(mode):
    cmd_map = {
        'internal': '/internal',
        'external': '/external',
        'extend': '/extend',
        'clone': '/clone'
    }
    
    cmd = f"DisplaySwitch.exe {cmd_map[mode]}"
    subprocess.run(cmd, shell=True)
    time.sleep(5)  # 等待切换完成
```

### 实时状态检测

使用 PowerShell 脚本：

```powershell
Add-Type -AssemblyName System.Windows.Forms
$screens = [System.Windows.Forms.Screen]::AllScreens
$count = $screens.Count
$primary = $screens | Where-Object { $_.Primary }

Write-Host "COUNT:$count"
Write-Host "PRIMARY:$($primary -ne $null)"
```

### HTTP 服务器实现

使用 Python 标准库：

```python
from http.server import HTTPServer, BaseHTTPRequestHandler

class DisplayHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/status':
            mode = get_current_display_mode()
            response = {'status': 'ok', 'mode': mode}
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
    
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))
        
        command = data.get('command')
        success, message = switch_display(command)
        
        self.send_response(200)
        self.end_headers()
        self.wfile.write(json.dumps({'success': success}).encode())
```

## 日志和调试

### 查看服务器日志

服务器运行时会输出：
- ADB 设备检测信息
- HTTP 请求日志
- 显示器状态变化
- PowerShell 检测结果

### 常见问题

**Q: 端口 8765 被占用**
```bash
# 查找占用端口的进程
netstat -ano | findstr :8765
# 终止进程
taskkill /F /PID <进程 ID>
```

**Q: ADB 设备未识别**
```bash
# 检查 ADB 设备
adb devices
# 重启 ADB 服务器
adb kill-server
adb start-server
```

**Q: 显示器状态检测失败**
- 确保显示器驱动正常
- 检查 Windows 显示设置
- 更新显卡驱动

## 开发说明

### 添加新 API

1. 在 `DisplayHandler` 类中添加新的处理方法
2. 实现业务逻辑
3. 返回 JSON 响应

### 修改显示模式

如需支持更多模式，修改：
- `mode_map` 字典（添加新模式）
- `switch_display()` 函数（实现切换逻辑）
- `get_current_display_mode()` 函数（支持新模式检测）

## 安全注意事项

1. **本地访问**: 服务器仅监听 localhost，外部无法访问
2. **无认证**: 当前版本无需认证（仅本地使用）
3. **权限**: 需要普通用户权限即可运行

## 性能优化

### 已实施优化

- 实时状态检测（无缓存）
- 切换后等待 5 秒（确保完成）
- ADB 自动重连机制

### 未来优化

- 连接池复用
- 增量状态更新
- WebSocket 支持

---

**最后更新**: 2026-04-27  
**版本**: v1.0.0
