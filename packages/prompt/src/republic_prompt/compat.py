"""兼容性层

提供向后兼容的API，让现有代码可以继续工作。
逐步引导用户迁移到新的三层架构。
"""

import warnings
from typing import Dict, Any, Optional, List, Union, Callable
from pathlib import Path

# 从新架构导入
from .simple import format_template as simple_format_template
from .simple import create_renderer
from .simple.models import RenderResult, TemplateModel

# 兼容原有的API
def format(template: str, custom_functions: Optional[Dict[str, Callable]] = None, 
           auto_escape: bool = False, **variables) -> str:
    """兼容原有的format函数
    
    这个函数保持与原有API的兼容性。
    """
    warnings.warn(
        "format() is deprecated, use republic_prompt.simple.format_template() instead",
        DeprecationWarning,
        stacklevel=2
    )
    
    if custom_functions:
        # 如果有自定义函数，使用渲染器
        renderer = create_renderer(auto_escape=auto_escape)
        for name, func in custom_functions.items():
            renderer.add_function(name, func)
        
        result = renderer.render(template, variables)
        return result.content
    else:
        # 简单情况，直接使用simple层的API
        return simple_format_template(template, **variables)

def format_with_functions(template: str, functions: Dict[str, Callable], 
                         auto_escape: bool = False, **variables) -> str:
    """兼容原有的format_with_functions函数"""
    warnings.warn(
        "format_with_functions() is deprecated, use republic_prompt.simple.format_template() with custom renderer instead",
        DeprecationWarning,
        stacklevel=2
    )
    
    return format(template, custom_functions=functions, auto_escape=auto_escape, **variables)

# 兼容原有的工作空间API
class PromptWorkspace:
    """兼容原有的PromptWorkspace类"""
    
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "PromptWorkspace is deprecated, use republic_prompt.workspace.load_workspace() instead",
            DeprecationWarning,
            stacklevel=2
        )
        # 这里需要实现兼容逻辑
        # 暂时抛出异常，提示用户迁移
        raise NotImplementedError(
            "PromptWorkspace is deprecated. Please use:\n"
            "from republic_prompt.workspace import load_workspace\n"
            "workspace = load_workspace(path)"
        )
    
    @classmethod
    def load(cls, path: Union[str, Path], **kwargs):
        """兼容原有的load方法"""
        warnings.warn(
            "PromptWorkspace.load() is deprecated, use republic_prompt.workspace.load_workspace() instead",
            DeprecationWarning,
            stacklevel=2
        )
        
        # 导入新的API
        from .workspace import load_workspace
        return load_workspace(str(path), **kwargs)

def load_workspace(path: Union[str, Path], **kwargs):
    """兼容原有的load_workspace函数"""
    warnings.warn(
        "This load_workspace() is deprecated, use republic_prompt.workspace.load_workspace() instead",
        DeprecationWarning,
        stacklevel=2
    )
    
    from .workspace import load_workspace as new_load_workspace
    return new_load_workspace(str(path), **kwargs)

def quick_render(workspace_path: Union[str, Path], template_name: str, **variables):
    """兼容原有的quick_render函数"""
    warnings.warn(
        "quick_render() is deprecated, use workspace.render() instead",
        DeprecationWarning,
        stacklevel=2
    )
    
    from .workspace import load_workspace as new_load_workspace
    workspace = new_load_workspace(str(workspace_path))
    return workspace.render(template_name, **variables)

# 兼容原有的模型
# 这些已经在新架构中定义了，直接导入即可
from .simple.models import MessageRole, PromptMessage

# 兼容原有的异常
class TemplateError(Exception):
    """兼容原有的TemplateError"""
    
    def __init__(self, message: str, template_name: Optional[str] = None):
        super().__init__(message)
        self.template_name = template_name
        
        warnings.warn(
            "TemplateError is deprecated, use republic_prompt.simple.exceptions.RenderError instead",
            DeprecationWarning,
            stacklevel=2
        )

class WorkspaceError(Exception):
    """兼容原有的WorkspaceError"""
    
    def __init__(self, message: str):
        super().__init__(message)
        
        warnings.warn(
            "WorkspaceError is deprecated, use appropriate exceptions from the new architecture",
            DeprecationWarning,
            stacklevel=2
        )

# 导出兼容API
__all__ = [
    "format",
    "format_with_functions", 
    "PromptWorkspace",
    "load_workspace",
    "quick_render",
    "MessageRole",
    "PromptMessage",
    "TemplateError",
    "WorkspaceError",
]