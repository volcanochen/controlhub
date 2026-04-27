# Windows 显示器控制功能使用说明

## 功能概述

Android 应用可以通过 RPC 远程控制 Windows 电脑的显示器显示模式：
- 仅第一屏（笔记本内置屏幕）
- 仅第二屏（外接显示器）
- 扩展模式（双屏同时使用）
- 复制模式（双屏显示相同内容）

## 架构说明

```
Android 手机 → HTTP RPC → Windows 服务端 → DisplaySwitch.exe → 切换显示器
```

## 使用步骤

### 1. 在 Windows 电脑上启动 RPC 服务端

```bash
# 安装依赖
pip install flask flask-cors

# 运行服务端
python windows_display_server.py
```

服务端启动后会显示监听地址，例如：
```
==================================================
Windows 显示器控制 RPC 服务端
==================================================
服务器地址：http://192.168.50.100:8080
本地地址：http://127.0.0.1:8080
==================================================
```

### 2. 配置 Android 应用

修改 `WindowsDisplayController.java` 中的服务器地址：

```java
private static final String SERVER_URL = "http://192.168.50.100:8080";
```

**改成你的 Windows 电脑 IP 地址**（从服务端启动信息中获取）

### 3. 确保网络连接

- Windows 电脑和 Android 手机必须在**同一 WiFi 网络**
- 确保防火墙允许 8080 端口访问

### 4. 测试功能

在 Android 应用中：
1. 打开应用
2. 找到 "Windows 显示器控制" 部分
3. 切换 Switch 按钮
4. 观察 Windows 显示器是否切换

## API 接口

### POST /api/display
切换显示器模式

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

### GET /api/display/status
获取当前显示器状态

### GET /api/health
健康检查

## 故障排查

### 1. 连接超时
- 检查 Windows 防火墙是否允许 8080 端口
- 确认 IP 地址配置正确
- 确认手机和电脑在同一网络

### 2. 命令执行失败
- 确保在 Windows 系统上运行（DisplaySwitch.exe 是 Windows 专用）
- 以管理员权限运行服务端

### 3. 无法切换
- 确认电脑连接了多个显示器
- 检查显示器设置

## 安全提示

⚠️ **注意**：这个服务端只在局域网内使用，不要暴露到公网！

如需增加安全性，可以：
1. 添加认证 Token
2. 使用 HTTPS
3. 限制访问 IP 白名单

## 自定义开发

### 添加更多功能

编辑 `windows_display_server.py`，添加新的 API 端点：

```python
@app.route('/api/custom', methods=['POST'])
def api_custom():
    # 你的自定义逻辑
    return jsonify({"success": True})
```

### 修改 Android 端

编辑 `WindowsDisplayController.java`，添加新的 RPC 调用方法。
