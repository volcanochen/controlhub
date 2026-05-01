# 网络测试

测试手机和电脑之间的网络通信功能。

## 文件说明

| 文件名 | 说明 |
|--------|------|
| `test_adb.py` | ADB 连接和设备检测测试 |
| `test_usb_speed.py` | USB 网络速度测试（Ping/下载/上传） |

## 运行测试

### ADB 连接测试

```bash
python test_adb.py
```

测试内容：
- ADB 版本检测
- 设备连接
- ADB reverse 端口转发设置

### USB 网络速度测试

前置条件：先启动服务器
```bash
cd ../../server
python usb_display_control.py
```

然后运行测试：
```bash
python test_usb_speed.py
```

测试内容：
- Ping 延迟
- 下载速度
- 上传速度

## 通信方式

系统支持两种通信方式：

1. **USB (ADB reverse)** — 手机通过 localhost:8765 访问
2. **WiFi** — 手机通过 http://<PC_IP>:8765 访问

服务器统一监听 0.0.0.0:8765，同时支持两种连接方式。

---

**最后更新**: 2026-05-01
