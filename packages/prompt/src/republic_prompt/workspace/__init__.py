"""Republic Prompt Workspace Layer - 工作空间管理

这是中间层的Workspace层，基于Simple层构建工作空间管理功能。
遵循"吃自己下一层的狗粮"原则，只使用Simple层的接口。

主要功能：
- 工作空间管理
- 模板和片段加载
- 配置管理
- 注册表管理

设计原则：
- 只依赖Simple层的接口，不直接依赖实现
- 通过配置和注册表实现可扩展性
- 提供清晰的工作空间抽象
"""

from .interfaces import IWorkspace, ILoader, IRegistry
from .workspace import Workspace, WorkspaceError, load_workspace, create_workspace
from .loaders import ContentLoader, TemplateLoader, SnippetLoader, FunctionLoader
from .registry import Registry, LoaderRegistry, FormatterRegistry, FunctionRegistry
from .config import WorkspaceConfig, load_workspace_config

# 主要API - 大部分用户使用这些函数
def load_workspace_simple(path: str, **config) -> IWorkspace:
    """加载工作空间 - 主要API
    
    Args:
        path: 工作空间路径
        **config: 配置选项
        
    Returns:
        工作空间实例
        
    Example:
        >>> workspace = load_workspace_simple("./my-workspace")
        >>> result = workspace.render("my-template", name="World")
    """
    return load_workspace(path, **config)

def create_workspace_simple(path: str, config: WorkspaceConfig) -> IWorkspace:
    """创建工作空间实例
    
    Args:
        path: 工作空间路径
        config: 工作空间配置
        
    Returns:
        工作空间实例
    """
    return create_workspace(path, config)

__all__ = [
    # 接口
    "IWorkspace",
    "ILoader", 
    "IRegistry",
    
    # 核心实现
    "Workspace",
    "WorkspaceError",
    
    # 加载器
    "ContentLoader",
    "TemplateLoader",
    "SnippetLoader", 
    "FunctionLoader",
    
    # 注册表
    "Registry",
    "LoaderRegistry",
    "FormatterRegistry",
    "FunctionRegistry",
    
    # 配置
    "WorkspaceConfig",
    "load_workspace_config",
    
    # 主要API
    "load_workspace",
    "create_workspace",
    "load_workspace_simple",
    "create_workspace_simple",
]