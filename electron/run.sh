#!/bin/bash

# 文章监测系统 - 快速运行脚本
# 直接运行此脚本启动应用（无需构建）

set -e

echo "启动文章监测系统..."

# 检查Node.js
if ! command -v node &> /dev/null; then
    echo "错误: 未安装 Node.js"
    echo "请访问 https://nodejs.org 下载安装"
    exit 1
fi

# 检查依赖
if [ ! -d "node_modules" ]; then
    echo "正在安装依赖..."
    npm install
fi

# 运行应用
npm start
