#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 app_info.py 生成 Java 常量类和 strings.xml
用于 Android 端和 Python 端保持信息同步
"""

import sys
from pathlib import Path

# 添加 server/core 到路径
SERVER_CORE_PATH = Path(__file__).parent.parent / "server" / "core"
sys.path.insert(0, str(SERVER_CORE_PATH))

from app_info import (
    APP_NAME,
    APP_VERSION,
    APP_COPYRIGHT,
    APP_DESCRIPTION,
    APP_AUTHOR,
    APP_REPO,
    VERSION_CHANGELOG
)

# 生成的文件路径
JAVA_FILE_PATH = Path(__file__).parent.parent / "app" / "src" / "main" / "java" / \
    "com" / "volcano" / "controlhub" / "AppInfo.java"

STRINGS_XML_PATH = Path(__file__).parent.parent / "app" / "src" / "main" / "res" / \
    "values" / "strings.xml"


def generate_changelog_constant():
    """生成更新日志字符串常量"""
    lines = []
    for ver_info in VERSION_CHANGELOG:
        line = f"v{ver_info['version']}"
        if ver_info['date']:
            line += f" ({ver_info['date']})"
        lines.append(line)
        for change in ver_info['changes']:
            lines.append(f"• {change}")
        lines.append("")
    return "\\n".join(lines).rstrip()


def generate_java_code():
    """生成完整的 Java 代码"""
    changelog_text = generate_changelog_constant()
    
    java_code = f"""
// Auto-generated file - DO NOT EDIT MANUALLY!
// Generated from server/core/app_info.py by tools/generate_app_info.py

package com.volcano.controlhub;

public final class AppInfo {{
    public static final String APP_NAME = "{APP_NAME}";
    public static final String APP_VERSION = "{APP_VERSION}";
    public static final String APP_COPYRIGHT = "{APP_COPYRIGHT}";
    public static final String APP_DESCRIPTION = "{APP_DESCRIPTION}";
    public static final String APP_AUTHOR = "{APP_AUTHOR}";
    public static final String APP_REPO = "{APP_REPO}";
    
    public static final String CHANGELOG = "{changelog_text}";
}}
"""
    return java_code.strip()


def generate_strings_xml():
    """生成 strings.xml 内容，保留非生成的条目"""
    return f'''<resources>
    <string name="app_name">控制屏</string>
    <string name="time_format">HH:mm:ss</string>
    <string name="date_format">yyyy MM dd</string>
    <string name="day_format">EEEE</string>
    <string name="app_version">v{APP_VERSION}</string>
    <string name="app_copyright">{APP_COPYRIGHT}</string>
</resources>'''


def main():
    """主函数 - 生成所有文件"""
    print(f"Generating from: {SERVER_CORE_PATH / 'app_info.py'}")
    print()
    
    # 1. 生成 Java 文件
    print(f"[1/2] Generating {JAVA_FILE_PATH.name}...")
    JAVA_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(JAVA_FILE_PATH, "w", encoding="utf-8") as f:
        f.write(generate_java_code())
    print(f"      OK: {JAVA_FILE_PATH}")
    
    # 2. 生成 strings.xml
    print(f"[2/2] Generating {STRINGS_XML_PATH.name}...")
    STRINGS_XML_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STRINGS_XML_PATH, "w", encoding="utf-8") as f:
        f.write(generate_strings_xml())
    print(f"      OK: {STRINGS_XML_PATH}")
    
    # 打印验证信息
    print()
    print("Generated content summary:")
    print(f"  APP_NAME = {APP_NAME}")
    print(f"  APP_VERSION = {APP_VERSION}")
    print(f"  APP_COPYRIGHT = {APP_COPYRIGHT}")
    print(f"  CHANGELOG has {len(VERSION_CHANGELOG)} versions")


if __name__ == "__main__":
    main()
