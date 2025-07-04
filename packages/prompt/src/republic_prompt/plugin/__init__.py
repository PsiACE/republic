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
from .manager import PluginManager, PluginError, FunctionPlugin, FilterPlugin, TemplatePlugin
from .extensions import ExtensionRegistry, FunctionExtension, AttributeExtension, PropertyExtension, EventExtension
from .hooks import HookRegistry, FunctionHook, ConditionalHook, ChainHook, HookPoints
from .integrations import IntegrationRegistry, OpenAIIntegration, LangChainIntegration, AnthropicIntegration, OllamaIntegration

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

def create_function_plugin(name: str, functions: dict) -> IPlugin:
    """创建函数插件
    
    Args:
        name: 插件名称
        functions: 函数字典
        
    Returns:
        函数插件实例
    """
    return FunctionPlugin(name, functions)

def create_integration_plugin(integration_name: str, **kwargs) -> Optional[IPlugin]:
    """创建集成插件
    
    Args:
        integration_name: 集成名称 (openai, langchain, anthropic, etc.)
        **kwargs: 集成参数
        
    Returns:
        集成插件实例
    """
    from .integrations import create_integration_plugin
    return create_integration_plugin(integration_name, **kwargs)

def register_hook(hook_point: str, hook_func, hook_name: Optional[str] = None) -> None:
    """注册钩子函数
    
    Args:
        hook_point: 钩子点
        hook_func: 钩子函数
        hook_name: 钩子名称
    """
    from .hooks import register_function_hook
    name = hook_name or f"hook_{len(str(hook_func))}"
    register_function_hook(hook_point, name, hook_func)

def execute_hooks(hook_point: str, *args, **kwargs) -> List[Any]:
    """执行钩子
    
    Args:
        hook_point: 钩子点
        *args: 位置参数
        **kwargs: 关键字参数
        
    Returns:
        钩子执行结果列表
    """
    from .hooks import execute_hooks as _execute_hooks
    return _execute_hooks(hook_point, *args, **kwargs)

__all__ = [
    # 接口
    "IPlugin",
    "IExtension", 
    "IHook",
    "IPluginManager",
    
    # 核心实现
    "PluginManager",
    "PluginError",
    
    # 内置插件
    "FunctionPlugin",
    "FilterPlugin", 
    "TemplatePlugin",
    
    # 扩展系统
    "ExtensionRegistry",
    "FunctionExtension",
    "AttributeExtension",
    "PropertyExtension",
    "EventExtension",
    
    # 钩子系统
    "HookRegistry",
    "FunctionHook",
    "ConditionalHook",
    "ChainHook",
    "HookPoints",
    
    # 集成系统
    "IntegrationRegistry",
    "OpenAIIntegration",
    "LangChainIntegration", 
    "AnthropicIntegration",
    "OllamaIntegration",
    
    # 主要API
    "create_plugin_manager",
    "load_workspace_with_plugins",
    "create_function_plugin",
    "create_integration_plugin",
    "register_hook",
    "execute_hooks",
]