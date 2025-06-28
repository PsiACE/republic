"""Data models for Republic Prompt.

This module defines the core data structures used throughout the system,
with a focus on simplicity and type safety.
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class MessageRole(str, Enum):
    """Supported message roles for LLM conversations."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class PromptMessage(BaseModel):
    """A single message in an LLM conversation."""
    role: MessageRole
    content: str
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary format (e.g., for OpenAI API)."""
        return {"role": self.role.value, "content": self.content}


class BaseContentModel(BaseModel):
    """Base class for content models with common attributes."""
    name: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    file_path: Optional[Path] = None
    
    def get_variables(self) -> List[str]:
        """Extract template variables from content."""
        import re
        # Simple regex to find Jinja2 variables like {{ variable }}
        pattern = r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}'
        return list(set(re.findall(pattern, self.content)))


class SnippetModel(BaseContentModel):
    """Represents a reusable text snippet."""
    pass


class TemplateModel(BaseContentModel):
    """Represents a prompt template."""
    
    def get_required_variables(self) -> List[str]:
        """Get variables that must be provided for rendering."""
        # For now, treat all variables as required
        # Could be enhanced to detect optional variables with defaults
        return self.get_variables()


class FunctionModel(BaseModel):
    """Represents a callable function available in templates."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    name: str
    callable: Any  # The actual function object
    signature: Optional[str] = None
    docstring: Optional[str] = None
    module: Optional[str] = None


class PromptWorkspaceConfig(BaseModel):
    """Configuration for a prompt workspace."""
    name: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = "1.0.0"
    
    # Content directories
    snippets_dir: str = "snippets"
    templates_dir: str = "templates" 
    functions_dir: str = "functions"
    
    # External workspaces
    external_workspaces: Dict[str, str] = Field(default_factory=dict)
    
    # Rendering options
    template_engine: str = "jinja2"
    auto_escape: bool = False
    
    # Environment configurations
    environments: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    
    # Default values
    defaults: Dict[str, Any] = Field(default_factory=dict)


class PromptModel(BaseModel):
    """The result of rendering a prompt template."""
    content: str
    messages: Optional[List[PromptMessage]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    template_name: Optional[str] = None
    
    def to_text(self) -> str:
        """Get the rendered content as plain text."""
        return self.content
    
    def to_messages(self) -> List[Dict[str, str]]:
        """Get the content as a list of messages (OpenAI format)."""
        if self.messages:
            return [msg.to_dict() for msg in self.messages]
        
        # If no structured messages, treat as single user message
        return [{"role": "user", "content": self.content}]
    
    def to_openai_format(self) -> List[Dict[str, str]]:
        """Alias for to_messages() for clarity."""
        return self.to_messages() 