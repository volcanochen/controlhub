# Tools

## generate_app_info.py

### 作用

从 **单一真实源** (`server/core/app_info.py`) 生成：

- `app/src/main/java/com/volcano/controlhub/AppInfo.java` - Java常量类
- `app/src/main/res/values/strings.xml` - Android资源文件

### 谁来执行？

| 场景 | 执行者 |
|------|--------|
| **更新版本/更新日志** | 开发者手动执行 |
| **发布版本** | 自动：`release/publish.py` 会先调用它 |

### 用法

```bash
# 1. 修改 app_info.py（唯一需要手动改的文件）

# 2. 运行生成脚本
python tools/generate_app_info.py
```

### 工作原理

```
app_info.py (单一源)
    ↓
generate_app_info.py
    ├─→ AppInfo.java (Java)
    └─→ strings.xml (Android)
```
