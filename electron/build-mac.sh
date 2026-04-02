#!/bin/bash

# 文章监测系统 - macOS 构建脚本
# 在Mac上运行此脚本即可构建

set -e

echo "======================================"
echo "文章监测系统 - macOS 构建工具"
echo "======================================"

# 检查Node.js
if ! command -v node &> /dev/null; then
    echo "错误: 未安装 Node.js"
    echo "请访问 https://nodejs.org 下载安装"
    exit 1
fi

echo "Node.js 版本: $(node --version)"
echo "npm 版本: $(npm --version)"
echo ""

# 安装依赖
echo "正在安装依赖..."
npm install

# 构建macOS版本
echo "正在构建macOS安装包..."
npm run dist:mac

echo ""
echo "======================================"
echo "构建完成！"
echo "安装包位于: dist/mac/*.dmg"
echo "======================================"

# 自动打开文件夹
open dist/mac/
