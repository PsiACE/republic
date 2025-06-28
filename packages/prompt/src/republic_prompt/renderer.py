"""Template rendering system for Republic Prompt.

This module provides template rendering capabilities with support for
Jinja2 templating, snippet inclusion, and message parsing.
"""

import re
from typing import Dict, List, Any, Optional

try:
    from jinja2 import Environment, BaseLoader, TemplateNotFound
except ImportError:
    raise ImportError("Jinja2 is required for template rendering. Install it with: pip install jinja2")

from .models import (
    PromptModel, PromptMessage, MessageRole, 
    SnippetModel, TemplateModel, FunctionModel
)
from .exceptions import TemplateError

class SnippetLoader(BaseLoader):
    """Custom Jinja2 loader for snippet inclusion."""

    def __init__(self, snippets: Dict[str, SnippetModel]):
        self.snippets = snippets

    def get_source(self, environment, template):
        """Get snippet source for Jinja2."""
        if template in self.snippets:
            snippet = self.snippets[template]
            source = snippet.content
            # Return (source, filename, uptodate_func)
            return source, str(snippet.file_path), lambda: True
        
        raise TemplateNotFound(template)

class DefaultRenderer:
    """Default template renderer using Jinja2."""
    
    def __init__(self, 
                 snippets: Dict[str, SnippetModel] = None,
                 functions: Dict[str, FunctionModel] = None,
                 auto_escape: bool = False):
        """Initialize the renderer.

    Args:
            snippets: Available snippets for inclusion
            functions: Available functions for templates
            auto_escape: Whether to auto-escape HTML content
        """
        self.snippets = snippets or {}
        self.functions = functions or {}

        # Create Jinja2 environment
        self.env = Environment(
            loader=SnippetLoader(self.snippets),
            autoescape=auto_escape
        )
        
        # Add custom filters and functions
        self._setup_template_context()
    
    def _setup_template_context(self):
        """Setup Jinja2 template context with custom filters and functions."""
        
        # Add snippet inclusion filter
        def include_snippet(snippet_name: str) -> str:
            """Include a snippet by name."""
            if snippet_name in self.snippets:
                return self.snippets[snippet_name].content
            return f"<!-- Snippet '{snippet_name}' not found -->"
        
        self.env.filters['snippet'] = include_snippet
        self.env.globals['include_snippet'] = include_snippet
        
        # Add all workspace functions to template context
        for name, func_model in self.functions.items():
            self.env.globals[name] = func_model.callable

        # Add utility functions
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
        })
    
    def render_template(self, template: TemplateModel, context: Dict[str, Any]) -> PromptModel:
        """Render a template with the given context.

        Args:
                    template: The template to render
                    context: Variables to pass to the template

        Returns:
                    PromptModel with rendered content
        """
        try:
                    # Create Jinja2 template
                    jinja_template = self.env.from_string(template.content)
                    
                    # Merge template metadata into context, with context taking precedence
                    render_context = {}
                    if template.metadata:
                        render_context.update(template.metadata)
                    render_context.update(context)
                    
                    # Render template
                    rendered_content = jinja_template.render(**render_context)

                    # Parse messages if content contains message markers
                    messages = self._parse_messages(rendered_content)

                    return PromptModel(
                        content=rendered_content.strip(),
                        messages=messages,
                    metadata=template.metadata.copy(),
                        template_name=template.name
                )

        except Exception as e:
                    raise TemplateError(
                        f"Failed to render template: {e}",
                        template_name=template.name
                    )
    
    def _parse_messages(self, content: str) -> Optional[List[PromptMessage]]:
        """Parse content for structured messages.
        
        Looks for patterns like:
        ```
        ## System
        You are a helpful assistant.
        
        ## User  
        Hello, how are you?
        
        ## Assistant
        I'm doing well, thank you!
        ```
        """
        # Pattern to match message sections
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
                # Skip invalid roles
                continue
        
        return messages if messages else None
    
    def render_text(self, content: str, context: Dict[str, Any]) -> str:
        """Render arbitrary text content with template variables.

    Args:
            content: Text content with template variables
            context: Variables to substitute

    Returns:
            Rendered text
        """
        try:
            template = self.env.from_string(content)
            return template.render(**context)
        except Exception as e:
            raise TemplateError(f"Failed to render text: {e}")
    
    def update_snippets(self, snippets: Dict[str, SnippetModel]):
        """Update available snippets."""
        self.snippets = snippets
        # Update loader
        self.env.loader = SnippetLoader(self.snippets)
    
    def update_functions(self, functions: Dict[str, FunctionModel]):
        """Update available functions."""
        self.functions = functions
        # Re-setup template context
        self._setup_template_context()
    
    def add_snippet(self, name: str, snippet: SnippetModel):
        """Add a single snippet."""
        self.snippets[name] = snippet
        self.env.loader.snippets[name] = snippet

    def add_function(self, name: str, function: FunctionModel):
        """Add a single function."""
        self.functions[name] = function
        self.env.globals[name] = function.callable

    def add_filter(self, name: str, filter_func):
        """Add a custom Jinja2 filter."""
        self.env.filters[name] = filter_func
    
    def add_global(self, name: str, value):
        """Add a global variable/function to template context."""
        self.env.globals[name] = value


class MessageRenderer(DefaultRenderer):
    """Specialized renderer that always outputs structured messages."""
    
    def render_template(self, template: TemplateModel, context: Dict[str, Any]) -> PromptModel:
        """Render template and ensure it has structured messages."""
        result = super().render_template(template, context)

        # If no structured messages found, create a single user message
        if not result.messages:
            result.messages = [PromptMessage(
                role=MessageRole.USER,
                content=result.content
            )]
        
        return result


def create_renderer(renderer_type: str = "default", **kwargs) -> DefaultRenderer:
    """Factory function to create different types of renderers.

    Args:
        renderer_type: Type of renderer ("default", "message")
        **kwargs: Additional arguments for renderer

    Returns:
        Configured renderer instance
    """
    if renderer_type == "message":
        return MessageRenderer(**kwargs)
    else:
        return DefaultRenderer(**kwargs) 