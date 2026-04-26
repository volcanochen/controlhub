# 低耗电桌面时钟应用

一个专为旧手机设计的低耗电桌面时钟应用，适合长时间作为桌面时钟使用。

## 功能特性

- 🕒 实时时钟显示（每秒更新）
- 📅 日期和星期显示
- 🌙 沉浸式全屏模式
- 🔋 低耗电设计，保持屏幕常亮
- 📱 大字体显示，清晰易读
- 🎨 黑色背景，减少耗电量

## 系统要求

- Android 5.0 (API 21) 或更高版本
- 特别为三星Note8（Android 9）优化

## 在Android Studio中构建和运行

### 1. 打开项目
- 启动 Android Studio
- 选择 "Open an existing project"
- 导航到 `C:\VOLCANO\myws\andr` 目录并打开

### 2. 同步项目
- Android Studio会自动检测项目结构
- 如果提示 "Gradle Sync Failed"，点击 "Sync Now" 按钮
- 等待依赖下载和同步完成

### 3. 构建项目
- 点击菜单栏的 "Build" → "Make Project"
- 或使用快捷键 `Ctrl+F9`
- 等待构建完成（首次构建可能需要几分钟）

### 4. 运行应用

#### 通过USB连接手机
- 连接您的三星Note8手机到电脑
- 在手机上启用USB调试模式：
  - 打开设置 → 关于手机 → 连续点击版本号7次
  - 返回设置 → 开发者选项 → 打开USB调试
- 在Android Studio中点击绿色的 "Run" 按钮（或按Shift+F10）
- 在弹出的设备选择窗口中选择您的Note8
- 点击 "OK" 开始安装和运行应用

#### 使用模拟器
- 在设备选择下拉菜单中点击 "Device Manager"
- 创建新的虚拟设备
- 选择设备类型（推荐Pixel 2）
- 选择Android版本（推荐API 30）
- 启动模拟器
- 点击 "Run" 按钮运行应用

## 应用使用说明

1. 应用启动后会自动进入全屏模式
2. 时间会每秒更新
3. 日期和星期会自动更新
4. 屏幕会保持常亮
5. 按返回键或Home键可以退出应用

## 项目结构

```
c:\VOLCANO\myws\andr\
├── app/
│   ├── src/
│   │   └── main/
│   │       ├── java/com/example/clockapp/
│   │       │   ├── ClockApp.java (原Activity)
│   │       │   └── MainActivity.java (主Activity)
│   │       ├── res/
│   │       │   ├── layout/
│   │       │   │   ├── activity_clock.xml
│   │       │   │   └── activity_main.xml
│   │       │   └── values/
│   │       │       ├── strings.xml
│   │       │       └── styles.xml
│   │       └── AndroidManifest.xml
│   └── build.gradle
├── gradle/
│   └── wrapper/
│       └── gradle-wrapper.properties
├── gradle-7.0.2/ (本地Gradle)
├── build.gradle
├── settings.gradle
├── local.properties (SDK配置)
└── gradlew.bat (Gradle包装器)
```

## 低耗电设计原理

1. 使用 `FLAG_KEEP_SCREEN_ON` 代替 WakeLock，减少耗电量
2. 黑色背景，AMOLED屏幕更省电
3. 减少不必要的UI更新
4. 禁用窗口动画，减少CPU使用
5. 使用Handler精确控制更新时间

## 故障排除

### Gradle同步失败
- 检查网络连接
- 使用国内镜像源
- 清理缓存：File → Invalidate Caches / Restart

### 构建失败
- 检查Android SDK是否安装完整
- 确保SDK版本匹配
- 清理项目：Build → Clean Project，然后重新构建

### 应用无法在手机上运行
- 检查手机是否启用USB调试
- 确保手机与电脑连接正常
- 尝试重新插拔USB线

## 技术栈

- 语言：Java
- 最低SDK：API 21 (Android 5.0)
- 目标SDK：API 30 (Android 11)
- 构建工具：Gradle 7.0.2
- Android Gradle插件：7.0.2

## 许可证

本项目仅供学习和个人使用。

## 联系方式

如有问题或建议，请随时联系。
