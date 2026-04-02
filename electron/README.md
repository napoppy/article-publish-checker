# Electron桌面应用构建指南

## 运行应用

### 开发模式
```bash
cd electron
npm install
npm start
```

### 构建Windows安装包
```bash
npm install
npm run dist:win
```

安装包将生成在 `dist/` 目录下。

## 注意事项

- 构建需要Node.js 18+环境
- Windows安装包为NSIS格式
- Mac版本需要配置code signing（可选）
