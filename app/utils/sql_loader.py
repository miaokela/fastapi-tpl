"""
SQL 加载器 - 负责从 YAML 文件加载 SQL 语句
"""
import os
import yaml
import jinja2
from typing import Dict, List, Optional
from config.settings import settings
from config.logging import get_logger

logger = get_logger(__name__)


class SqlLoader:
    """SQL 加载器（单例模式）"""

    # 类属性（从 settings 配置）
    SQL_FILE_PATH: str = "app/sql"
    page_param: str = "page"
    page_size_param: str = "page_size"

    # 全局缓存
    sql_cache: Dict[str, str] = {}
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化，预加载所有 SQL"""
        if not self.sql_cache:
            self.preload_all_sqls()

    @classmethod
    def preload_all_sqls(cls) -> int:
        """预加载所有 SQL 到内存，返回加载的 SQL 数量"""
        count = 0
        sql_path = os.path.abspath(cls.SQL_FILE_PATH)

        if not os.path.exists(sql_path):
            logger.warning(f"SQL 目录不存在: {sql_path}")
            return 0

        for root, dirs, files in os.walk(sql_path):
            for file in files:
                if file.endswith('.yml') or file.endswith('.yaml'):
                    file_path = os.path.join(root, file)
                    sql_group = cls._load_yaml_file(file_path)

                    if not sql_group:
                        continue

                    # 生成 SQL ID 前缀
                    relative_path = os.path.relpath(file_path, sql_path)
                    prefix = relative_path.replace(os.sep, '.').replace('.yml', '').replace('.yaml', '')

                    # 缓存每个 SQL 语句
                    for key, sql in sql_group.items():
                        sql_id = f"{prefix}.{key}"
                        cls.sql_cache[sql_id] = sql
                        count += 1

        logger.info(f"SQL 加载完成，共加载 {count} 条 SQL")
        return count

    @staticmethod
    def _load_yaml_file(file_path: str) -> Dict:
        """加载 YAML 文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"加载 YAML 文件失败 {file_path}: {e}")
            return {}

    def get_sql(self, sql_id: str) -> str:
        """获取原始 SQL"""
        if sql_id not in self.sql_cache:
            raise ValueError(f"SQL ID 不存在: {sql_id}")
        return self.sql_cache[sql_id]

    def render_sql(self, sql_id: str, params: Dict = None, options: Dict = None) -> str:
        """渲染 SQL（处理分页和 Jinja2 模板）"""
        # 获取原始 SQL
        sql = self.get_sql(sql_id)

        # 合并参数
        context = {**(params or {}), **(options or {})}

        # 处理分页参数
        page = options.get(self.page_param) if options else None
        page_size = options.get(self.page_size_param) if options else None

        if page is not None or page_size is not None:
            page = page or 1
            page_size = page_size or 10
            offset = (page - 1) * page_size

            # MySQL 分页语法
            pagination_sql = """
            {% if limit is not none and offset is not none %}
                LIMIT {{ offset }}, {{ limit }}
            {% elif limit is not none %}
                LIMIT {{ limit }}
            {% endif %}
            """
            sql += pagination_sql
            context['limit'] = page_size
            context['offset'] = offset

        # Jinja2 渲染
        if context:
            try:
                sql = jinja2.Template(sql).render(**context)
            except Exception as e:
                logger.error(f"SQL 渲染失败 {sql_id}: {e}")
                raise

        return sql

    @classmethod
    def get_all_sql_ids(cls) -> List[str]:
        """获取所有已加载的 SQL ID"""
        return list(cls.sql_cache.keys())

    @classmethod
    def get_sql_info(cls, sql_id: str) -> Optional[Dict]:
        """获取 SQL 的详细信息"""
        if sql_id in cls.sql_cache:
            return {
                "sql_id": sql_id,
                "sql": cls.sql_cache[sql_id]
            }
        return None


# 全局实例
sql_loader = SqlLoader()
