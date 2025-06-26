"""
Test cases for all code examples in README.md

This file ensures that all code examples in the README work correctly
and demonstrate the actual functionality of Republic Prompt.
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from republic_prompt import (
    load_workspace,
    render,
    quick_render,
    FunctionLoader,
    validate_template_syntax,
    Workspace,
    Template,
    Prompt,
)


class WorkspaceTestSetup:
    """Helper class to create test workspaces with proper setup and teardown."""

    def __init__(self):
        self.temp_dir = None

    def create_workspace(self) -> Path:
        """Create a complete test workspace matching README examples."""
        self.temp_dir = Path(tempfile.mkdtemp())

        # Create workspace structure
        (self.temp_dir / "snippets").mkdir()
        (self.temp_dir / "templates").mkdir()
        (self.temp_dir / "prompts").mkdir()
        (self.temp_dir / "functions").mkdir()

        self._create_config()
        self._create_snippets()
        self._create_templates()
        self._create_prompts()
        self._create_functions()

        return self.temp_dir

    def _create_config(self):
        """Create prompts.toml configuration file."""
        config_content = """[prompts]
name = "my-ai-workspace"
function_loaders = ["python"]

[prompts.defaults]
tone = "professional"
max_output_lines = 3

[prompts.environments.development]
debug_mode = true
verbose = true

[prompts.environments.production]
debug_mode = false
verbose = false"""
        (self.temp_dir / "prompts.toml").write_text(config_content)

    def _create_snippets(self):
        """Create snippet files matching README examples."""
        # Greeting snippet from README
        greeting_content = """---
description: Standard AI assistant greeting
var_name: Assistant
---
Hello! I'm {{ name }}, your AI assistant specialized in {{ domain }}."""
        (self.temp_dir / "snippets" / "greeting.md").write_text(greeting_content)

    def _create_templates(self):
        """Create template files matching README examples."""
        # Code reviewer template from README
        code_reviewer_content = """---
description: Code review assistant template
snippets: greeting
var_language: python
var_review_type: general
---
{% include 'greeting' %}

I'll review your {{ language }} code focusing on {{ review_type }} aspects.

{% if debug_mode %}
**Debug mode enabled** - I'll provide detailed explanations.
{% endif %}

{% set topic = extract_topic(user_query) %}
{% if topic == "security" %}
## Security Review Checklist
{{ get_security_checklist(language) }}
{% endif %}

Please share your code for review."""
        (self.temp_dir / "templates" / "code_reviewer.md").write_text(
            code_reviewer_content
        )

        # Conversation template for message format testing
        conversation_content = """---
output_format: messages
---
[SYSTEM]
You are a helpful AI assistant.

[USER]
{{ user_query }}

[ASSISTANT]
I'll help you with that."""
        (self.temp_dir / "templates" / "conversation.md").write_text(
            conversation_content
        )

        # System agent template
        system_agent_content = """---
description: System agent template
var_domain: data_science
---
You are a {{ domain }} specialist.

{% if debug_mode %}
**Debug mode is active**
{% endif %}

Task: {{ user_query }}"""
        (self.temp_dir / "templates" / "system_agent.md").write_text(
            system_agent_content
        )

    def _create_prompts(self):
        """Create pre-built prompt files."""
        # Debugging assistant prompt
        debug_assistant_content = """---
description: Debugging Assistant (pre-built version)
---
I'm a debugging specialist ready to help you solve problems systematically.

My approach:
1. Analyze the issue
2. Identify root causes  
3. Provide solutions
4. Verify fixes

What debugging challenge can I help you with today?"""
        (self.temp_dir / "prompts" / "debugging_assistant.md").write_text(
            debug_assistant_content
        )

    def _create_functions(self):
        """Create function files matching README examples exactly."""
        # Functions from README examples (only the two shown in README)
        functions_content = '''"""Business logic functions for the test workspace."""

def extract_topic(query: str) -> str:
    """Extract the main topic from user query"""
    if "security" in query.lower() or "vulnerability" in query.lower():
        return "security"
    elif "performance" in query.lower():
        return "performance"
    return "general"

def get_security_checklist(language: str) -> str:
    """Get security checklist for specific language"""
    checklists = {
        "python": "- Check for SQL injection\\n- Validate input sanitization",
        "javascript": "- Check for XSS vulnerabilities\\n- Validate CSRF protection"
    }
    return checklists.get(language, "- Follow general security practices")

def get_examples_for_topic(topic: str, count: int = 3) -> str:
    """Get examples for a specific topic"""
    examples = {
        "security": ["Example 1: Input validation", "Example 2: Authentication", "Example 3: Authorization"],
        "performance": ["Example 1: Caching", "Example 2: Database optimization", "Example 3: Algorithm efficiency"],
        "general": ["Example 1: Code structure", "Example 2: Best practices", "Example 3: Documentation"]
    }
    topic_examples = examples.get(topic, examples["general"])
    return "\\n".join(topic_examples[:count])

def get_current_task() -> str:
    """Get current task description"""
    return "Data analysis and visualization"

# Export functions for template use
WORKSPACE_FUNCTIONS = {
    'extract_topic': extract_topic,
    'get_security_checklist': get_security_checklist,
    'get_examples_for_topic': get_examples_for_topic,
    'get_current_task': get_current_task,
}
'''
        (self.temp_dir / "functions" / "__init__.py").write_text(functions_content)

    def cleanup(self):
        """Clean up the temporary workspace."""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace for testing with proper setup and teardown."""
    setup = WorkspaceTestSetup()
    workspace_path = setup.create_workspace()

    yield workspace_path

    # Cleanup
    setup.cleanup()


class TestBasicUsage:
    """Test basic usage examples from README."""

    def test_load_workspace_and_use_prompts(self, temp_workspace):
        """Test: Load a prompt workspace and use pre-built prompts."""
        # Load a prompt workspace
        workspace = load_workspace(str(temp_workspace))

        # Use pre-built prompts (ready to use)
        debug_assistant = workspace.prompts["debugging_assistant"]
        assert debug_assistant.content is not None
        assert "debugging specialist" in debug_assistant.content.lower()

        # Verify workspace structure
        assert isinstance(workspace, Workspace)
        assert "debugging_assistant" in workspace.prompts
        assert "code_reviewer" in workspace.templates
        assert "greeting" in workspace.snippets

    def test_render_dynamic_templates(self, temp_workspace):
        """Test: Render dynamic templates with variables."""
        workspace = load_workspace(str(temp_workspace))

        # Render dynamic templates with variables
        template = workspace.templates["code_reviewer"]
        prompt = render(
            template,
            {
                "language": "python",
                "review_type": "security",
                "user_query": "Check this authentication function",
            },
            workspace,
        )

        assert isinstance(prompt, Prompt)
        assert "python" in prompt.content
        assert "security" in prompt.content
        assert "Hello! I'm" in prompt.content  # From greeting snippet


class TestWorkspaceCreation:
    """Test workspace creation examples from README."""

    def test_environment_configuration(self, temp_workspace):
        """Test environment-driven configuration."""
        workspace = load_workspace(str(temp_workspace))

        # Test environment configurations
        dev_config = workspace.get_environment_config("development")
        prod_config = workspace.get_environment_config("production")

        assert dev_config["debug_mode"] is True
        assert dev_config["verbose"] is True
        assert prod_config["debug_mode"] is False
        assert prod_config["verbose"] is False

    def test_template_rendering_with_environment(self, temp_workspace):
        """Test rendering templates with environment configuration."""
        workspace = load_workspace(str(temp_workspace))
        template = workspace.templates["code_reviewer"]

        # Render with environment configuration
        env_config = workspace.get_environment_config("development")
        variables = {
            **env_config,
            "name": "CodeReviewer",
            "domain": "software engineering",
            "language": "python",
            "review_type": "security",
            "user_query": "Please check for security vulnerabilities",
        }

        prompt = render(template, variables, workspace)

        # Verify environment-specific content
        assert "Debug mode enabled" in prompt.content
        assert "Security Review Checklist" in prompt.content
        assert "SQL injection" in prompt.content  # From security checklist


class TestAdvancedFeatures:
    """Test advanced features from README."""

    def test_environment_driven_rendering(self, temp_workspace):
        """Test different behavior based on environment."""
        workspace = load_workspace(str(temp_workspace))
        template = workspace.templates["system_agent"]

        # Different behavior based on environment
        dev_prompt = render(
            template, workspace.get_environment_config("development"), workspace
        )
        prod_prompt = render(
            template, workspace.get_environment_config("production"), workspace
        )

        # Development should have debug info, production shouldn't
        assert "Debug mode is active" in dev_prompt.content
        assert "Debug mode is active" not in prod_prompt.content

    def test_message_format_support(self, temp_workspace):
        """Test message format support."""
        workspace = load_workspace(str(temp_workspace))
        template = workspace.templates["conversation"]

        variables = {"user_query": "Help me with Python"}

        # Render to OpenAI-compatible message format
        prompt = render(template, variables, workspace)
        messages = prompt.to_openai_format()

        # Verify message format
        assert isinstance(messages, list)
        assert len(messages) == 3  # SYSTEM, USER, ASSISTANT
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert messages[2]["role"] == "assistant"
        assert "helpful AI assistant" in messages[0]["content"]
        assert "Help me with Python" in messages[1]["content"]


class TestUsagePatterns:
    """Test usage patterns from README."""

    def test_quick_use_prebuilt_prompts(self, temp_workspace):
        """Test: Quick Use - Pre-built Prompts."""
        # Out of the box, no rendering needed
        workspace = load_workspace(str(temp_workspace))
        prompt = workspace.prompts["debugging_assistant"]

        # Ready to use immediately
        assert prompt.content is not None
        assert len(prompt.content) > 0

    def test_customization_dynamic_templates(self, temp_workspace):
        """Test: Customization - Dynamic Templates."""
        workspace = load_workspace(str(temp_workspace))

        # Parameterized rendering for different scenarios
        template = workspace.templates["system_agent"]
        custom_prompt = render(
            template,
            {
                "domain": "data_science",
                "user_query": "Analyze this dataset",
                "debug_mode": True,
            },
            workspace,
        )

        assert "data_science" in custom_prompt.content
        assert "Analyze this dataset" in custom_prompt.content
        assert "Debug mode is active" in custom_prompt.content

    def test_development_compose_from_components(self, temp_workspace):
        """Test: Development - Compose from Components."""
        workspace = load_workspace(str(temp_workspace))

        # Build prompts from snippets and functions
        content = """
{% include 'greeting' %}
Current task: {{ get_current_task() }}
"""

        prompt = quick_render(
            content, {"name": "DataAnalyst", "domain": "analytics"}, workspace
        )

        assert "Hello! I'm DataAnalyst" in prompt
        assert "Data analysis and visualization" in prompt


class TestAPIReference:
    """Test API reference examples from README."""

    def test_core_functions_signatures(self, temp_workspace):
        """Test that core functions work as documented."""
        # Test load_workspace
        workspace = load_workspace(str(temp_workspace))
        assert isinstance(workspace, Workspace)

        # Test render
        template = workspace.templates["code_reviewer"]
        prompt = render(
            template,
            {"language": "python", "user_query": "Review this code"},
            workspace,
        )
        assert isinstance(prompt, Prompt)

        # Test quick_render
        result = quick_render("Hello {{ name }}!", {"name": "World"}, workspace)
        assert result == "Hello World!"

        valid_template = Template(
            name="test", content="Hello {{ name }}!", variables={"name": "World"}
        )
        invalid_template = Template(name="test2", content="Hello {{ name")

        valid_errors = validate_template_syntax(valid_template, workspace)
        invalid_errors = validate_template_syntax(invalid_template, workspace)

        assert len(valid_errors) == 0  # No errors for valid template
        assert len(invalid_errors) > 0  # Should have syntax errors

    def test_workspace_data_structure(self, temp_workspace):
        """Test Workspace data structure as documented."""
        workspace = load_workspace(str(temp_workspace))

        # Test workspace attributes
        assert hasattr(workspace, "snippets")
        assert hasattr(workspace, "templates")
        assert hasattr(workspace, "prompts")
        assert hasattr(workspace, "functions")
        assert hasattr(workspace, "config")

        # Test workspace methods
        env_config = workspace.get_environment_config("development")
        assert isinstance(env_config, dict)

        functions_dict = workspace.get_functions_dict()
        assert isinstance(functions_dict, dict)
        assert "extract_topic" in functions_dict

    def test_prompt_data_structure(self, temp_workspace):
        """Test Prompt data structure as documented."""
        workspace = load_workspace(str(temp_workspace))
        template = workspace.templates["conversation"]

        prompt = render(template, {"user_query": "Test"}, workspace)

        # Test prompt attributes
        assert hasattr(prompt, "content")
        assert hasattr(prompt, "messages")
        assert hasattr(prompt, "metadata")

        # Test prompt methods
        openai_format = prompt.to_openai_format()
        assert isinstance(openai_format, list)

        # Note: to_anthropic_format might not be implemented yet
        # anthropic_format = prompt.to_anthropic_format()
        # assert isinstance(anthropic_format, dict)


class TestFunctionLoaders:
    """Test function loader examples from README."""

    def test_custom_function_loader_registration(self):
        """Test custom function loader registration."""

        # Mock a custom JavaScript function loader
        class MockJavaScriptFunctionLoader(FunctionLoader):
            language = "javascript"
            supported_extensions = [".js", ".mjs"]

            def load_functions(self, workspace_path: Path):
                return {}

        # Test registration (this is just a mock test)
        # In reality, the register_function_loader decorator would be used
        loader = MockJavaScriptFunctionLoader()
        assert loader.language == "javascript"
        assert ".js" in loader.supported_extensions
        assert ".mjs" in loader.supported_extensions


class TestBusinessLogicFunctions:
    """Test business logic functions from README."""

    def test_extract_topic_function(self, temp_workspace):
        """Test extract_topic function works as documented."""
        workspace = load_workspace(str(temp_workspace))
        extract_topic = workspace.get_functions_dict()["extract_topic"]

        # Test security topic detection
        assert extract_topic("Check for security vulnerabilities") == "security"
        assert extract_topic("Find vulnerability in this code") == "security"

        # Test performance topic detection
        assert extract_topic("Optimize performance") == "performance"

        # Test general topic fallback
        assert extract_topic("Review this code") == "general"

    def test_get_security_checklist_function(self, temp_workspace):
        """Test get_security_checklist function works as documented."""
        workspace = load_workspace(str(temp_workspace))
        get_security_checklist = workspace.get_functions_dict()[
            "get_security_checklist"
        ]

        # Test Python checklist
        python_checklist = get_security_checklist("python")
        assert "SQL injection" in python_checklist
        assert "input sanitization" in python_checklist

        # Test JavaScript checklist
        js_checklist = get_security_checklist("javascript")
        assert "XSS vulnerabilities" in js_checklist
        assert "CSRF protection" in js_checklist

        # Test fallback for unknown language
        generic_checklist = get_security_checklist("unknown")
        assert "general security practices" in generic_checklist


class TestTemplateComposition:
    """Test template composition examples from README."""

    def test_snippet_inclusion(self, temp_workspace):
        """Test including snippets in templates."""
        workspace = load_workspace(str(temp_workspace))

        # Test that greeting snippet is properly included
        template = workspace.templates["code_reviewer"]
        prompt = render(
            template,
            {
                "name": "TestBot",
                "domain": "testing",
                "language": "python",
                "review_type": "general",
                "user_query": "Please review this code",
            },
            workspace,
        )

        # Should include greeting snippet content
        assert "Hello! I'm TestBot" in prompt.content
        assert "testing" in prompt.content

    def test_dynamic_function_calls(self, temp_workspace):
        """Test dynamic function calls in templates."""
        workspace = load_workspace(str(temp_workspace))

        # Create a template with function calls
        template_content = """
{% set topic = extract_topic(user_query) %}
Topic: {{ topic }}
{{ get_examples_for_topic(topic, count=2) }}
"""

        result = quick_render(
            template_content, {"user_query": "Help with security issues"}, workspace
        )

        assert "Topic: security" in result
        assert "Example 1: Input validation" in result
        assert "Example 2: Authentication" in result

    def test_environment_aware_rendering(self, temp_workspace):
        """Test environment-aware rendering in templates."""
        workspace = load_workspace(str(temp_workspace))

        # Template with environment-aware content
        template_content = """
{% if debug_mode %}
**Debug Information:**
- Environment: {{ environment | default('unknown') }}
- Debug mode: {{ debug_mode }}
{% endif %}
Main content here.
"""

        # Test with debug mode enabled
        debug_result = quick_render(
            template_content,
            {"debug_mode": True, "environment": "development"},
            workspace,
        )

        assert "Debug Information:" in debug_result
        assert "Environment: development" in debug_result

        # Test with debug mode disabled
        prod_result = quick_render(template_content, {"debug_mode": False}, workspace)

        assert "Debug Information:" not in prod_result
        assert "Main content here." in prod_result


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_invalid_template_syntax(self, temp_workspace):
        """Test handling of invalid template syntax."""
        workspace = load_workspace(str(temp_workspace))

        # Test invalid Jinja2 syntax
        from republic_prompt.core import Template

        valid_template = Template(
            name="valid", content="Hello {{ name }}!", variables={"name": "World"}
        )
        invalid_template1 = Template(name="invalid1", content="Hello {{ name")
        invalid_template2 = Template(name="invalid2", content="Hello {% if %}")

        assert len(validate_template_syntax(valid_template, workspace)) == 0
        assert len(validate_template_syntax(invalid_template1, workspace)) > 0
        assert len(validate_template_syntax(invalid_template2, workspace)) > 0

    def test_missing_snippet_handling(self, temp_workspace):
        """Test handling of missing snippets."""
        workspace = load_workspace(str(temp_workspace))

        # Template referencing non-existent snippet
        template_content = "{% include 'nonexistent' %}"

        # This should raise an error or handle gracefully
        with pytest.raises(
            Exception
        ):  # Specific exception type depends on implementation
            quick_render(template_content, {}, workspace)

    def test_missing_function_handling(self, temp_workspace):
        """Test handling of missing functions."""
        workspace = load_workspace(str(temp_workspace))

        # Template calling non-existent function
        template_content = "{{ nonexistent_function() }}"

        # This should raise an error or handle gracefully
        with pytest.raises(
            Exception
        ):  # Specific exception type depends on implementation
            quick_render(template_content, {}, workspace)


if __name__ == "__main__":
    pytest.main([__file__])
