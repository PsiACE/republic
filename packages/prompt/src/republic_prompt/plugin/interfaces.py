"""Plugin层接口定义

定义Plugin层的所有接口，支持插件系统和扩展功能。
"""

from abc import ABC, abstractmethod
from typing import Protocol, Dict, Any, List, Optional, Callable, runtime_checkable

# 前向声明
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..workspace.interfaces import IWorkspace

@runtime_checkable
class IPlugin(Protocol):
    """插件接口"""
    
    @property
    def name(self) -> str:
        """插件名称"""
        ...
    
    @property
    def version(self) -> str:
        """插件版本"""
        ...
    
    def initialize(self, context: Dict[str, Any]) -> None:
        """初始化插件"""
        ...
    
    def apply_to_workspace(self, workspace: "IWorkspace") -> "IWorkspace":
        """应用插件到工作空间"""
        ...
    
    def cleanup(self) -> None:
        """清理插件资源"""
        ...

@runtime_checkable
class IHook(Protocol):
    """钩子接口"""
    
    @property
    def name(self) -> str:
        """钩子名称"""
        ...
    
    def execute(self, *args, **kwargs) -> Any:
        """执行钩子"""
        ...

@runtime_checkable
class IExtension(Protocol):
    """扩展接口"""
    
    @property
    def name(self) -> str:
        """扩展名称"""
        ...
    
    def install(self, target: Any) -> None:
        """安装扩展"""
        ...
    
    def uninstall(self, target: Any) -> None:
        """卸载扩展"""
        ...

@runtime_checkable
class IPluginManager(Protocol):
    """插件管理器接口"""
    
    def register_plugin(self, name: str, plugin: IPlugin) -> None:
        """注册插件"""
        ...
    
    def unregister_plugin(self, name: str) -> bool:
        """取消注册插件"""
        ...
    
    def get_plugin(self, name: str) -> Optional[IPlugin]:
        """获取插件"""
        ...
    
    def list_plugins(self) -> List[str]:
        """列出所有插件"""
        ...
    
    def apply_plugins(self, workspace: "IWorkspace") -> "IWorkspace":
        """应用所有插件到工作空间"""
        ...
    
    def load_plugin(self, plugin_name: str) -> bool:
        """加载插件"""
        ...

class BasePlugin(ABC):
    """插件基类"""
    
    def __init__(self, name: str, version: str = "1.0.0"):
        self._name = name
        self._version = version
        self._initialized = False
    
    @property
    def name(self) -> str:
        """插件名称"""
        return self._name
    
    @property
    def version(self) -> str:
        """插件版本"""
        return self._version
    
    def initialize(self, context: Dict[str, Any]) -> None:
        """初始化插件 - 默认实现"""
        self._initialized = True
    
    @abstractmethod
    def apply_to_workspace(self, workspace: "IWorkspace") -> "IWorkspace":
        """应用插件到工作空间"""
        pass
    
    def cleanup(self) -> None:
        """清理插件资源 - 默认实现"""
        self._initialized = False

class BaseHook(ABC):
    """钩子基类"""
    
    def __init__(self, name: str):
        self._name = name
    
    @property
    def name(self) -> str:
        """钩子名称"""
        return self._name
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """执行钩子"""
        pass

class BaseExtension(ABC):
    """扩展基类"""
    
    def __init__(self, name: str):
        self._name = name
        self._installed = False
    
    @property
    def name(self) -> str:
        """扩展名称"""
        return self._name
    
    @property
    def is_installed(self) -> bool:
        """是否已安装"""
        return self._installed
    
    @abstractmethod
    def install(self, target: Any) -> None:
        """安装扩展"""
        pass
    
    @abstractmethod
    def uninstall(self, target: Any) -> None:
        """卸载扩展"""
        pass