#!/bin/bash

# 设置错误时退出
set -e

echo "=== 开发环境启动 ==="

# 启动FastAPI应用
echo "启动FastAPI应用..."
echo "访问地址:"
echo "  - API文档: http://localhost:8000/docs"
echo "  - ReDoc文档: http://localhost:8000/redoc"
echo "  - 健康检查: http://localhost:8000/health"
echo ""

# 使用uvicorn启动，支持热重载
uvicorn main:app --reload --host 0.0.0.0 --port 8000