"""Workspace层注册表管理

提供各种组件的注册表功能，支持加载器、格式化器等的注册和查找。
"""

from typing import Dict, Any, Optional, List, Type
from .interfaces import BaseRegistry, ILoader
from ..simple.interfaces import IFormatter

class LoaderRegistry(BaseRegistry):
    """加载器注册表"""
    
    def __init__(self):
        super().__init__()
        self._loaders: Dict[str, ILoader] = {}
    
    def register_loader(self, name: str, loader: ILoader) -> None:
        """注册加载器"""
        self._loaders[name] = loader
        self.register(name, loader)
    
    def get_loader(self, name: str) -> Optional[ILoader]:
        """获取加载器"""
        return self._loaders.get(name)
    
    def find_loader_for_path(self, path) -> Optional[ILoader]:
        """为路径查找合适的加载器"""
        for loader in self._loaders.values():
            if loader.can_handle(path):
                return loader
        return None
    
    def get_all_loaders(self) -> Dict[str, ILoader]:
        """获取所有加载器"""
        return self._loaders.copy()

class FormatterRegistry(BaseRegistry):
    """格式化器注册表"""
    
    def __init__(self):
        super().__init__()
        self._formatters: Dict[str, IFormatter] = {}
    
    def register_formatter(self, name: str, formatter: IFormatter) -> None:
        """注册格式化器"""
        self._formatters[name] = formatter
        self.register(name, formatter)
    
    def get_formatter(self, name: str) -> Optional[IFormatter]:
        """获取格式化器"""
        return self._formatters.get(name)
    
    def find_formatter_for_content(self, content: str) -> Optional[IFormatter]:
        """为内容查找合适的格式化器"""
        for formatter in self._formatters.values():
            if formatter.can_handle(content):
                return formatter
        return None
    
    def get_all_formatters(self) -> Dict[str, IFormatter]:
        """获取所有格式化器"""
        return self._formatters.copy()

class FunctionRegistry(BaseRegistry):
    """函数注册表"""
    
    def __init__(self):
        super().__init__()
        self._functions: Dict[str, Any] = {}
    
    def register_function(self, name: str, func: Any) -> None:
        """注册函数"""
        self._functions[name] = func
        self.register(name, func)
    
    def get_function(self, name: str) -> Optional[Any]:
        """获取函数"""
        return self._functions.get(name)
    
    def get_all_functions(self) -> Dict[str, Any]:
        """获取所有函数"""
        return self._functions.copy()

class Registry:
    """主注册表 - 组合所有子注册表"""
    
    def __init__(self):
        self.loaders = LoaderRegistry()
        self.formatters = FormatterRegistry()
        self.functions = FunctionRegistry()
    
    def register_loader(self, name: str, loader: ILoader) -> None:
        """注册加载器"""
        self.loaders.register_loader(name, loader)
    
    def register_formatter(self, name: str, formatter: IFormatter) -> None:
        """注册格式化器"""
        self.formatters.register_formatter(name, formatter)
    
    def register_function(self, name: str, func: Any) -> None:
        """注册函数"""
        self.functions.register_function(name, func)
    
    def clear_all(self) -> None:
        """清空所有注册表"""
        self.loaders = LoaderRegistry()
        self.formatters = FormatterRegistry()
        self.functions = FunctionRegistry()

# 全局注册表实例
global_registry = Registry()