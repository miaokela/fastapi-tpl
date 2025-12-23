#!/bin/bash

echo "=== 启动Celery服务 ==="

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "虚拟环境不存在，请先运行setup.sh"
    exit 1
fi

# 激活虚拟环境
source .venv/bin/activate

# 启动选项
case "$1" in
    "worker")
        echo "启动Celery Worker..."
        celery -A celery_app.celery worker --loglevel=info
        ;;
    "beat")
        echo "启动Celery Beat (数据库定时任务调度器)..."
        celery -A celery_app.celery beat \
            -S celery_app.scheduler:DatabaseScheduler \
            --loglevel=info
        ;;
    "flower")
        echo "启动Flower监控..."
        echo "访问地址: http://localhost:5555"
        celery -A celery_app.celery flower --port=5555
        ;;
    "all")
        echo "启动所有Celery服务..."
        # 使用tmux或screen在后台启动多个服务
        if command -v tmux &> /dev/null; then
            tmux new-session -d -s celery-worker "celery -A celery_app.celery worker --loglevel=info"
            tmux new-session -d -s celery-beat "celery -A celery_app.celery beat -S celery_app.scheduler:DatabaseScheduler --loglevel=info"
            tmux new-session -d -s celery-flower "celery -A celery_app.celery flower --port=5555"
            echo "Celery服务已在tmux会话中启动:"
            echo "  - Worker: tmux attach -t celery-worker"
            echo "  - Beat: tmux attach -t celery-beat"
            echo "  - Flower: tmux attach -t celery-flower"
        else
            echo "请安装tmux以同时启动多个服务，或分别启动:"
            echo "$0 worker    # 启动Worker"
            echo "$0 beat      # 启动定时任务"
            echo "$0 flower    # 启动监控"
        fi
        ;;
    *)
        echo "用法: $0 {worker|beat|flower|all}"
        echo ""
        echo "选项:"
        echo "  worker  - 启动Celery Worker (处理异步任务)"
        echo "  beat    - 启动Celery Beat (定时任务调度器)"
        echo "  flower  - 启动Flower (任务监控界面)"
        echo "  all     - 启动所有服务 (需要tmux)"
        exit 1
        ;;
esac