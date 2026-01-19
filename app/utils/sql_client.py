"""
SQL 客户端 - 负责执行 SQL 查询，支持条件操作符
"""
import copy
from typing import Any, Dict, List, Optional, Tuple
from tortoise import Tortoise
from config.settings import settings
from config.logging import get_logger
from .sql_loader import SqlLoader

logger = get_logger(__name__)


class SQLClient:
    """SQL 客户端（异步版本）"""

    def __init__(self):
        """初始化，创建 SQL 加载器实例"""
        self.loader = SqlLoader()

    # ========== 条件操作符处理 ==========

    @staticmethod
    def handle_ops(key: str, val: Any, opt_type: str = "where") -> str:
        """
        处理条件操作符
        支持: __gt, __gte, __lt, __lte, __like, __in, __isnull, __between

        Args:
            key: 字段名（可能包含操作符后缀）
            val: 字段值
            opt_type: 操作类型 ("where" 或 "exclude")

        Returns:
            SQL 条件片段
        """
        filter_str = '_where_' if opt_type == 'where' else '_exclude_'

        operator_mapping = {
            '__gt': ('>', False),
            '__gte': ('>=', False),
            '__lt': ('<', False),
            '__lte': ('<=', False),
            '__like': ('LIKE', False),
            '__in': ('IN', True),  # 需要特殊处理列表值
            '__isnull': ('IS NULL', False),
            '__between': ('BETWEEN', True),  # 需要两个值
        }

        for op, (sql_op, is_special) in operator_mapping.items():
            if key.endswith(op):
                field = key.replace(op, '')

                if op == '__between':
                    return f"{field} {sql_op} :{filter_str}between_1_{key} AND :{filter_str}between_2_{key}"
                elif op == '__isnull':
                    return f"{field} {sql_op}"
                elif op == '__in':
                    return f"{field} {sql_op} :{filter_str}{key}"
                else:
                    return f"{field} {sql_op} :{filter_str}{key}"

        # 默认等值查询
        return f"{key} = :{filter_str}{key}"

    @staticmethod
    def build_where_clause(where: Dict, opt_type: str = "where") -> Tuple[str, Dict]:
        """
        构建 WHERE 子句

        Args:
            where: 条件字典
            opt_type: "where" 或 "exclude"

        Returns:
            (SQL 子句, 参数字典)
        """
        if not where:
            return "", {}

        filter_str = '_where_' if opt_type == 'where' else '_exclude_'
        conditions = []
        params = {}

        for key, val in where.items():
            # 检查是否有操作符
            if any(key.endswith(op) for op in ['__gt', '__gte', '__lt', '__lte', '__like', '__in', '__isnull', '__between']):
                cond = SQLClient.handle_ops(key, val, opt_type)
                conditions.append(cond)

                # 处理特殊参数
                if key.endswith('__between'):
                    if isinstance(val, (list, tuple)) and len(val) == 2:
                        params[f"{filter_str}between_1_{key}"] = val[0]
                        params[f"{filter_str}between_2_{key}"] = val[1]
                elif key.endswith('__isnull'):
                    # IS NULL 不需要参数
                    pass
                else:
                    params[f"{filter_str}{key}"] = val
            else:
                # 默认等值查询
                conditions.append(f"{key} = :{filter_str}{key}")
                params[f"{filter_str}{key}"] = val

        where_clause = ' AND '.join(conditions)
        return where_clause, params

    # ========== SQL 执行方法 ==========

    async def execute_sql_query(
        self,
        sql: str,
        params: Dict = None
    ) -> List[Dict[str, Any]]:
        """执行原生 SQL 查询"""
        try:
            conn = Tortoise.get_connection("default")

            if settings.SQL_PRINT_SQL:
                logger.info(f"执行 SQL: {sql}, 参数: {params}")

            # 使用 execute_query_dict 返回字典列表
            if params:
                result = await conn.execute_query_dict(sql, params)
            else:
                result = await conn.execute_query_dict(sql)

            return result

        except Exception as e:
            logger.error(f"SQL 执行失败: {sql}, 参数: {params}, 错误: {e}")
            raise

    async def execute_sql_script(
        self,
        sql: str,
        params: Dict = None
    ) -> Any:
        """执行 SQL 脚本（INSERT/UPDATE/DELETE）"""
        try:
            conn = Tortoise.get_connection("default")

            if settings.SQL_PRINT_SQL:
                logger.info(f"执行 SQL: {sql}, 参数: {params}")

            if params:
                result = await conn.execute_script(sql, params)
            else:
                result = await conn.execute_script(sql)

            return result

        except Exception as e:
            logger.error(f"SQL 执行失败: {sql}, 参数: {params}, 错误: {e}")
            raise

    # ========== CRUD 方法 ==========

    async def select_one(
        self,
        sql_id: str,
        params: Dict = None,
        options: Dict = None
    ) -> Optional[Dict[str, Any]]:
        """查询单条记录"""
        # 渲染 SQL（不带分页）
        sql = self.loader.render_sql(sql_id, params, options)

        # 移除分页参数用于单条查询
        clean_options = {}
        if options:
            clean_options = {
                k: v for k, v in options.items()
                if k not in [self.loader.page_param, self.loader.page_size_param]
            }

        result = await self.execute_sql_query(sql, params)
        return result[0] if result else None

    async def select_all(
        self,
        sql_id: str,
        params: Dict = None,
        options: Dict = None
    ) -> List[Dict[str, Any]]:
        """查询多条记录（支持分页）"""
        # 渲染 SQL（带分页）
        sql = self.loader.render_sql(sql_id, params, options)
        return await self.execute_sql_query(sql, params)

    async def execute_create(
        self,
        table_name: str,
        data: Dict
    ) -> Optional[int]:
        """插入数据，返回 ID"""
        self._check_sql_injection(table_name)

        columns = ', '.join(f'`{k}`' for k in data.keys())
        placeholders = ', '.join(f':{k}' for k in data.keys())

        sql = f"INSERT INTO `{table_name}` ({columns}) VALUES ({placeholders})"

        result = await self.execute_sql_script(sql, data)

        # MySQL 获取插入的 ID
        if hasattr(result, 'lastrowid'):
            return result.lastrowid
        return None

    async def execute_update(
        self,
        table_name: str,
        data: Dict,
        where: Dict = None,
        exclude: Dict = None
    ) -> Optional[int]:
        """
        更新数据，返回影响行数

        Args:
            table_name: 表名
            data: 要更新的数据
            where: WHERE 条件（支持操作符）
            exclude: EXCLUDE 条件（NOT 条件，支持操作符）
        """
        self._check_sql_injection(table_name)

        set_clause = ', '.join(f'`{k}` = :set_{k}' for k in data.keys())
        sql = f"UPDATE `{table_name}` SET {set_clause}"

        # 合并参数，避免字段名冲突
        params = {f'set_{k}': v for k, v in data.items()}

        # 处理 WHERE 条件
        if where:
            where_clause, where_params = self.build_where_clause(where, "where")
            sql += f" WHERE {where_clause}"
            params.update(where_params)

        # 处理 EXCLUDE 条件
        if exclude:
            exclude_clause, exclude_params = self.build_where_clause(exclude, "exclude")
            if where:
                sql += f" AND {exclude_clause}"
            else:
                sql += f" WHERE {exclude_clause}"
            params.update(exclude_params)

        result = await self.execute_sql_script(sql, params)

        if hasattr(result, 'rowcount'):
            return result.rowcount
        return None

    async def execute_delete(
        self,
        table_name: str,
        where: Dict = None,
        exclude: Dict = None,
        logic: bool = False
    ) -> Optional[int]:
        """
        删除数据，返回影响行数

        Args:
            table_name: 表名
            where: WHERE 条件（支持操作符）
            exclude: EXCLUDE 条件（支持操作符）
            logic: 是否使用逻辑删除
        """
        self._check_sql_injection(table_name)

        if logic:
            # 逻辑删除：更新 delete_flag 字段
            sql = f"UPDATE `{table_name}` SET `delete_flag` = 1"
        else:
            sql = f"DELETE FROM `{table_name}`"

        params = {}

        # 处理 WHERE 条件
        if where:
            where_clause, where_params = self.build_where_clause(where, "where")
            sql += f" WHERE {where_clause}"
            params.update(where_params)

        # 处理 EXCLUDE 条件
        if exclude:
            exclude_clause, exclude_params = self.build_where_clause(exclude, "exclude")
            if where:
                sql += f" AND {exclude_clause}"
            else:
                sql += f" WHERE {exclude_clause}"
            params.update(exclude_params)

        result = await self.execute_sql_script(sql, params)

        if hasattr(result, 'rowcount'):
            return result.rowcount
        return None

    # ========== 工具方法 ==========

    @staticmethod
    def _check_sql_injection(input_string: str):
        """SQL 注入检测"""
        dangerous_keywords = [
            'DROP', 'DELETE', 'UPDATE', 'INSERT',
            '--', '/*', '*/', 'xp_', 'sp_'
        ]

        upper_str = input_string.upper()
        for keyword in dangerous_keywords:
            if keyword in upper_str:
                raise ValueError(f"检测到潜在的 SQL 注入攻击: {keyword}")

    @staticmethod
    def get_params_without_paginated(params: Dict) -> Dict:
        """移除分页参数"""
        if not params:
            return {}
        return {
            k: v for k, v in params.items()
            if k not in ['page', 'page_size']
        }


# 全局实例
sql_client = SQLClient()
