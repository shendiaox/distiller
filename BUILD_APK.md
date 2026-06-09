# Distiller Android APK 构建指南

## 前提条件

1. **Linux 环境**（WSL2 Ubuntu 或实体 Linux）
2. 安装 Buildozer：
   ```bash
   pip install buildozer
   sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev
   ```

## 构建步骤

```bash
# 1. 进入项目目录
cd Distiller

# 2. 替换入口文件（Buildozer 要求 main.py 作为入口）
cp main.py desktop_main.py.backup
cp android_app.py main.py

# 3. 构建 APK
buildozer android debug

# 4. 恢复桌面版入口
cp desktop_main.py.backup main.py
```

首次构建约 20-40 分钟（需下载 Android SDK/NDK）。
构建完成后 APK 在 `bin/` 目录下。

## 架构说明

- **后端**：Flask 运行在手机本地 localhost:8888
- **前端**：WebView 加载本地 Flask 页面
- **知识库**：SQLite + TF-IDF（完全离线）
- **AI 对话**：通过 DeepSeek API（需联网）
- **搜索**：Bing 中国（需联网）

## 安装到手机

```bash
buildozer android deploy run
```

或手动安装 `bin/distiller-*.apk`
