#!/usr/bin/env python3
"""
FastAPI Base CLI 入口
用于 PyInstaller 打包，支持启动不同服务
"""
import sys
import os

# 确保当前目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def print_usage():
    """打印使用说明"""
    print("""
FastAPI Base - 命令行工具

用法: ./app <command> [options]

命令:
  server          启动 FastAPI Web 服务
  worker          启动 Celery Worker
  beat            启动 Celery Beat 定时任务调度
  init-db         初始化数据库（创建表结构）
  
选项:
  --host HOST     Web 服务监听地址 (默认: 0.0.0.0)
  --port PORT     Web 服务端口 (默认: 8000)
  --workers NUM   Worker 进程数 (默认: 4)
  --reload        启用热重载 (仅开发环境，使用 uvicorn)
  
示例:
  ./app server                    # 启动 Web 服务 (gunicorn + uvicorn)
  ./app server --port 8080        # 指定端口启动
  ./app server --workers 8        # 指定 worker 数量
  ./app worker                    # 启动 Celery Worker
  ./app beat                      # 启动定时任务调度
  ./app init-db                   # 初始化数据库
""")


def run_server(host: str = "0.0.0.0", port: int = 8000, workers: int = 4, reload: bool = False):
    """启动 FastAPI 服务 (gunicorn + uvicorn workers)"""
    from config.logging import setup_logging
    
    setup_logging()
    print(f"启动 FastAPI 服务: http://{host}:{port}")
    print(f"API 文档: http://{host}:{port}/docs")
    print(f"Workers: {workers}")
    
    if reload:
        # 开发模式使用 uvicorn 直接启动
        import uvicorn
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
    else:
        # 生产模式使用 gunicorn + uvicorn workers
        from gunicorn.app.base import BaseApplication
        from main import app as application
        
        class StandaloneApplication(BaseApplication):
            def __init__(self, app, options=None):
                self.options = options or {}
                self.application = app
                super().__init__()
            
            def load_config(self):
                for key, value in self.options.items():
                    if key in self.cfg.settings and value is not None:
                        self.cfg.set(key.lower(), value)
            
            def load(self):
                return self.application
        
        options = {
            "bind": f"{host}:{port}",
            "workers": workers,
            "worker_class": "uvicorn.workers.UvicornWorker",
            "accesslog": "-",
            "errorlog": "-",
            "loglevel": "info",
        }
        
        StandaloneApplication(application, options).run()


def run_worker():
    """启动 Celery Worker"""
    from celery_app.celery import celery_app
    from config.logging import setup_logging
    
    setup_logging()
    print("启动 Celery Worker...")
    
    celery_app.worker_main([
        "worker",
        "--loglevel=info",
        "--concurrency=4"
    ])


def run_beat():
    """启动 Celery Beat"""
    from celery_app.celery import celery_app
    from config.logging import setup_logging
    
    setup_logging()
    print("启动 Celery Beat 定时任务调度...")
    
    celery_app.worker_main([
        "beat",
        "-S", "celery_app.scheduler:DatabaseScheduler",
        "--loglevel=info"
    ])


def init_database():
    """初始化数据库"""
    import asyncio
    from tortoise import Tortoise
    from config.database import DATABASE_CONFIG
    from config.logging import setup_logging, get_logger
    
    setup_logging()
    logger = get_logger(__name__)
    
    async def _init():
        logger.info("初始化数据库...")
        await Tortoise.init(config=DATABASE_CONFIG)
        await Tortoise.generate_schemas()
        logger.info("数据库表结构创建完成")
        await Tortoise.close_connections()
    
    asyncio.run(_init())
    print("数据库初始化完成!")


def main():
    """主入口"""
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    command = sys.argv[1]
    
    # 解析参数
    host = "0.0.0.0"
    port = 8000
    workers = 4
    reload = False
    
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--host" and i + 1 < len(sys.argv):
            host = sys.argv[i + 1]
            i += 2
        elif arg == "--port" and i + 1 < len(sys.argv):
            port = int(sys.argv[i + 1])
            i += 2
        elif arg == "--workers" and i + 1 < len(sys.argv):
            workers = int(sys.argv[i + 1])
            i += 2
        elif arg == "--reload":
            reload = True
            i += 1
        else:
            i += 1
    
    # 执行命令
    if command == "server":
        run_server(host=host, port=port, workers=workers, reload=reload)
    elif command == "worker":
        run_worker()
    elif command == "beat":
        run_beat()
    elif command == "init-db":
        init_database()
    elif command in ["-h", "--help", "help"]:
        print_usage()
    else:
        print(f"未知命令: {command}")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
