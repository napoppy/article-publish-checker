# 文章监测系统

多平台文章发布状态+关键词监测系统的Electron桌面应用。

## 支持平台

- **Windows** (x64) - NSIS安装包
- **macOS** (Intel x64, Apple Silicon) - DMG安装包

## 构建命令

### 安装依赖
```bash
npm install
```

### 开发模式
```bash
npm start
```

### 构建安装包

**macOS (Intel)**
```bash
npm run dist:mac
```

**Windows**
```bash
npm run dist:win
```

## 输出目录

构建完成后，安装包位于 `dist/` 目录：

- macOS: `dist/mac/` (`.dmg` 文件)
- Windows: `dist/win-unpacked/` (便携版) 或 `dist/文章监测系统 Setup x.x.x.exe` (安装版)

## 系统要求

- macOS 10.15 (Catalina) 或更高版本
- Windows 10 或更高版本
- 至少 4GB 内存
- 100MB 可用磁盘空间
