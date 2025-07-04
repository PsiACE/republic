"""Republic Prompt - A modern prompt engineering toolkit.

基于清晰的三层架构：plugin -> workspace -> simple

新架构API：
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

架构特点：
- 每一层只依赖下一层的接口，不跨层依赖
- 每一层都"吃自己下一层的狗粮"
- 接口优于实现，使用Protocol和ABC
- 符合Python哲学：简单、直接、易用
"""

# Simple层 - 基础模板渲染
from .simple import (
    format_template,
    create_renderer,
    IRenderer,
    IFormatter,
    IRenderContext,
    RenderResult,
    TemplateModel,
    RenderContext,
    MessageRole,
    PromptMessage,
    DefaultRenderer,
    get_formatter,
    register_formatter,
    SimpleLayerError,
    RenderError,
    FormatError,
)

# Workspace层 - 工作空间管理
from .workspace import (
    load_workspace,
    create_workspace,
    load_workspace_simple,
    create_workspace_simple,
    IWorkspace,
    ILoader,
    IRegistry,
    Workspace,
    WorkspaceError,
    ContentLoader,
    TemplateLoader,
    SnippetLoader,
    FunctionLoader,
    Registry,
    LoaderRegistry,
    FormatterRegistry,
    FunctionRegistry,
    WorkspaceConfig,
    load_workspace_config,
)

# Plugin层 - 插件系统
from .plugin import (
    create_plugin_manager,
    load_workspace_with_plugins,
    create_function_plugin,
    create_integration_plugin,
    register_hook,
    execute_hooks,
    IPlugin,
    IExtension,
    IHook,
    IPluginManager,
    PluginManager,
    PluginError,
    FunctionPlugin,
    FilterPlugin,
    TemplatePlugin,
    ExtensionRegistry,
    FunctionExtension,
    AttributeExtension,
    PropertyExtension,
    EventExtension,
    HookRegistry,
    FunctionHook,
    ConditionalHook,
    ChainHook,
    HookPoints,
    IntegrationRegistry,
    OpenAIIntegration,
    LangChainIntegration,
    AnthropicIntegration,
    OllamaIntegration,
)

__version__ = "0.1.0"

# 推荐的主要API - 按使用频率排序
__all__ = [
    # === Simple层（90%用户） ===
    "format_template",           # 最常用：简单模板渲染
    "create_renderer",           # 需要更多控制时
    
    # === Workspace层（工作空间管理） ===
    "load_workspace",            # 加载工作空间
    "create_workspace",          # 创建工作空间
    
    # === Plugin层（插件系统） ===
    "create_plugin_manager",     # 创建插件管理器
    "load_workspace_with_plugins", # 加载带插件的工作空间
    "create_function_plugin",    # 创建函数插件
    "create_integration_plugin", # 创建集成插件
    "register_hook",             # 注册钩子
    "execute_hooks",             # 执行钩子
    
    # === 接口（供高级用户扩展） ===
    "IRenderer",                 # Simple层接口
    "IFormatter",
    "IRenderContext", 
    "IWorkspace",                # Workspace层接口
    "ILoader",
    "IRegistry",
    "IPlugin",                   # Plugin层接口
    "IExtension",
    "IHook",
    "IPluginManager",
    
    # === 数据模型 ===
    "RenderResult",              # 渲染结果
    "TemplateModel",             # 模板模型
    "RenderContext",             # 渲染上下文
    "MessageRole",               # 消息角色
    "PromptMessage",             # 消息模型
    "WorkspaceConfig",           # 工作空间配置
    
    # === 实现类（供高级用户） ===
    "DefaultRenderer",           # Simple层实现
    "Workspace",                 # Workspace层实现
    "PluginManager",             # Plugin层实现
    
    # === 异常 ===
    "SimpleLayerError",          # Simple层异常
    "RenderError",
    "FormatError", 
    "WorkspaceError",            # Workspace层异常
    "PluginError",               # Plugin层异常
    
    # === 内置组件 ===
    "ContentLoader",             # 内容加载器
    "Registry",                  # 注册表
    "FunctionPlugin",            # 函数插件
    "OpenAIIntegration",         # OpenAI集成
    "HookPoints",                # 钩子点
]

# 显示架构信息的函数
def show_architecture_info():
    """显示新架构信息"""
    print("""
    🏗️ Republic Prompt 三层架构
    
    📦 Simple层 (最底层)
    ├── 基础模板渲染
    ├── 数据模型定义
    ├── 格式化器支持
    └── 异常处理
    
    📦 Workspace层 (中间层) 
    ├── 工作空间管理
    ├── 模板和片段加载
    ├── 配置管理
    └── 注册表系统
    
    📦 Plugin层 (最上层)
    ├── 插件管理
    ├── 扩展功能
    ├── 钩子系统
    └── 第三方集成
    
    🎯 设计原则：
    • 每层只依赖下层接口
    • 吃自己下一层的狗粮
    • 接口优于实现
    • 符合Python哲学
    """)

# 如果用户设置了环境变量，显示架构信息
import os
if os.environ.get("REPUBLIC_PROMPT_SHOW_ARCHITECTURE"):
    show_architecture_info()
