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
from .workspace import Workspace
from .loaders import ContentLoader, ConfigLoader
from .registry import Registry
from .config import WorkspaceConfig

# 主要API - 大部分用户使用这些函数
def load_workspace(path: str, **config) -> IWorkspace:
    """加载工作空间 - 主要API
    
    Args:
        path: 工作空间路径
        **config: 配置选项
        
    Returns:
        工作空间实例
        
    Example:
        >>> workspace = load_workspace("./my-workspace")
        >>> result = workspace.render("my-template", name="World")
    """
    return Workspace.load(path, **config)

def create_workspace(path: str, config: WorkspaceConfig) -> IWorkspace:
    """创建工作空间实例
    
    Args:
        path: 工作空间路径
        config: 工作空间配置
        
    Returns:
        工作空间实例
    """
    return Workspace(path, config)

__all__ = [
    # 接口
    "IWorkspace",
    "ILoader", 
    "IRegistry",
    
    # 实现
    "Workspace",
    "ContentLoader",
    "ConfigLoader",
    "Registry",
    "WorkspaceConfig",
    
    # 主要API
    "load_workspace",
    "create_workspace",
]