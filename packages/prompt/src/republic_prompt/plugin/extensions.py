"""Plugin层扩展系统

提供扩展功能管理，支持动态安装和卸载扩展。
"""

from typing import Dict, Any, List, Optional, Type
from .interfaces import BaseExtension, IExtension

class ExtensionRegistry:
    """扩展注册表"""
    
    def __init__(self):
        self._extensions: Dict[str, IExtension] = {}
        self._extension_types: Dict[str, Type[IExtension]] = {}
    
    def register_extension_type(self, name: str, extension_class: Type[IExtension]) -> None:
        """注册扩展类型"""
        self._extension_types[name] = extension_class
    
    def create_extension(self, type_name: str, name: str, **kwargs) -> Optional[IExtension]:
        """创建扩展实例"""
        if type_name not in self._extension_types:
            return None
        
        extension_class = self._extension_types[type_name]
        # 根据不同的扩展类型创建实例
        if type_name == "function":
            return extension_class(name, kwargs.get("functions"))
        elif type_name == "attribute": 
            return extension_class(name, kwargs.get("attributes"))
        else:
            return extension_class(name)
    
    def register_extension(self, extension: IExtension) -> None:
        """注册扩展实例"""
        self._extensions[extension.name] = extension
    
    def get_extension(self, name: str) -> Optional[IExtension]:
        """获取扩展"""
        return self._extensions.get(name)
    
    def list_extensions(self) -> List[str]:
        """列出所有扩展"""
        return list(self._extensions.keys())
    
    def list_extension_types(self) -> List[str]:
        """列出所有扩展类型"""
        return list(self._extension_types.keys())
    
    def install_extension(self, name: str, target: Any) -> bool:
        """安装扩展"""
        if name not in self._extensions:
            return False
        
        extension = self._extensions[name]
        extension.install(target)
        return True
    
    def uninstall_extension(self, name: str, target: Any) -> bool:
        """卸载扩展"""
        if name not in self._extensions:
            return False
        
        extension = self._extensions[name]
        extension.uninstall(target)
        return True

# 内置扩展类型

class FunctionExtension(BaseExtension):
    """函数扩展 - 为对象添加方法"""
    
    def __init__(self, name: str, functions: Optional[Dict[str, Any]] = None):
        super().__init__(name)
        self.functions = functions or {}
    
    def install(self, target: Any) -> None:
        """安装扩展"""
        for name, func in self.functions.items():
            setattr(target, name, func)
        self._installed = True
    
    def uninstall(self, target: Any) -> None:
        """卸载扩展"""
        for name in self.functions.keys():
            if hasattr(target, name):
                delattr(target, name)
        self._installed = False
    
    def add_function(self, name: str, func: Any) -> None:
        """添加函数"""
        self.functions[name] = func

class AttributeExtension(BaseExtension):
    """属性扩展 - 为对象添加属性"""
    
    def __init__(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        super().__init__(name)
        self.attributes = attributes or {}
    
    def install(self, target: Any) -> None:
        """安装扩展"""
        for name, value in self.attributes.items():
            setattr(target, name, value)
        self._installed = True
    
    def uninstall(self, target: Any) -> None:
        """卸载扩展"""
        for name in self.attributes.keys():
            if hasattr(target, name):
                delattr(target, name)
        self._installed = False
    
    def add_attribute(self, name: str, value: Any) -> None:
        """添加属性"""
        self.attributes[name] = value

class PropertyExtension(BaseExtension):
    """属性扩展 - 为对象添加Python属性（property）"""
    
    def __init__(self, name: str):
        super().__init__(name)
        self.properties: Dict[str, property] = {}
    
    def add_property(self, name: str, getter=None, setter=None, deleter=None, doc=None) -> None:
        """添加属性"""
        self.properties[name] = property(getter, setter, deleter, doc)
    
    def install(self, target: Any) -> None:
        """安装扩展"""
        target_class = target.__class__ if hasattr(target, '__class__') else type(target)
        
        for name, prop in self.properties.items():
            setattr(target_class, name, prop)
        
        self._installed = True
    
    def uninstall(self, target: Any) -> None:
        """卸载扩展"""
        target_class = target.__class__ if hasattr(target, '__class__') else type(target)
        
        for name in self.properties.keys():
            if hasattr(target_class, name):
                delattr(target_class, name)
        
        self._installed = False

class EventExtension(BaseExtension):
    """事件扩展 - 为对象添加事件处理能力"""
    
    def __init__(self, name: str):
        super().__init__(name)
        self.event_handlers: Dict[str, List[Any]] = {}
    
    def install(self, target: Any) -> None:
        """安装扩展"""
        # 添加事件处理方法
        def on(event_name: str, handler):
            if event_name not in self.event_handlers:
                self.event_handlers[event_name] = []
            self.event_handlers[event_name].append(handler)
        
        def emit(event_name: str, *args, **kwargs):
            if event_name in self.event_handlers:
                for handler in self.event_handlers[event_name]:
                    handler(*args, **kwargs)
        
        def off(event_name: str, handler=None):
            if event_name in self.event_handlers:
                if handler:
                    try:
                        self.event_handlers[event_name].remove(handler)
                    except ValueError:
                        pass
                else:
                    self.event_handlers[event_name].clear()
        
        setattr(target, 'on', on)
        setattr(target, 'emit', emit)
        setattr(target, 'off', off)
        
        self._installed = True
    
    def uninstall(self, target: Any) -> None:
        """卸载扩展"""
        for attr_name in ['on', 'emit', 'off']:
            if hasattr(target, attr_name):
                delattr(target, attr_name)
        
        self.event_handlers.clear()
        self._installed = False

# 全局扩展注册表
global_extension_registry = ExtensionRegistry()

# 注册内置扩展类型
global_extension_registry.register_extension_type("function", FunctionExtension)
global_extension_registry.register_extension_type("attribute", AttributeExtension)
global_extension_registry.register_extension_type("property", PropertyExtension)
global_extension_registry.register_extension_type("event", EventExtension)

# 便捷函数
def create_extension(type_name: str, name: str, **kwargs) -> Optional[IExtension]:
    """创建扩展"""
    return global_extension_registry.create_extension(type_name, name, **kwargs)

def register_extension(extension: IExtension) -> None:
    """注册扩展"""
    global_extension_registry.register_extension(extension)

def install_extension(name: str, target: Any) -> bool:
    """安装扩展"""
    return global_extension_registry.install_extension(name, target)

def uninstall_extension(name: str, target: Any) -> bool:
    """卸载扩展"""
    return global_extension_registry.uninstall_extension(name, target)