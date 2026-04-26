# USB Display Control - 产品测试规范

## 1. 概述

本文档定义了 USB Display Control 系统的测试规范，用于确保产品质量和功能完整性。

### 1.1 测试范围
- Python 服务器端功能
- 显示器状态检测
- 显示器切换控制
- Android 客户端通信
- 错误处理和边界条件
- 系统集成

### 1.2 系统架构
```
┌─────────────┐      USB/ADB       ┌─────────────┐
│  Android    │ ←─────────────────→ │   PC Server │
│    App      │    tcp:8765        │  (Python)   │
└─────────────┘                     └──────┬──────┘
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
- Android 应用已安装
- 显示器驱动正常

### 2.3 前置检查
```bash
# 检查 ADB 连接
adb devices

# 检查 ADB reverse
adb reverse --list

# 检查服务器端口
netstat -ano | findstr :8765
```

## 3. 测试用例详细规范

### 3.1 服务器基础功能测试 (TEST-001)

#### TEST-001-01: 服务器进程运行
- **目的**: 验证服务器进程正常运行
- **步骤**: 
  1. 启动 usb_display_control.py
  2. 检查进程列表
- **预期**: python.exe 进程存在
- **自动化**: `tasklist /FI "IMAGENAME eq python.exe"`

#### TEST-001-02: 服务器端口监听
- **目的**: 验证服务器正确监听端口
- **步骤**:
  1. 启动服务器
  2. 检查端口 8765 状态
- **预期**: 端口处于 LISTENING 状态
- **自动化**: `netstat -ano | findstr :8765`

#### TEST-001-03: 健康检查 API
- **目的**: 验证 /status API 正常工作
- **步骤**:
  1. 发送 GET /status 请求
  2. 检查响应
- **预期**: 
  - HTTP 200
  - JSON 包含 status: "ok"
- **自动化**: 
  ```powershell
  Invoke-WebRequest -Uri "http://localhost:8765/status"
  ```

#### TEST-001-04: 响应格式验证
- **目的**: 验证 API 响应包含所有必需字段
- **必需字段**:
  - status (string)
  - mode (int): 0-4
  - mode_name (string): internal/external/extend/clone
  - server (string): "running"
  - realtime (bool): true
- **预期**: 所有字段存在且类型正确

### 3.2 显示器状态检测测试 (TEST-002)

#### TEST-002-01: 实时检测标记
- **目的**: 验证服务器使用实时检测而非缓存
- **步骤**:
  1. 查询 /status API
  2. 检查 realtime 字段
- **预期**: realtime = true

#### TEST-002-02: 模式值范围
- **目的**: 验证模式值在有效范围内
- **有效值**:
  - 0: unknown
  - 1: primary only (仅第一屏)
  - 2: secondary only (仅第二屏)
  - 3: extended (扩展模式)
  - 4: duplicate (复制模式)
- **预期**: mode ∈ {0, 1, 2, 3, 4}

#### TEST-002-03: PowerShell 检测脚本
- **目的**: 验证 PowerShell 检测脚本正确执行
- **步骤**:
  1. 调用 get_current_display_mode()
  2. 验证返回值
- **预期**: 
  - 执行时间 < 10 秒
  - 返回有效模式值
- **检测原理**:
  ```powershell
  Add-Type -AssemblyName System.Windows.Forms
  $screens = [System.Windows.Forms.Screen]::AllScreens
  ```

### 3.3 显示器切换控制测试 (TEST-003)

#### TEST-003-01: 切换到仅第一屏
- **目的**: 验证切换到 internal 模式
- **步骤**:
  1. POST / {"command": "internal"}
  2. 等待 8 秒
  3. 查询状态
- **预期**: mode = 1

#### TEST-003-02: 切换到仅第二屏
- **目的**: 验证切换到 external 模式
- **步骤**:
  1. POST / {"command": "external"}
  2. 等待 8 秒
  3. 查询状态
- **预期**: mode = 2

#### TEST-003-03: 切换到扩展模式
- **目的**: 验证切换到 extend 模式
- **步骤**:
  1. POST / {"command": "extend"}
  2. 等待 8 秒
  3. 查询状态
- **预期**: mode = 3

#### TEST-003-04: 切换响应时间
- **目的**: 验证切换操作的响应时间
- **要求**:
  - API 响应时间 < 1 秒
  - 总切换时间（含等待）< 10 秒
- **预期**: 符合时间要求

#### TEST-003-05: 切换后状态持久化
- **目的**: 验证切换后状态稳定
- **步骤**:
  1. 切换模式
  2. 等待 10 秒
  3. 连续查询 3 次状态
- **预期**: 3 次查询结果一致

### 3.4 Android 端通信测试 (TEST-004)

#### TEST-004-01: ADB 设备连接
- **目的**: 验证 Android 设备正确连接
- **步骤**: `adb devices`
- **预期**: 设备状态为 "device"

#### TEST-004-02: ADB reverse 设置
- **目的**: 验证端口转发正确配置
- **步骤**: `adb reverse --list`
- **预期**: 包含 "tcp:8765"

#### TEST-004-03: Android 应用安装
- **目的**: 验证 ClockApp 已安装
- **步骤**: 
  ```bash
  adb shell pm list packages | grep com.example.clockapp
  ```
- **预期**: 包名存在

#### TEST-004-04: Android 端 HTTP 请求
- **目的**: 验证 Android 端可访问服务器
- **步骤**:
  ```bash
  adb shell curl http://localhost:8765/status
  ```
- **预期**: 返回有效 JSON

### 3.5 错误处理测试 (TEST-005)

#### TEST-005-01: 无效命令处理
- **目的**: 验证服务器拒绝无效命令
- **步骤**: POST / {"command": "invalid"}
- **预期**: success = false 或错误响应

#### TEST-005-02: 非法 HTTP 方法
- **目的**: 验证服务器处理非 POST 请求
- **步骤**: 发送 PUT/DELETE 请求
- **预期**: 返回错误或忽略

#### TEST-005-03: PowerShell 脚本超时
- **目的**: 验证超时处理机制
- **要求**: 脚本超时时间 ≤ 10 秒
- **预期**: 不阻塞服务器

#### TEST-005-04: ADB 断开恢复
- **目的**: 验证 ADB 断开后的恢复能力
- **步骤**:
  1. 断开 USB
  2. 重新连接
  3. 检查服务器状态
- **预期**: 服务器自动重连

### 3.6 集成测试 (TEST-006)

#### TEST-006-01: 完整工作流程
- **目的**: 验证端到端完整流程
- **步骤**:
  1. 获取初始状态
  2. 切换到扩展模式
  3. 验证状态
  4. 切换到仅第一屏
  5. 验证状态
  6. 恢复初始状态
- **预期**: 所有步骤成功

#### TEST-006-02: 多用户并发
- **目的**: 验证并发请求处理
- **步骤**: 同时发送多个请求
- **预期**: 所有请求正确处理

#### TEST-006-03: 长时间稳定性
- **目的**: 验证长时间运行稳定性
- **步骤**: 运行 1 小时，周期性查询状态
- **预期**: 无崩溃、无内存泄漏

## 4. 测试执行

### 4.1 自动化测试脚本

运行所有测试：
```bash
cd c:\VOLCANO\myws\andr
python test_display_control.py
```

### 4.2 手动测试检查单

#### 启动前检查
- [ ] 显示器连接正常
- [ ] USB 线连接牢固
- [ ] ADB 驱动已安装
- [ ] Python 环境就绪

#### 功能测试
- [ ] 服务器启动成功
- [ ] 状态指示灯正确
- [ ] 切换第一屏正常
- [ ] 切换第二屏正常
- [ ] 扩展模式正常
- [ ] Android 端显示同步

#### 性能测试
- [ ] 状态更新延迟 < 1 秒
- [ ] 切换响应时间 < 10 秒
- [ ] 无卡顿或崩溃

## 5. 缺陷管理

### 5.1 缺陷严重程度分类

- **Critical**: 系统崩溃、数据丢失
- **Major**: 主要功能失效
- **Minor**: 次要功能问题
- **Cosmetic**: 界面或文档问题

### 5.2 缺陷报告模板

```
缺陷 ID: DEFECT-XXX
标题：[简短描述]
严重程度：[Critical/Major/Minor/Cosmetic]
复现步骤:
1. ...
2. ...
预期结果：...
实际结果：...
环境信息：
- Windows 版本：
- Python 版本：
- Android 版本：
```

## 6. 发布标准

### 6.1 必须满足的条件
- [ ] 所有 TEST-001 到 TEST-005 测试通过
- [ ] TEST-006 集成测试通过
- [ ] 无 Critical 或 Major 缺陷
- [ ] 性能指标达标
- [ ] 文档完整

### 6.2 测试报告
发布前必须生成测试报告，包括：
- 测试覆盖率
- 通过率统计
- 已知问题列表
- 性能测试结果

## 7. 附录

### 7.1 模式映射表

| 模式值 | 模式名称 | 说明 |
|--------|---------|------|
| 0 | unknown | 未知状态 |
| 1 | internal | 仅第一屏（笔记本内置） |
| 2 | external | 仅第二屏（外接显示器） |
| 3 | extend | 扩展模式（双屏） |
| 4 | clone | 复制模式（双屏相同内容） |

### 7.2 API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| / | GET | 健康检查 |
| /status | GET | 获取显示器状态 |
| / | POST | 执行显示器切换 |

### 7.3 相关文件

- `usb_display_control.py` - 服务器主程序
- `test_display_control.py` - 自动化测试脚本
- `app/src/main/java/com/example/clockapp/MainActivity.java` - Android 主程序
- `app/src/main/java/com/example/clockapp/WindowsDisplayController.java` - Android 显示控制器

---

**文档版本**: 1.0  
**最后更新**: 2026-04-27  
**维护者**: Development Team
