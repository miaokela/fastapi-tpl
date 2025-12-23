"""
测试配置文件
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

# 设置测试环境变量
os.environ["DATABASE_URL"] = "sqlite://:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["DEBUG"] = "True"
