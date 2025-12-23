#!/bin/bash

echo "=== FastAPI 开发服务器启动 ==="

# 使用uv运行应用
echo "启动FastAPI服务器..."
echo "访问地址:"
echo "  - API文档: http://localhost:8000/docs"
echo "  - ReDoc文档: http://localhost:8000/redoc"
echo "  - 健康检查: http://localhost:8000/health"
echo ""

uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000