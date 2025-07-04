"""Simple层渲染器

基于Jinja2的模板渲染器实现。
"""

import re
from typing import Dict, Any, List, Optional

try:
    from jinja2 import Environment, BaseLoader, TemplateNotFound
except ImportError:
    raise ImportError("Jinja2 is required for template rendering. Install it with: pip install jinja2")

from .interfaces import BaseRenderer
from .models import RenderResult, TemplateModel, RenderContext, PromptMessage, MessageRole
from .exceptions import RenderError

class SimpleLoader(BaseLoader):
    """简单的模板加载器"""
    
    def __init__(self):
        self.templates: Dict[str, str] = {}
    
    def get_source(self, environment, template):
        """获取模板源码"""
        if template in self.templates:
            source = self.templates[template]
            return source, None, lambda: True
        raise TemplateNotFound(template)
    
    def add_template(self, name: str, content: str):
        """添加模板"""
        self.templates[name] = content

class DefaultRenderer(BaseRenderer):
    """默认渲染器实现"""
    
    def __init__(self, auto_escape: bool = False, **config):
        """初始化渲染器
        
        Args:
            auto_escape: 是否自动转义HTML
            **config: 其他配置
        """
        self.auto_escape = auto_escape
        self.config = config
        
        # 创建Jinja2环境
        self.loader = SimpleLoader()
        self.env = Environment(
            loader=self.loader,
            autoescape=auto_escape
        )
        
        # 添加内置函数
        self._setup_builtin_functions()
    
    def _setup_builtin_functions(self):
        """设置内置函数"""
        # 添加常用的Python内置函数
        self.env.globals.update({
            'len': len,
            'str': str,
            'int': int,
            'float': float,
            'list': list,
            'dict': dict,
            'enumerate': enumerate,
            'zip': zip,
            'range': range,
            'max': max,
            'min': min,
            'sum': sum,
            'abs': abs,
            'round': round,
        })
    
    def render(self, template: str, context: Dict[str, Any]) -> RenderResult:
        """渲染模板字符串"""
        try:
            # 创建Jinja2模板
            jinja_template = self.env.from_string(template)
            
            # 渲染模板
            rendered_content = jinja_template.render(**context)
            
            # 解析消息
            messages = self._parse_messages(rendered_content)
            
            return RenderResult(
                content=rendered_content.strip(),
                messages=messages,
                metadata={}
            )
            
        except Exception as e:
            raise RenderError(f"Failed to render template: {e}")
    
    def render_template(self, template: TemplateModel, context: Dict[str, Any]) -> RenderResult:
        """渲染模板模型"""
        try:
            # 创建Jinja2模板
            jinja_template = self.env.from_string(template.content)
            
            # 合并模板元数据和上下文
            render_context = {}
            if template.metadata:
                render_context.update(template.metadata)
            render_context.update(context)
            
            # 渲染模板
            rendered_content = jinja_template.render(**render_context)
            
            # 解析消息
            messages = self._parse_messages(rendered_content)
            
            return RenderResult(
                content=rendered_content.strip(),
                messages=messages,
                metadata=template.metadata.copy(),
                template_name=template.name
            )
            
        except Exception as e:
            raise RenderError(f"Failed to render template: {e}", template_name=template.name)
    
    def _parse_messages(self, content: str) -> Optional[List[PromptMessage]]:
        """解析结构化消息
        
        查找如下模式的消息：
        ```
        ## System
        You are a helpful assistant.
        
        ## User
        Hello, how are you?
        
        ## Assistant
        I'm doing well, thank you!
        ```
        """
        # 匹配消息段落的正则表达式
        message_pattern = r'^##\s+(System|User|Assistant)\s*\n(.*?)(?=^##\s+(?:System|User|Assistant)\s*\n|\Z)'
        matches = re.findall(message_pattern, content, re.MULTILINE | re.DOTALL | re.IGNORECASE)
        
        if not matches:
            return None
        
        messages = []
        for role_str, message_content in matches:
            try:
                role = MessageRole(role_str.lower())
                messages.append(PromptMessage(
                    role=role,
                    content=message_content.strip()
                ))
            except ValueError:
                # 跳过无效的角色
                continue
        
        return messages if messages else None
    
    def add_function(self, name: str, func: Any) -> None:
        """添加自定义函数"""
        self.env.globals[name] = func
    
    def add_filter(self, name: str, func: Any) -> None:
        """添加自定义过滤器"""
        self.env.filters[name] = func
    
    def add_template(self, name: str, content: str) -> None:
        """添加命名模板"""
        self.loader.add_template(name, content)
    
    def get_template_variables(self, template: str) -> List[str]:
        """获取模板中的变量"""
        try:
            jinja_template = self.env.from_string(template)
            # 获取未定义的变量
            from jinja2.meta import find_undeclared_variables
            ast = self.env.parse(template)
            variables = find_undeclared_variables(ast)
            return list(variables)
        except Exception:
            # 如果解析失败，使用简单的正则表达式
            pattern = r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}'
            return list(set(re.findall(pattern, template)))