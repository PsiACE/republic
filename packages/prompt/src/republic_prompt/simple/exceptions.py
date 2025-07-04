"""Simple层异常定义

定义Simple层的所有异常，符合Python异常层次结构。
"""

from typing import Optional

class SimpleLayerError(Exception):
    """Simple层基础异常"""
    pass

class RenderError(SimpleLayerError):
    """渲染异常"""
    
    def __init__(self, message: str, template_name: Optional[str] = None, line_number: Optional[int] = None):
        super().__init__(message)
        self.template_name = template_name
        self.line_number = line_number
    
    def __str__(self):
        base = super().__str__()
        if self.template_name:
            base += f" (template: {self.template_name})"
        if self.line_number:
            base += f" (line: {self.line_number})"
        return base

class FormatError(SimpleLayerError):
    """格式化异常"""
    
    def __init__(self, message: str, format_type: Optional[str] = None):
        super().__init__(message)
        self.format_type = format_type
    
    def __str__(self):
        base = super().__str__()
        if self.format_type:
            base += f" (format: {self.format_type})"
        return base

class ValidationError(SimpleLayerError):
    """验证异常"""
    pass