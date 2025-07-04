"""Republic Prompt Plugin Layer - 插件系统

这是最上层的Plugin层，基于Workspace层提供插件系统和高级功能。
遵循"吃自己下一层的狗粮"原则，只使用Workspace层的接口。

主要功能：
- 插件管理
- 扩展功能
- 钩子系统
- 第三方集成

设计原则：
- 只依赖Workspace层的接口
- 通过插件系统实现功能扩展
- 提供灵活的钩子机制
- 支持第三方集成
"""

from typing import List, Optional, Any

from .interfaces import IPlugin, IExtension, IHook, IPluginManager
from .manager import PluginManager
from .extensions import ExtensionRegistry
from .hooks import HookRegistry
from .integrations import IntegrationRegistry

# 主要API
def create_plugin_manager() -> IPluginManager:
    """创建插件管理器
    
    Returns:
        插件管理器实例
    """
    return PluginManager()

def load_workspace_with_plugins(path: str, plugins: Optional[List[str]] = None, **config) -> Any:
    """加载带插件的工作空间
    
    Args:
        path: 工作空间路径
        plugins: 插件列表
        **config: 配置选项
        
    Returns:
        增强的工作空间实例
    """
    # 这里会依赖Workspace层的接口
    from ..workspace import load_workspace
    
    # 创建基础工作空间
    workspace = load_workspace(path, **config)
    
    # 如果有插件，应用插件
    if plugins:
        plugin_manager = create_plugin_manager()
        for plugin_name in plugins:
            plugin_manager.load_plugin(plugin_name)
        
        # 应用插件到工作空间
        workspace = plugin_manager.apply_plugins(workspace)
    
    return workspace

__all__ = [
    # 接口
    "IPlugin",
    "IExtension", 
    "IHook",
    "IPluginManager",
    
    # 实现
    "PluginManager",
    "ExtensionRegistry",
    "HookRegistry",
    "IntegrationRegistry",
    
    # 主要API
    "create_plugin_manager",
    "load_workspace_with_plugins",
]