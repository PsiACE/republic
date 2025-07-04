"""Simple层数据模型

定义Simple层的核心数据模型，专注于简洁性和类型安全。
使用标准库的dataclasses而不是pydantic以减少依赖。
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

class MessageRole(str, Enum):
    """消息角色枚举"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

@dataclass
class PromptMessage:
    """单个消息"""
    role: MessageRole
    content: str
    
    def to_dict(self) -> Dict[str, str]:
        """转换为字典格式"""
        return {"role": self.role.value, "content": self.content}

@dataclass
class TemplateModel:
    """模板模型"""
    name: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_variables(self) -> List[str]:
        """提取模板变量"""
        import re
        pattern = r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}'
        return list(set(re.findall(pattern, self.content)))

@dataclass
class RenderContext:
    """渲染上下文"""
    variables: Dict[str, Any] = field(default_factory=dict)
    
    def get_variable(self, name: str) -> Any:
        """获取变量值"""
        return self.variables.get(name)
    
    def set_variable(self, name: str, value: Any) -> None:
        """设置变量值"""
        self.variables[name] = value
    
    def get_all_variables(self) -> Dict[str, Any]:
        """获取所有变量"""
        return self.variables.copy()
    
    def update(self, **kwargs) -> None:
        """更新变量"""
        self.variables.update(kwargs)

@dataclass
class RenderResult:
    """渲染结果"""
    content: str
    messages: Optional[List[PromptMessage]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    template_name: Optional[str] = None
    
    def to_text(self) -> str:
        """获取纯文本内容"""
        return self.content
    
    def to_messages(self) -> List[Dict[str, str]]:
        """获取消息列表"""
        if self.messages:
            return [msg.to_dict() for msg in self.messages]
        # 如果没有结构化消息，作为用户消息返回
        return [{"role": "user", "content": self.content}]
    
    def to_openai_format(self) -> List[Dict[str, str]]:
        """获取OpenAI格式的消息"""
        return self.to_messages()
    
    def has_messages(self) -> bool:
        """检查是否有结构化消息"""
        return self.messages is not None and len(self.messages) > 0