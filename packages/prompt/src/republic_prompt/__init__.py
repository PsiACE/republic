"""Republic Prompt - A modern prompt engineering toolkit.

这个包提供了一个简单而强大的API来管理提示模板、片段和函数。

新架构（推荐）：
    # Simple层 - 基础模板渲染（90%的用户）
    from republic_prompt.simple import format_template
    result = format_template("Hello {{name}}!", name="Alice")
    
    # Workspace层 - 工作空间管理
    from republic_prompt.workspace import load_workspace
    workspace = load_workspace("./workspace")
    result = workspace.render("template", name="Alice")
    
    # Plugin层 - 插件系统
    from republic_prompt.plugin import load_workspace_with_plugins
    workspace = load_workspace_with_plugins("./workspace", plugins=["my-plugin"])

兼容性API（将被废弃）：
    # 仍然可以使用原有的API，但会显示废弃警告
    from republic_prompt import format
    result = format("Hello {{ name }}!", name="Alice")
    
    # 工作空间仍然可以使用，但推荐使用新的API
    from republic_prompt import PromptWorkspace
    workspace = PromptWorkspace.load("./workspace")
"""

# 新架构的主要API
from .simple import format_template, create_renderer

# 尝试导入其他层，如果失败则忽略（开发阶段）
try:
    from .workspace import load_workspace, create_workspace  
except ImportError:
    # Workspace层还未完全实现
    def load_workspace(*args, **kwargs):
        raise NotImplementedError("Workspace layer is not yet implemented")
    
    def create_workspace(*args, **kwargs):
        raise NotImplementedError("Workspace layer is not yet implemented")

try:
    from .plugin import create_plugin_manager, load_workspace_with_plugins
except ImportError:
    # Plugin层还未完全实现
    def create_plugin_manager(*args, **kwargs):
        raise NotImplementedError("Plugin layer is not yet implemented")
    
    def load_workspace_with_plugins(*args, **kwargs):
        raise NotImplementedError("Plugin layer is not yet implemented")

# 兼容性API - 从兼容层导入
from .compat import (
    format,
    format_with_functions,
    PromptWorkspace,
    load_workspace as compat_load_workspace,
    quick_render,
    MessageRole,
    PromptMessage,
    TemplateError,
    WorkspaceError,
)

# 从旧模块导入的兼容模型
# 这些将逐步迁移到新架构
try:
    from .models import PromptModel, SnippetModel, TemplateModel
except ImportError:
    # 如果旧模块不存在，从新架构导入
    from .simple.models import TemplateModel, RenderResult as PromptModel
    # 创建兼容的模型别名
    SnippetModel = TemplateModel

__version__ = "0.1.0"

# 新架构的推荐API
__all__ = [
    # Simple层
    "format_template",
    "create_renderer",
    
    # Workspace层
    "load_workspace",
    "create_workspace",
    
    # Plugin层
    "create_plugin_manager",
    "load_workspace_with_plugins",
    
    # 兼容API（将被废弃）
    "format",
    "format_with_functions",
    "PromptWorkspace",
    "quick_render",
    
    # 模型
    "PromptModel",
    "SnippetModel", 
    "TemplateModel",
    "MessageRole",
    "PromptMessage",
    
    # 异常
    "TemplateError",
    "WorkspaceError",
]

# 添加废弃警告信息
def _show_migration_info():
    """显示迁移信息"""
    import warnings
    print("""
    📢 Republic Prompt 新架构已发布！
    
    推荐使用新的三层架构API：
    
    1. Simple层（基础模板渲染）：
       from republic_prompt.simple import format_template
       result = format_template("Hello {{name}}!", name="World")
    
    2. Workspace层（工作空间管理）：
       from republic_prompt.workspace import load_workspace
       workspace = load_workspace("./workspace")
       result = workspace.render("template", name="World")
    
    3. Plugin层（插件系统）：
       from republic_prompt.plugin import load_workspace_with_plugins
       workspace = load_workspace_with_plugins("./workspace", plugins=["my-plugin"])
    
    旧API仍然可用但将显示废弃警告。
    查看迁移指南：https://github.com/your-repo/republic-prompt/blob/main/MIGRATION.md
    """)

# 如果用户设置了环境变量，显示迁移信息
import os
if os.environ.get("REPUBLIC_PROMPT_SHOW_MIGRATION_INFO"):
    _show_migration_info()
