#!/bin/bash

# 多平台文章监测系统运行脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3环境"
    exit 1
fi

# 检查依赖
if ! python3 -c "import requests" 2>/dev/null; then
    echo "正在安装依赖..."
    pip3 install -r requirements.txt
fi

# 运行监测
echo "======================================"
echo "多平台文章发布状态监测系统"
echo "======================================"

python3 main.py "$@"
