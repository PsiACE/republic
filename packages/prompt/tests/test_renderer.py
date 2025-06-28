"""Simplified tests for republic_prompt renderer."""

import pytest

from republic_prompt.renderer import DefaultRenderer
from republic_prompt.models import TemplateModel, PromptMessage, MessageRole, SnippetModel, FunctionModel
from republic_prompt.exceptions import TemplateError


class TestDefaultRenderer:
    """Test DefaultRenderer functionality."""

    def test_create_renderer(self):
        """Test creating a renderer."""
        renderer = DefaultRenderer()
        assert renderer is not None

    def test_render_simple_template(self):
        """Test rendering a simple template."""
        renderer = DefaultRenderer()
        template = TemplateModel(
            name="greeting",
            content="Hello {{ name }}!"
        )
        context = {"name": "Alice"}

        result = renderer.render_template(template, context)
        
        assert result.content == "Hello Alice!"
        assert result.template_name == "greeting"

    def test_render_template_with_functions(self):
        """Test rendering template with custom functions."""
        def upper_func(text):
            return text.upper()

        # Create function model
        func_model = FunctionModel(
            name="upper_func",
            callable=upper_func
        )
        
        renderer = DefaultRenderer(functions={"upper_func": func_model})
        template = TemplateModel(
            name="greeting",
            content="Hello {{ upper_func(name) }}!"
        )
        context = {"name": "alice"}

        result = renderer.render_template(template, context)
        
        assert result.content == "Hello ALICE!"

    def test_render_template_with_filters(self):
        """Test rendering template with Jinja2 filters."""
        renderer = DefaultRenderer()
        template = TemplateModel(
            name="greeting",
            content="Hello {{ name|title }}!"
        )
        context = {"name": "alice"}

        result = renderer.render_template(template, context)
        
        assert result.content == "Hello Alice!"

    def test_render_template_with_conditionals(self):
        """Test rendering template with conditionals."""
        renderer = DefaultRenderer()
        template = TemplateModel(
            name="greeting",
            content="""Hello {{ name }}!
{% if show_age %}
You are {{ age }} years old.
{% endif %}"""
        )

        # With age shown
        context = {"name": "Alice", "show_age": True, "age": 25}
        result = renderer.render_template(template, context)
        
        assert "Hello Alice!" in result.content
        assert "You are 25 years old." in result.content

        # Without age shown
        context = {"name": "Bob", "show_age": False, "age": 30}
        result = renderer.render_template(template, context)
        
        assert "Hello Bob!" in result.content
        assert "You are 30 years old." not in result.content

    def test_render_template_with_loops(self):
        """Test rendering template with loops."""
        renderer = DefaultRenderer()
        template = TemplateModel(
            name="list",
            content="""Items:
{% for item in items %}
- {{ item }}
{% endfor %}"""
        )
        context = {"items": ["apple", "banana", "cherry"]}

        result = renderer.render_template(template, context)
        
        assert "Items:" in result.content
        assert "- apple" in result.content
        assert "- banana" in result.content
        assert "- cherry" in result.content

    def test_render_message_format(self):
        """Test rendering template in message format."""
        renderer = DefaultRenderer()
        template = TemplateModel(
            name="chat",
            content="""## System
You are a helpful assistant.

## User
{{ user_query }}

## Assistant
I'll help you with that."""
        )
        context = {"user_query": "Hello, how are you?"}

        result = renderer.render_template(template, context)
        
        # Should have parsed messages
        assert result.messages is not None
        assert len(result.messages) == 3
        
        assert result.messages[0].role == MessageRole.SYSTEM
        assert "helpful assistant" in result.messages[0].content
        
        assert result.messages[1].role == MessageRole.USER
        assert "Hello, how are you?" in result.messages[1].content
        
        assert result.messages[2].role == MessageRole.ASSISTANT
        assert "I'll help you" in result.messages[2].content

    def test_render_mixed_message_format(self):
        """Test rendering template with mixed message format."""
        renderer = DefaultRenderer()
        template = TemplateModel(
            name="mixed",
            content="""Some intro text.

## System
You are helpful.

## User
{{ query }}

More text here."""
        )
        context = {"query": "Help me"}

        result = renderer.render_template(template, context)
        
        # Should still parse messages even with extra text
        assert result.messages is not None
        assert len(result.messages) == 2
        assert result.messages[0].role == MessageRole.SYSTEM
        assert result.messages[1].role == MessageRole.USER
        assert "Help me" in result.messages[1].content

    def test_render_with_missing_variable(self):
        """Test rendering with missing variable."""
        renderer = DefaultRenderer()
        template = TemplateModel(
            name="greeting",
            content="Hello {{ name }}!"
        )
        context = {}  # Missing 'name' variable

        # Should not raise error, Jinja2 will render as empty
        result = renderer.render_template(template, context)
        assert result.content == "Hello !"

    def test_render_with_invalid_template(self):
        """Test rendering with invalid template syntax."""
        renderer = DefaultRenderer()
        template = TemplateModel(
            name="invalid",
            content="Hello {{ name"  # Missing closing brace
        )
        context = {"name": "Alice"}

        with pytest.raises(TemplateError):
            renderer.render_template(template, context)

    def test_render_with_snippets(self):
        """Test rendering with snippet inclusion."""
        greeting_snippet = SnippetModel(
            name="greeting",
            content="Hello there!"
        )
        
        renderer = DefaultRenderer(snippets={"greeting": greeting_snippet})
        template = TemplateModel(
            name="main",
            content="""{{ include_snippet('greeting') }}
Welcome to our service."""
        )
        context = {}

        result = renderer.render_template(template, context)
        
        assert "Hello there!" in result.content
        assert "Welcome to our service." in result.content

    def test_render_text_content(self):
        """Test rendering arbitrary text content."""
        renderer = DefaultRenderer()
        
        content = "Hello {{ name }}, you are {{ age }} years old!"
        context = {"name": "Alice", "age": 25}
        
        result = renderer.render_text(content, context)
        
        assert result == "Hello Alice, you are 25 years old!"

    def test_update_functions(self):
        """Test updating renderer functions."""
        renderer = DefaultRenderer()
        
        def new_func(text):
            return text.lower()
        
        func_model = FunctionModel(name="lower_func", callable=new_func)
        renderer.update_functions({"lower_func": func_model})
        
        template = TemplateModel(
            name="test",
            content="{{ lower_func('HELLO') }}"
        )
        
        result = renderer.render_template(template, {})
        assert result.content == "hello"

    def test_add_custom_filter(self):
        """Test adding custom Jinja2 filter."""
        renderer = DefaultRenderer()
        
        def reverse_filter(text):
            return text[::-1]
        
        renderer.add_filter('reverse', reverse_filter)
        
        template = TemplateModel(
            name="custom",
            content="Hello {{ name|reverse }}!"
        )
        context = {"name": "Alice"}

        result = renderer.render_template(template, context)
        
        assert result.content == "Hello ecilA!" 