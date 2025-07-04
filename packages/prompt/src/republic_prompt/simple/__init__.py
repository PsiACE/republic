"""Republic Prompt Simple Layer - 基础模板渲染功能

这是最底层的Simple层，提供基础的模板渲染功能和数据模型。
符合Python哲学：简单、直接、易用。

主要功能：
- 基础模板渲染
- 数据模型定义  
- 格式化器
- 异常定义

API设计原则：
- 90%的用户只需要format_template函数
- 10%的用户需要更多控制时使用渲染器
"""

from .interfaces import IRenderer, IFormatter, IRenderContext
from .models import (
    RenderResult, 
    TemplateModel, 
    RenderContext,
    MessageRole,
    PromptMessage
)
from .renderer import DefaultRenderer
from .formatters import get_formatter, register_formatter
from .exceptions import SimpleLayerError, RenderError, FormatError

# 最简单的API - 90%的用户只需要这个
def format_template(template: str, **context) -> str:
    """格式化模板字符串 - 最简单的API
    
    Args:
        template: 模板字符串，使用Jinja2语法
        **context: 模板变量
        
    Returns:
        渲染后的字符串
        
    Example:
        >>> format_template("Hello {{name}}!", name="World")
        'Hello World!'
    """
    renderer = DefaultRenderer()
    result = renderer.render(template, context)
    return result.content

# 需要更多控制的API
def create_renderer(**config) -> IRenderer:
    """创建渲染器实例
    
    Args:
        **config: 渲染器配置
        
    Returns:
        渲染器实例
    """
    return DefaultRenderer(**config)

__all__ = [
    # 核心接口
    "IRenderer",
    "IFormatter", 
    "IRenderContext",
    
    # 数据模型
    "RenderResult",
    "TemplateModel",
    "RenderContext",
    "MessageRole",
    "PromptMessage",
    
    # 实现
    "DefaultRenderer",
    
    # 格式化器
    "get_formatter",
    "register_formatter",
    
    # 异常
    "SimpleLayerError",
    "RenderError",
    "FormatError",
    
    # 简单API
    "format_template",
    "create_renderer",
]