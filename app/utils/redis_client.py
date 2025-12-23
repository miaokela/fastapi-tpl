import json
import asyncio
from typing import Any, Optional, Dict, List
import redis.asyncio as redis
from config.settings import settings


class RedisClient:
    """Redis客户端工具类"""
    
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        
    async def connect(self):
        """连接Redis"""
        try:
            self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
            await self.redis.ping()
            print("Redis连接成功")
        except Exception as e:
            print(f"Redis连接失败: {e}")
            raise
    
    async def disconnect(self):
        """断开Redis连接"""
        if self.redis:
            await self.redis.close()
            print("Redis连接已断开")
    
    async def set_value(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """设置键值对"""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            
            if expire:
                return await self.redis.setex(key, expire, value)
            else:
                return await self.redis.set(key, value)
        except Exception as e:
            print(f"设置Redis键值失败: {e}")
            return False
    
    async def get_value(self, key: str) -> Optional[Any]:
        """获取值"""
        try:
            value = await self.redis.get(key)
            if value is None:
                return None
                
            # 尝试解析JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except Exception as e:
            print(f"获取Redis值失败: {e}")
            return None
    
    async def delete_key(self, key: str) -> bool:
        """删除键"""
        try:
            return bool(await self.redis.delete(key))
        except Exception as e:
            print(f"删除Redis键失败: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        try:
            return bool(await self.redis.exists(key))
        except Exception as e:
            print(f"检查Redis键存在性失败: {e}")
            return False
    
    async def expire_key(self, key: str, seconds: int) -> bool:
        """设置键的过期时间"""
        try:
            return bool(await self.redis.expire(key, seconds))
        except Exception as e:
            print(f"设置Redis键过期时间失败: {e}")
            return False
    
    async def get_ttl(self, key: str) -> int:
        """获取键的剩余过期时间"""
        try:
            return await self.redis.ttl(key)
        except Exception as e:
            print(f"获取Redis键TTL失败: {e}")
            return -1
    
    # 列表操作
    async def lpush(self, key: str, *values) -> int:
        """从列表左侧推入元素"""
        try:
            return await self.redis.lpush(key, *values)
        except Exception as e:
            print(f"Redis LPUSH操作失败: {e}")
            return 0
    
    async def rpush(self, key: str, *values) -> int:
        """从列表右侧推入元素"""
        try:
            return await self.redis.rpush(key, *values)
        except Exception as e:
            print(f"Redis RPUSH操作失败: {e}")
            return 0
    
    async def lpop(self, key: str) -> Optional[str]:
        """从列表左侧弹出元素"""
        try:
            return await self.redis.lpop(key)
        except Exception as e:
            print(f"Redis LPOP操作失败: {e}")
            return None
    
    async def rpop(self, key: str) -> Optional[str]:
        """从列表右侧弹出元素"""
        try:
            return await self.redis.rpop(key)
        except Exception as e:
            print(f"Redis RPOP操作失败: {e}")
            return None
    
    async def lrange(self, key: str, start: int = 0, end: int = -1) -> List[str]:
        """获取列表范围内的元素"""
        try:
            return await self.redis.lrange(key, start, end)
        except Exception as e:
            print(f"Redis LRANGE操作失败: {e}")
            return []
    
    # 集合操作
    async def sadd(self, key: str, *values) -> int:
        """向集合添加元素"""
        try:
            return await self.redis.sadd(key, *values)
        except Exception as e:
            print(f"Redis SADD操作失败: {e}")
            return 0
    
    async def srem(self, key: str, *values) -> int:
        """从集合移除元素"""
        try:
            return await self.redis.srem(key, *values)
        except Exception as e:
            print(f"Redis SREM操作失败: {e}")
            return 0
    
    async def smembers(self, key: str) -> set:
        """获取集合所有成员"""
        try:
            return await self.redis.smembers(key)
        except Exception as e:
            print(f"Redis SMEMBERS操作失败: {e}")
            return set()
    
    async def sismember(self, key: str, value: str) -> bool:
        """检查元素是否在集合中"""
        try:
            return bool(await self.redis.sismember(key, value))
        except Exception as e:
            print(f"Redis SISMEMBER操作失败: {e}")
            return False
    
    # 哈希操作
    async def hset(self, key: str, field: str, value: Any) -> int:
        """设置哈希字段值"""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            return await self.redis.hset(key, field, value)
        except Exception as e:
            print(f"Redis HSET操作失败: {e}")
            return 0
    
    async def hget(self, key: str, field: str) -> Optional[Any]:
        """获取哈希字段值"""
        try:
            value = await self.redis.hget(key, field)
            if value is None:
                return None
            
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except Exception as e:
            print(f"Redis HGET操作失败: {e}")
            return None
    
    async def hdel(self, key: str, *fields) -> int:
        """删除哈希字段"""
        try:
            return await self.redis.hdel(key, *fields)
        except Exception as e:
            print(f"Redis HDEL操作失败: {e}")
            return 0
    
    async def hgetall(self, key: str) -> Dict[str, Any]:
        """获取哈希所有字段和值"""
        try:
            result = await self.redis.hgetall(key)
            # 尝试解析JSON值
            parsed_result = {}
            for field, value in result.items():
                try:
                    parsed_result[field] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    parsed_result[field] = value
            return parsed_result
        except Exception as e:
            print(f"Redis HGETALL操作失败: {e}")
            return {}
    
    # 缓存装饰器相关方法
    async def cache_get_or_set(self, key: str, func, *args, expire: int = 3600, **kwargs) -> Any:
        """获取缓存或设置缓存"""
        try:
            # 先尝试从缓存获取
            cached_value = await self.get_value(key)
            if cached_value is not None:
                return cached_value
            
            # 如果缓存不存在，执行函数获取值
            if asyncio.iscoroutinefunction(func):
                value = await func(*args, **kwargs)
            else:
                value = func(*args, **kwargs)
            
            # 设置缓存
            await self.set_value(key, value, expire)
            return value
            
        except Exception as e:
            print(f"缓存操作失败: {e}")
            # 如果缓存操作失败，直接返回函数结果
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)


# 全局Redis客户端实例
redis_client = RedisClient()