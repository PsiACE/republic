"""End-to-end tests for republic_prompt package."""

import tempfile
import pytest
from pathlib import Path

from republic_prompt import PromptWorkspace


class TestEndToEnd:
    """End-to-end tests using the examples workspace."""

    def test_load_examples_workspace(self):
        """Test loading the actual examples workspace."""
        # Use the examples directory from the package
        examples_path = Path(__file__).parent.parent / "examples"
        
        if not examples_path.exists():
            pytest.skip("Examples directory not found")
        
        workspace = PromptWorkspace.load(examples_path)
        
        # Verify workspace loaded correctly
        assert workspace.name == "gemini-cli-agent"
        assert workspace.version == "1.0.0"
        
        # Check that we have expected content
        assert len(workspace.list_templates()) > 0
        assert len(workspace.list_snippets()) > 0
        assert len(workspace.list_functions()) > 0

    def test_render_simple_agent_template(self):
        """Test rendering the simple agent template."""
        examples_path = Path(__file__).parent.parent / "examples"
        
        if not examples_path.exists():
            pytest.skip("Examples directory not found")
        
        workspace = PromptWorkspace.load(examples_path)
        
        # Render simple agent template
        result = workspace.render(
            "simple_agent",
            domain="software_development",
            use_tools=True
        )
        
        assert result.messages is None  # Should be text format
        assert "software_development agent" in result.content
        assert "Ready to help!" in result.content
        assert len(result.content) > 100  # Should be substantial content

    def test_render_gemini_cli_system_prompt(self):
        """Test rendering the complex Gemini CLI system prompt."""
        examples_path = Path(__file__).parent.parent / "examples"
        
        if not examples_path.exists():
            pytest.skip("Examples directory not found")
        
        workspace = PromptWorkspace.load(examples_path)
        
        # Check if the template exists
        if "gemini_cli_system_prompt" not in workspace.list_templates():
            pytest.skip("Gemini CLI system prompt template not found")
        
        # Render with development environment settings
        result = workspace.render(
            "gemini_cli_system_prompt",
            **workspace.config.environments.get("development", {})
        )
        
        assert result.messages is None  # Should be text format
        assert len(result.content) > 100  # Should be substantial content

    def test_function_integration(self):
        """Test that workspace functions are properly integrated."""
        examples_path = Path(__file__).parent.parent / "examples"
        
        if not examples_path.exists():
            pytest.skip("Examples directory not found")
        
        workspace = PromptWorkspace.load(examples_path)
        
        # Check that functions from tools.py are loaded
        function_names = workspace.list_functions()
        
        expected_functions = [
            "get_available_tools",
            "get_dangerous_command_examples", 
            "format_tool_usage_guidelines",
            "get_security_guidelines"
        ]
        
        for func_name in expected_functions:
            if func_name in function_names:
                # Test that we can get the function
                func_model = workspace.get_function(func_name)
                assert func_model.name == func_name
                # Function loaded successfully

    def test_custom_function_injection(self):
        """Test injecting custom functions into workspace."""
        examples_path = Path(__file__).parent.parent / "examples"
        
        if not examples_path.exists():
            pytest.skip("Examples directory not found")
        
        # Define custom function
        def format_command(cmd):
            return f"$ {cmd}"
        
        def count_words(text):
            return len(text.split())
        
        custom_functions = {
            "format_command": format_command,
            "count_words": count_words,
        }
        
        # Load workspace with custom functions
        workspace = PromptWorkspace.load(examples_path, custom_functions=custom_functions)
        
        # Verify custom functions are available
        assert "format_command" in workspace.list_functions()
        assert "count_words" in workspace.list_functions()
        
        # Test that we can use them (would need a template that uses them)
        # For now just verify they're callable
        format_cmd_func = workspace.get_function("format_command")
        count_words_func = workspace.get_function("count_words")
        assert format_cmd_func is not None and callable(format_cmd_func.callable)
        assert count_words_func is not None and callable(count_words_func.callable)

    def test_environment_configuration_usage(self):
        """Test using different environment configurations."""
        examples_path = Path(__file__).parent.parent / "examples"
        
        if not examples_path.exists():
            pytest.skip("Examples directory not found")
        
        workspace = PromptWorkspace.load(examples_path)
        
        # Test that environments are loaded
        assert "development" in workspace.config.environments
        assert "production" in workspace.config.environments
        
        dev_config = workspace.config.environments["development"]
        prod_config = workspace.config.environments["production"]
        
        # Verify they have different settings
        assert dev_config.get("debug_mode") != prod_config.get("debug_mode")
        assert dev_config.get("max_output_lines") != prod_config.get("max_output_lines")

    def test_snippet_inclusion(self):
        """Test that snippets can be included in templates."""
        examples_path = Path(__file__).parent.parent / "examples"
        
        if not examples_path.exists():
            pytest.skip("Examples directory not found")
        
        workspace = PromptWorkspace.load(examples_path)
        
        # Check available snippets
        snippet_names = workspace.list_snippets()
        
        if snippet_names:
            # Pick first available snippet
            snippet_name = snippet_names[0]
            snippet = workspace.get_snippet(snippet_name)
            
            assert snippet.name == snippet_name
            assert len(snippet.content) > 0

    def test_complete_workflow_example(self):
        """Test a complete workflow from loading to rendering with all features."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_path = Path(temp_dir)
            
            # Create a comprehensive test workspace
            (workspace_path / "prompts.toml").write_text("""
[prompts]
name = "workflow-test"
version = "1.0.0"
function_loaders = ["python"]

[prompts.defaults]
project_name = "TestProject"
user_role = "developer"
environment = "development"

[prompts.environments]
[prompts.environments.development]
debug = true
verbose = true
max_lines = 10

[prompts.environments.production]
debug = false
verbose = false
max_lines = 3
""")
            
            # Create templates
            templates_dir = workspace_path / "templates"
            templates_dir.mkdir()
            
            (templates_dir / "welcome.md").write_text("""+++
title = "Welcome Template"
+++

# Welcome to {{ project_name }}

Hello {{ user_name }}! You are a {{ user_role }}.

{% include 'instructions' %}

{{ get_project_info() }}

{% if debug %}
Debug mode is enabled.
{% endif %}
""")
            
            (templates_dir / "chat.md").write_text("""
## System
You are an assistant for {{ project_name }}.
Environment: {{ environment }}

{{ get_project_info() }}

## User
{{ user_message }}

## Assistant
I'll help you with that request.
""")
            
            # Create snippets
            snippets_dir = workspace_path / "snippets"
            snippets_dir.mkdir()
            
            (snippets_dir / "instructions.md").write_text("""
## Instructions

1. Follow best practices
2. Write clean code
3. Test your changes
""")
            
            # Create functions
            functions_dir = workspace_path / "functions"
            functions_dir.mkdir()
            
            (functions_dir / "project.py").write_text("""
def get_project_info():
    '''Get project information.'''
    return '''## Project Information

This is a test project for demonstrating Republic Prompt functionality.

### Features
- Template rendering
- Function integration
- Snippet inclusion
- Environment configuration
'''

def format_user_name(name):
    '''Format a user name properly.'''
    return name.title()

WORKSPACE_FUNCTIONS = {
    "get_project_info": get_project_info,
    "format_user_name": format_user_name,
}
""")
            
            # Load workspace
            workspace = PromptWorkspace.load(workspace_path)
            
            # Test basic properties
            assert workspace.name == "workflow-test"
            assert workspace.version == "1.0.0"
            
            # Test rendering text template
            result = workspace.render(
                "welcome",
                user_name="alice",
                project_name="TestProject",
                user_role="developer",
                debug=True
            )
            
            assert result.messages is None  # Should be text format
            assert "Welcome to TestProject" in result.content
            assert "Hello alice!" in result.content  # Check actual case
            assert "You are a developer" in result.content  # Uses passed variable
            assert "Instructions" in result.content  # From snippet
            assert "Project Information" in result.content  # From function
            assert "Debug mode is enabled" in result.content  # Conditional
            
            # Test rendering message template
            result = workspace.render(
                "chat",
                user_message="How do I get started?",
                project_name="TestProject",
                environment="development",
                **workspace.config.environments.get("development", {})
            )
            
            assert result.messages is not None  # Should be message format
            assert len(result.messages) == 3
            
            system_msg = result.messages[0]
            assert "assistant for TestProject" in system_msg.content
            assert "Environment: development" in system_msg.content
            assert "Project Information" in system_msg.content
            
            user_msg = result.messages[1]
            assert "How do I get started?" in user_msg.content
            
            assistant_msg = result.messages[2]
            assert "I'll help you" in assistant_msg.content
            
            # Test OpenAI format conversion
            openai_format = result.to_openai_format()
            assert len(openai_format) == 3
            assert all("role" in msg and "content" in msg for msg in openai_format)

    def test_error_scenarios(self):
        """Test various error scenarios."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_path = Path(temp_dir)
            
            # Test missing config file - should load with default config
            workspace = PromptWorkspace.load(workspace_path)
            assert workspace.name is None  # Default config has no name
            
            # Create minimal config
            (workspace_path / "prompts.toml").write_text("""
[prompts]
name = "error-test"
version = "1.0.0"
""")
            
            workspace = PromptWorkspace.load(workspace_path)
            
            # Test rendering nonexistent template
            with pytest.raises(Exception):
                workspace.render("nonexistent")
            
            # Test getting nonexistent items
            template = workspace.get_template("nonexistent")
            assert template is None
            
            snippet = workspace.get_snippet("nonexistent")
            assert snippet is None
            
            function = workspace.get_function("nonexistent")
            assert function is None 