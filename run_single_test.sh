#!/bin/bash
# 运行单个测试的辅助脚本
# 用法: ./run_single_test.sh <测试路径>
# 示例: ./run_single_test.sh tests/test_users.py::TestUserAPI::test_get_users_list

if [ -z "$1" ]; then
    echo "❌ 错误: 请提供测试路径"
    echo ""
    echo "用法:"
    echo "  ./run_single_test.sh <测试路径>"
    echo ""
    echo "示例:"
    echo "  # 运行单个测试方法"
    echo "  ./run_single_test.sh tests/test_users.py::TestUserAPI::test_get_users_list"
    echo ""
    echo "  # 运行整个测试类"
    echo "  ./run_single_test.sh tests/test_users.py::TestUserAPI"
    echo ""
    echo "  # 运行整个测试文件"
    echo "  ./run_single_test.sh tests/test_users.py"
    echo ""
    echo "  # 使用关键字匹配"
    echo "  ./run_single_test.sh tests/test_users.py -k get_users"
    exit 1
fi

echo "🧪 运行测试: $@"
echo "================================"

# 激活虚拟环境
source .venv/bin/activate

# 设置测试环境变量
export DATABASE_URL="sqlite://:memory:"
export REDIS_URL="redis://localhost:6379/0"
export DEBUG="True"

# 运行测试
pytest "$@" -vv -s --tb=short

EXIT_CODE=$?

echo "================================"
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ 测试通过！"
else
    echo "❌ 测试失败，退出码: $EXIT_CODE"
fi

exit $EXIT_CODE
