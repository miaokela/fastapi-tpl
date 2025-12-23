#!/bin/bash

# 设置错误时退出
set -e

echo "=== 开发环境启动 ==="

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "虚拟环境不存在，请先运行setup.sh"
    exit 1
fi

# 激活虚拟环境
source .venv/bin/activate

# 启动FastAPI应用
echo "启动FastAPI应用..."
echo "访问地址:"
echo "  - API文档: http://localhost:8000/docs"
echo "  - ReDoc文档: http://localhost:8000/redoc"
echo "  - 健康检查: http://localhost:8000/health"
echo ""

# 使用uvicorn启动，支持热重载
uvicorn main:app --reload --host 0.0.0.0 --port 8000