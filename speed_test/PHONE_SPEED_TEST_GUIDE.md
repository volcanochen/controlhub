# 📱 手机 - 电脑网络速度测试指南

## 🎯 测试目的
测试 Android 手机与 Windows 电脑之间的**真实 WiFi 网络连接速度**。

## ✅ 已安装应用

最新版 "控制屏" 应用已安装到手机，包含网络速度测试功能。

## 🚀 测试步骤

### 步骤 1：启动电脑端的测试服务器

**方法 1**：双击运行
```
c:\VOLCANO\myws\andr\test\start_speed_test_server.bat
```

**方法 2**：命令行运行
```bash
cd c:\VOLCANO\myws\andr\test
python simple_speed_test.py
```

服务器启动后会显示：
```
============================================================
Network Speed Test Server
============================================================

Server starting on port 8766...
Local: http://127.0.0.1:8766
LAN: http://192.168.50.111:8766  <-- 这是手机要连接的地址

Use Android app to connect and test speed
Press Ctrl+C to stop
```

### 步骤 2：在手机上运行测试

1. 确保手机和电脑在**同一 WiFi 网络**（192.168.50.x）
2. 打开 "控制屏" 应用
3. 在主界面上找到 **"📊 网速测试"** 按钮（蓝色）
4. 点击按钮开始测试

### 步骤 3：查看测试结果

测试会自动进行 3 个项目：

1. **Ping 延迟测试**（5 次）
   - 测试手机到电脑的往返时间
   - 单位：毫秒（ms）

2. **下载速度测试**（5 秒）
   - 从电脑下载数据到手机
   - 测试电脑 → 手机的速度

3. **上传速度测试**（10MB）
   - 从手机上传数据到电脑
   - 测试手机 → 电脑的速度

测试结果会实时显示在手机的对话框中。

## 📊 结果解读

### Ping 延迟
- **< 10ms**: 优秀 ⭐⭐⭐⭐⭐
- **10-30ms**: 良好 ⭐⭐⭐⭐
- **30-50ms**: 一般 ⭐⭐⭐
- **> 50ms**: 较差 ⭐⭐

### 带宽速度
- **> 50 Mbps**: 优秀（5GHz WiFi）
- **20-50 Mbps**: 良好（2.4GHz WiFi）
- **10-20 Mbps**: 一般
- **< 10 Mbps**: 较差

## 🔧 故障排查

### 无法连接服务器
1. 检查手机和电脑是否在同一 WiFi
2. 检查电脑防火墙是否允许 8766 端口
3. 确认服务器正在运行

### 测试速度慢
1. 靠近 WiFi 路由器
2. 使用 5GHz WiFi 频段（如果支持）
3. 减少网络干扰

### 应用中没有 "网速测试" 按钮
- 确认已安装最新版应用
- 按钮在主界面，蓝色，写着 "📊 网速测试"

## 📝 测试配置

**电脑 IP**: 192.168.50.111  
**测试端口**: 8766  
**测试协议**: HTTP  

如需修改服务器地址，编辑：
```
app/src/main/java/com/example/clockapp/NetworkSpeedTester.java
```
第 29 行的 `SERVER_URL` 常量。

## 🛠️ 相关文件

- `test/simple_speed_test.py` - Python 测试服务器
- `app/src/main/java/com/example/clockapp/NetworkSpeedTester.java` - Android 测试工具
- `app/src/main/res/layout/activity_main.xml` - 主界面布局（包含测试按钮）
- `test/NETWORK_SPEED_TEST.md` - 详细技术文档

## 💡 提示

- 测试完成后，服务器会继续运行，可以多次测试
- 按 Ctrl+C 停止服务器
- 测试结果会显示在手机上，不会自动保存

---

**准备就绪！现在可以开始测试了！** 🚀
