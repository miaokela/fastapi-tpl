#!/bin/bash
# 运行 Celery 集成测试的脚本

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}======================================${NC}"
echo -e "${YELLOW}Celery 集成测试启动脚本${NC}"
echo -e "${YELLOW}======================================${NC}"
echo ""

# 检查 Redis 是否运行
echo -e "${YELLOW}检查 Redis 连接...${NC}"
if ! redis-cli ping > /dev/null 2>&1; then
    echo -e "${RED}错误: Redis 未运行，请先启动 Redis${NC}"
    echo -e "${YELLOW}使用 Docker 启动: docker run -d -p 6379:6379 redis${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Redis 运行正常${NC}"
echo ""

# 检查 Celery worker 是否运行
echo -e "${YELLOW}检查 Celery Worker...${NC}"
CELERY_CHECK=$(celery -A celery_app.celery inspect ping 2>&1)
if echo "$CELERY_CHECK" | grep -q "pong"; then
    echo -e "${GREEN}✓ Celery Worker 运行正常${NC}"
else
    echo -e "${RED}错误: Celery Worker 未运行${NC}"
    echo -e "${YELLOW}请在另一个终端启动 Celery Worker:${NC}"
    echo -e "  celery -A celery_app.celery worker --loglevel=info"
    exit 1
fi
echo ""

# 运行集成测试
echo -e "${YELLOW}运行 Celery 集成测试...${NC}"
echo -e "${YELLOW}======================================${NC}"
pytest tests/test_celery_integration.py -v -m integration

# 检查测试结果
if [ $? -eq 0 ]; then
    echo -e "${GREEN}======================================${NC}"
    echo -e "${GREEN}所有集成测试通过!${NC}"
    echo -e "${GREEN}======================================${NC}"
else
    echo -e "${RED}======================================${NC}"
    echo -e "${RED}部分测试失败${NC}"
    echo -e "${RED}======================================${NC}"
    exit 1
fi
