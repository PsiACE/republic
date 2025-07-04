"""Simple层接口定义

定义Simple层的所有接口，使用Protocol和ABC确保类型安全和扩展性。
"""

from abc import ABC, abstractmethod
from typing import Protocol, Dict, Any, Optional, runtime_checkable

# 前向声明，避免循环导入
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .models import RenderResult, TemplateModel, RenderContext

@runtime_checkable
class IRenderContext(Protocol):
    """渲染上下文接口"""
    
    def get_variable(self, name: str) -> Any:
        """获取变量值"""
        ...
    
    def set_variable(self, name: str, value: Any) -> None:
        """设置变量值"""
        ...
    
    def get_all_variables(self) -> Dict[str, Any]:
        """获取所有变量"""
        ...

@runtime_checkable
class IRenderer(Protocol):
    """渲染器接口"""
    
    def render(self, template: str, context: Dict[str, Any]) -> "RenderResult":
        """渲染模板字符串"""
        ...
    
    def render_template(self, template: "TemplateModel", context: Dict[str, Any]) -> "RenderResult":
        """渲染模板模型"""
        ...
    
    def add_function(self, name: str, func: Any) -> None:
        """添加自定义函数"""
        ...
    
    def add_filter(self, name: str, func: Any) -> None:
        """添加自定义过滤器"""
        ...

@runtime_checkable
class IFormatter(Protocol):
    """格式化器接口"""
    
    def can_handle(self, content: str) -> bool:
        """检查是否可以处理该内容"""
        ...
    
    def parse(self, content: str) -> tuple[Dict[str, Any], str]:
        """解析内容，返回(元数据, 正文)"""
        ...
    
    @property
    def format_name(self) -> str:
        """格式化器名称"""
        ...

class BaseRenderer(ABC):
    """渲染器基类"""
    
    @abstractmethod
    def render(self, template: str, context: Dict[str, Any]) -> "RenderResult":
        """渲染模板字符串"""
        pass
    
    @abstractmethod
    def render_template(self, template: "TemplateModel", context: Dict[str, Any]) -> "RenderResult":
        """渲染模板模型"""
        pass
    
    def add_function(self, name: str, func: Any) -> None:
        """添加自定义函数 - 默认实现"""
        pass
    
    def add_filter(self, name: str, func: Any) -> None:
        """添加自定义过滤器 - 默认实现"""
        pass

class BaseFormatter(ABC):
    """格式化器基类"""
    
    @abstractmethod
    def can_handle(self, content: str) -> bool:
        """检查是否可以处理该内容"""
        pass
    
    @abstractmethod
    def parse(self, content: str) -> tuple[Dict[str, Any], str]:
        """解析内容，返回(元数据, 正文)"""
        pass
    
    @property
    @abstractmethod
    def format_name(self) -> str:
        """格式化器名称"""
        pass