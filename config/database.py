from config.settings import settings

# 不使用aerich
# Tortoise ORM 数据库配置
DATABASE_CONFIG = {
    "connections": {
        "default": settings.DATABASE_URL,
    },
    "apps": {
        "models": {
            "models": ["app.models"],
            "default_connection": "default",
        },
    },
    "use_tz": False,
    "timezone": "UTC",
}
