"""Basic tests for republic_prompt package."""

import tempfile
import pytest
from pathlib import Path

from republic_prompt import PromptWorkspace
from republic_prompt.models import PromptModel, PromptMessage, MessageRole


class TestBasicFunctionality:
    """Test basic functionality that should work."""

    def test_import_package(self):
        """Test that the package can be imported."""
        from republic_prompt import PromptWorkspace
        assert PromptWorkspace is not None

    def test_create_prompt_model(self):
        """Test creating a PromptModel."""
        prompt = PromptModel(content="Hello World")
        assert prompt.content == "Hello World"
        assert prompt.to_text() == "Hello World"

    def test_create_prompt_message(self):
        """Test creating a PromptMessage."""
        message = PromptMessage(role=MessageRole.USER, content="Hello")
        assert message.role == MessageRole.USER
        assert message.content == "Hello"
        assert message.to_dict() == {"role": "user", "content": "Hello"}

    def test_create_simple_workspace(self):
        """Test creating a simple workspace."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_path = Path(temp_dir)
            
            # Create minimal config
            (workspace_path / "prompts.toml").write_text("""
[prompts]
name = "test-workspace"
version = "1.0.0"
""")
            
            # Create templates directory with a simple template
            templates_dir = workspace_path / "templates"
            templates_dir.mkdir()
            (templates_dir / "hello.md").write_text("Hello {{ name }}!")
            
            # Load workspace
            workspace = PromptWorkspace.load(workspace_path)
            
            # Basic assertions
            assert workspace.name == "test-workspace"
            assert workspace.version == "1.0.0"
            
            # Test rendering
            result = workspace.render("hello", name="World")
            assert "Hello World!" in result.content

    def test_workspace_with_functions(self):
        """Test workspace with custom functions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_path = Path(temp_dir)
            
            # Create config
            (workspace_path / "prompts.toml").write_text("""
[prompts]
name = "func-workspace"
version = "1.0.0"
""")
            
            # Create template that uses function
            templates_dir = workspace_path / "templates"
            templates_dir.mkdir()
            (templates_dir / "greet.md").write_text("{{ greet_func(name) }}")
            
            # Define custom function
            def greet_func(name):
                return f"Hello, {name}!"
            
            # Load workspace with custom function
            workspace = PromptWorkspace.load(
                workspace_path, 
                custom_functions={"greet_func": greet_func}
            )
            
            # Test rendering with function
            result = workspace.render("greet", name="Alice")
            assert "Hello, Alice!" in result.content

    def test_message_format_rendering(self):
        """Test rendering in message format."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_path = Path(temp_dir)
            
            # Create config
            (workspace_path / "prompts.toml").write_text("""
[prompts]
name = "msg-workspace"
version = "1.0.0"
""")
            
            # Create message template
            templates_dir = workspace_path / "templates"
            templates_dir.mkdir()
            (templates_dir / "chat.md").write_text("""## System
You are helpful.

## User
{{ query }}""")
            
            workspace = PromptWorkspace.load(workspace_path)
            result = workspace.render("chat", query="Hello!")
            
            # Should have parsed messages
            assert result.messages is not None
            assert len(result.messages) == 2
            assert result.messages[0].role == MessageRole.SYSTEM
            assert result.messages[1].role == MessageRole.USER
            assert "Hello!" in result.messages[1].content

    def test_openai_format_conversion(self):
        """Test converting to OpenAI format."""
        prompt = PromptModel(
            content="Chat",
            messages=[
                PromptMessage(role=MessageRole.SYSTEM, content="You are helpful"),
                PromptMessage(role=MessageRole.USER, content="Hi"),
            ]
        )
        
        openai_format = prompt.to_openai_format()
        
        assert len(openai_format) == 2
        assert openai_format[0] == {"role": "system", "content": "You are helpful"}
        assert openai_format[1] == {"role": "user", "content": "Hi"}

    def test_workspace_info(self):
        """Test accessing workspace information."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_path = Path(temp_dir)
            
            # Create config
            (workspace_path / "prompts.toml").write_text("""
[prompts]
name = "info-workspace"
description = "Test workspace"
version = "2.0.0"
""")
            
            workspace = PromptWorkspace.load(workspace_path)
            
            assert workspace.name == "info-workspace"
            assert workspace.description == "Test workspace"  
            assert workspace.version == "2.0.0"

    def test_error_handling(self):
        """Test basic error handling."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_path = Path(temp_dir)
            
            # Create minimal workspace
            (workspace_path / "prompts.toml").write_text("""
[prompts]
name = "error-workspace"
version = "1.0.0"
""")
            
            workspace = PromptWorkspace.load(workspace_path)
            
            # Test rendering nonexistent template
            with pytest.raises(Exception):  # Should raise some kind of error
                workspace.render("nonexistent") 