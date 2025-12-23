#!/bin/bash
# 运行测试脚本

echo "🧪 运行 FastAPI 单元测试..."
echo "================================"

# 激活虚拟环境
source .venv/bin/activate

# 设置测试环境变量
export DATABASE_URL="sqlite://:memory:"
export REDIS_URL="redis://localhost:6379/0"
export DEBUG="True"

# 运行测试
pytest tests/ -v --tb=short

# 保存退出码
EXIT_CODE=$?

echo "================================"
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ 所有测试通过！"
else
    echo "❌ 部分测试失败，退出码: $EXIT_CODE"
fi

exit $EXIT_CODE
