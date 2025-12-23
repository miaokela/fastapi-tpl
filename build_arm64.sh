#!/bin/bash
# ARM64 打包脚本
# 使用 Docker 构建可在 ARM64 Debian 上运行的可执行文件

set -e

echo "🔨 Building ARM64 Docker image..."
docker buildx build --platform linux/arm64 -f Dockerfile.build -t fastapi-base-builder:arm64 .

echo "📦 Running PyInstaller in container..."
mkdir -p dist
docker run --platform linux/arm64 --rm -v "$(pwd)/dist:/output" fastapi-base-builder:arm64

echo "✅ Build complete!"
echo "📁 Output: dist/app"
ls -lh dist/app

echo ""
echo "📋 Usage on ARM64 Debian:"
echo "  ./app server              # 启动 API 服务"
echo "  ./app worker              # 启动 Celery Worker"  
echo "  ./app beat                # 启动 Celery Beat"
echo "  ./app init-db             # 初始化数据库"
echo "  ./app server --port 9000  # 指定端口"
