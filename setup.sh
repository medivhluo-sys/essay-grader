#!/bin/bash
set -e

echo "========================================="
echo "  作文批改助手 — 安装脚本"
echo "========================================="
echo ""

# Check Python version
echo "[1/4] 检查 Python 版本..."
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "0.0")
REQUIRED="3.10"

if [ "$(printf '%s\n' "$REQUIRED" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED" ]; then
    echo "错误：需要 Python 3.10 或更高版本，当前版本：$PYTHON_VERSION"
    echo "请安装 Python 3.10+ 后重试：https://www.python.org/downloads/"
    exit 1
fi
echo "  ✓ Python $PYTHON_VERSION"

# Create virtual environment
echo "[2/4] 创建虚拟环境..."
cd "$(dirname "$0")"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "  ✓ 虚拟环境已创建"
else
    echo "  ✓ 虚拟环境已存在"
fi

# Install dependencies
echo "[3/4] 安装依赖..."
source venv/bin/activate
pip install -r requirements.txt -q
echo "  ✓ 依赖安装完成"

# Setup .env
echo "[4/4] 配置 API Key..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "  ✓ 已创建 .env 文件"
    echo ""
    echo "⚠️  请编辑 .env 文件，填入你的 DeepSeek API Key："
    echo "   DEEPSEEK_API_KEY=你的密钥"
    echo ""
    echo "   获取 API Key：https://platform.deepseek.com/api_keys"
else
    echo "  ✓ .env 文件已存在"
fi

echo ""
echo "========================================="
echo "  安装完成！"
echo "========================================="
echo ""
echo "启动方式："
echo "  ./venv/bin/python main.py"
echo ""
echo "然后在浏览器打开：http://localhost:8001"
