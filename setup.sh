#!/bin/bash

# 设置错误时退出
set -e

echo "=== FastAPI项目启动脚本 ==="

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python3"
    exit 1
fi

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv .venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source .venv/bin/activate

# 升级pip
echo "升级pip..."
pip install --upgrade pip

# 安装依赖
echo "安装项目依赖..."
pip install -r requirements.txt

# 检查.env文件
if [ ! -f ".env" ]; then
    echo "创建.env配置文件..."
    cp .env.example .env
    echo "请编辑.env文件配置您的环境变量"
fi

# 创建必要的目录
echo "创建必要目录..."
mkdir -p uploads logs

# 数据库初始化
echo "初始化数据库..."
if [ -f "init_schema.sql" ]; then
    sqlite3 default_db.sqlite3 < init_schema.sql
    echo "数据库初始化完成"
else
    echo "警告: init_schema.sql 文件不存在，跳过数据库初始化"
fi

echo "=== 项目配置完成 ==="
echo ""
echo "启动开发服务器:"
echo "  python main.py"
echo ""
echo "或使用uvicorn:"
echo "  uvicorn main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "启动Celery Worker:"
echo "  celery -A celery_app.celery worker --loglevel=info"
echo ""
echo "启动Celery Beat:"
echo "  celery -A celery_app.celery beat --loglevel=info"
echo ""
echo "启动Flower监控:"
echo "  celery -A celery_app.celery flower --port=5555"
echo ""
echo "Docker启动:"
echo "  docker-compose up -d"