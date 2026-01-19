"""
调试端点 - 查看 SQL 信息
"""
from fastapi import APIRouter
from app.utils.sql_loader import sql_loader

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/sql")
async def list_sqls():
    """获取所有已加载的 SQL ID 列表"""
    sql_ids = sql_loader.get_all_sql_ids()
    return {
        "count": len(sql_ids),
        "sql_ids": sql_ids
    }


@router.get("/sql/{sql_id:path}")
async def get_sql_detail(sql_id: str):
    """获取指定 SQL 的详细信息"""
    sql_info = sql_loader.get_sql_info(sql_id)
    if not sql_info:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="SQL ID 不存在")
    return sql_info


@router.get("/test/user")
async def test_user_query():
    """测试查询用户 ID 为 1"""
    from app.utils.sql_client import sql_client
    from app.utils.responses import success, error

    try:
        user = await sql_client.select_one(
            sql_id="user.index.fetch_by_id",
            params={"user_id": 1}
        )
        if user:
            return success(data=user, message="查询成功")
        return error(code=4040, message="用户不存在")
    except Exception as e:
        return error(code=5000, message=f"查询失败: {str(e)}")
