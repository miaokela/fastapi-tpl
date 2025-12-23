"""
模型自动扫描
运行时自动扫描 models 文件夹下所有模块中的 Tortoise Model
"""
import importlib
import pkgutil
from pathlib import Path
from tortoise.models import Model


def _auto_discover_models():
    """自动发现并导入所有模型"""
    models = []
    package_dir = Path(__file__).parent
    
    # 遍历当前包下的所有模块
    for module_info in pkgutil.iter_modules([str(package_dir)]):
        if module_info.name.startswith('_'):
            continue
        
        # 动态导入模块
        module = importlib.import_module(f".{module_info.name}", package=__name__)
        
        # 查找模块中所有的 Tortoise Model
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) 
                and issubclass(attr, Model) 
                and attr is not Model
                and hasattr(attr, '_meta')):
                models.append(attr)
                # 将模型导出到当前命名空间
                globals()[attr_name] = attr
    
    return models


# 自动扫描并导入所有模型
_discovered_models = _auto_discover_models()

# 动态生成 __all__
__all__ = [model.__name__ for model in _discovered_models]
