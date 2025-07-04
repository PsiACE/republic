"""Workspace层接口定义

定义Workspace层的所有接口，确保层间解耦和扩展性。
"""

from abc import ABC, abstractmethod
from typing import Protocol, Dict, Any, List, Optional, Union, runtime_checkable
from pathlib import Path

# 前向声明
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..simple.interfaces import IRenderer
    from ..simple.models import RenderResult, TemplateModel

# 直接导入配置，因为在类定义中需要使用
from .config import WorkspaceConfig

@runtime_checkable
class IWorkspace(Protocol):
    """工作空间接口"""
    
    def render(self, template_name: str, **context) -> "RenderResult":
        """渲染模板"""
        ...
    
    def get_template(self, name: str) -> Optional["TemplateModel"]:
        """获取模板"""
        ...
    
    def list_templates(self) -> List[str]:
        """列出所有模板"""
        ...
    
    def list_snippets(self) -> List[str]:
        """列出所有片段"""
        ...
    
    def add_function(self, name: str, func: Any) -> None:
        """添加自定义函数"""
        ...
    
    @property
    def path(self) -> Path:
        """工作空间路径"""
        ...

@runtime_checkable
class ILoader(Protocol):
    """加载器接口"""
    
    def can_handle(self, path: Path) -> bool:
        """检查是否可以处理该路径"""
        ...
    
    def load(self, path: Path) -> Any:
        """加载内容"""
        ...

@runtime_checkable
class IRegistry(Protocol):
    """注册表接口"""
    
    def register(self, name: str, item: Any) -> None:
        """注册项目"""
        ...
    
    def get(self, name: str) -> Optional[Any]:
        """获取项目"""
        ...
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有项目"""
        ...
    
    def unregister(self, name: str) -> bool:
        """取消注册"""
        ...

class BaseWorkspace(ABC):
    """工作空间基类"""
    
    def __init__(self, path: Path, config: WorkspaceConfig):
        self.path = path
        self.config = config
    
    @abstractmethod
    def render(self, template_name: str, **context) -> "RenderResult":
        """渲染模板"""
        pass
    
    @abstractmethod
    def get_template(self, name: str) -> Optional["TemplateModel"]:
        """获取模板"""
        pass
    
    @abstractmethod
    def list_templates(self) -> List[str]:
        """列出所有模板"""
        pass
    
    @abstractmethod
    def list_snippets(self) -> List[str]:
        """列出所有片段"""
        pass
    
    def add_function(self, name: str, func: Any) -> None:
        """添加自定义函数 - 默认实现"""
        pass

class BaseLoader(ABC):
    """加载器基类"""
    
    @abstractmethod
    def can_handle(self, path: Path) -> bool:
        """检查是否可以处理该路径"""
        pass
    
    @abstractmethod
    def load(self, path: Path) -> Any:
        """加载内容"""
        pass

class BaseRegistry(ABC):
    """注册表基类"""
    
    def __init__(self):
        self._items: Dict[str, Any] = {}
    
    def register(self, name: str, item: Any) -> None:
        """注册项目"""
        self._items[name] = item
    
    def get(self, name: str) -> Optional[Any]:
        """获取项目"""
        return self._items.get(name)
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有项目"""
        return self._items.copy()
    
    def unregister(self, name: str) -> bool:
        """取消注册"""
        if name in self._items:
            del self._items[name]
            return True
        return False