"""
FastAPI Base 项目工具模块

这个模块包含项目中常用的工具函数和类
"""

import hashlib
import secrets
import string
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import json


def generate_random_string(length: int = 32) -> str:
    """生成随机字符串"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_hash(data: str, algorithm: str = "sha256") -> str:
    """生成哈希值"""
    if algorithm == "md5":
        return hashlib.md5(data.encode()).hexdigest()
    elif algorithm == "sha1":
        return hashlib.sha1(data.encode()).hexdigest()
    elif algorithm == "sha256":
        return hashlib.sha256(data.encode()).hexdigest()
    elif algorithm == "sha512":
        return hashlib.sha512(data.encode()).hexdigest()
    else:
        raise ValueError(f"不支持的哈希算法: {algorithm}")


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """格式化日期时间"""
    return dt.strftime(format_str)


def parse_datetime(date_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """解析日期时间字符串"""
    return datetime.strptime(date_str, format_str)


def is_valid_email(email: str) -> bool:
    """简单的邮箱验证"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def sanitize_filename(filename: str) -> str:
    """清理文件名，移除不安全字符"""
    import re
    # 移除或替换不安全字符
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # 移除连续的点号
    filename = re.sub(r'\.{2,}', '.', filename)
    # 移除开头和结尾的空格和点号
    filename = filename.strip(' .')
    return filename


def get_file_size_str(size_bytes: int) -> str:
    """将字节大小转换为人类可读的格式"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f}{size_names[i]}"


def deep_merge_dict(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """深度合并两个字典"""
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dict(result[key], value)
        else:
            result[key] = value
    
    return result


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """将列表分块"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def remove_duplicates(lst: List[Any], key: Optional[str] = None) -> List[Any]:
    """移除列表中的重复项"""
    if key is None:
        # 简单列表去重
        return list(dict.fromkeys(lst))
    else:
        # 根据对象的某个属性去重
        seen = set()
        result = []
        for item in lst:
            if isinstance(item, dict):
                value = item.get(key)
            else:
                value = getattr(item, key, None)
            
            if value not in seen:
                seen.add(value)
                result.append(item)
        
        return result


class Timer:
    """简单的计时器类"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
    
    def start(self):
        """开始计时"""
        self.start_time = datetime.now()
        return self
    
    def stop(self):
        """停止计时"""
        self.end_time = datetime.now()
        return self
    
    def elapsed(self) -> Optional[timedelta]:
        """获取经过的时间"""
        if self.start_time is None:
            return None
        
        end = self.end_time or datetime.now()
        return end - self.start_time
    
    def elapsed_seconds(self) -> Optional[float]:
        """获取经过的秒数"""
        elapsed = self.elapsed()
        return elapsed.total_seconds() if elapsed else None
    
    def __enter__(self):
        """上下文管理器入口"""
        return self.start()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.stop()


class JSONEncoder(json.JSONEncoder):
    """自定义JSON编码器，支持日期时间等类型"""
    
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, timedelta):
            return obj.total_seconds()
        elif hasattr(obj, 'dict'):
            return obj.dict()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        
        return super().default(obj)


def safe_json_dumps(obj: Any, **kwargs) -> str:
    """安全的JSON序列化"""
    return json.dumps(obj, cls=JSONEncoder, ensure_ascii=False, **kwargs)


def safe_json_loads(s: str, default: Any = None) -> Any:
    """安全的JSON反序列化"""
    try:
        return json.loads(s)
    except (json.JSONDecodeError, TypeError):
        return default


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
    """验证必需字段"""
    missing_fields = []
    
    for field in required_fields:
        if field not in data or data[field] is None or data[field] == "":
            missing_fields.append(field)
    
    return missing_fields


def mask_sensitive_data(data: str, visible_chars: int = 4, mask_char: str = "*") -> str:
    """掩码敏感数据"""
    if len(data) <= visible_chars:
        return mask_char * len(data)
    
    return data[:visible_chars] + mask_char * (len(data) - visible_chars)


def paginate_query_result(data: List[Any], page: int = 1, page_size: int = 20) -> Dict[str, Any]:
    """分页查询结果"""
    total = len(data)
    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    
    items = data[start_index:end_index]
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "has_next": end_index < total,
        "has_prev": page > 1
    }