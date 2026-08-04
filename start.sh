#!/bin/bash
# Polymarket 套利监控 Web App 启动脚本

echo "🚀 启动 Polymarket 套利监控..."

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 请先安装 Python 3"
    exit 1
fi

# 进入项目目录
cd "$(dirname "$0")"

# 安装依赖
echo "📦 安装依赖..."
pip3 install -r requirements.txt

# 启动应用
echo "🌐 启动Web服务器..."
echo "📱 手机访问: http://你的电脑IP:5000"
echo "💻 电脑访问: http://localhost:5000"
echo ""
echo "按 Ctrl+C 停止"
echo ""

python3 app.py