#!/bin/bash

echo "=== 生产环境部署脚本 ==="

# 设置错误时退出
set -e

# 检查Docker
if ! command -v docker &> /dev/null; then
    echo "错误: 未找到Docker，请先安装Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "错误: 未找到docker-compose，请先安装docker-compose"
    exit 1
fi

# 创建生产环境配置
if [ ! -f ".env.prod" ]; then
    echo "创建生产环境配置文件..."
    cat > .env.prod << EOF
# 生产环境配置
APP_NAME=FastAPI Base
VERSION=1.0.0
DEBUG=False

# 数据库配置 (请修改为实际值)
DATABASE_URL=postgresql://postgres:your_secure_password@db:5432/fastapi_base

# Redis配置
REDIS_URL=redis://redis:6379/0

# Celery配置
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# JWT配置 (请使用强密钥)
SECRET_KEY=your_very_secure_secret_key_here_change_this_in_production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 管理员配置
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_PASSWORD=your_secure_admin_password

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=app.log
EOF
    echo "已创建 .env.prod 文件，请修改其中的配置"
fi

# 构建和启动服务
echo "构建Docker镜像..."
docker-compose build

echo "启动服务..."
docker-compose up -d

echo "等待服务启动..."
sleep 10

# 检查服务状态
echo "检查服务状态..."
docker-compose ps

echo ""
echo "=== 部署完成 ==="
echo ""
echo "服务访问地址:"
echo "  - API服务: http://localhost:8000"
echo "  - API文档: http://localhost:8000/docs"
echo "  - Flower监控: http://localhost:5555"
echo ""
echo "查看日志:"
echo "  docker-compose logs -f web"
echo ""
echo "停止服务:"
echo "  docker-compose down"
echo ""
echo "重启服务:"
echo "  docker-compose restart"