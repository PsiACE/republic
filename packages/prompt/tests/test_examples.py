"""Test cases for the examples workspace to validate the complete architecture."""

import pytest

from pathlib import Path
from republic_prompt import (
    load_workspace,
    render,
    MessageRole,
    PromptMessage,
    parse_message_blocks,
)
from republic_prompt.core import Template, Snippet, Function


# Test workspace loading
def test_examples_workspace_loading():
    """Test that the examples workspace loads correctly with all components."""
    examples_path = Path(__file__).parent.parent / "examples"

    # Load the workspace
    workspace = load_workspace(examples_path)

    # Basic workspace properties
    assert workspace.name == "gemini-cli-agent"
    assert (
        workspace.config.description
        == "Gemini CLI agent workspace demonstrating complex system prompt management"
    )
    assert workspace.config.version == "1.0.0"

    # Check that all directories are loaded
    assert len(workspace.snippets) > 0, "Should have snippets loaded"
    assert len(workspace.templates) > 0, "Should have templates loaded"
    assert len(workspace.prompts) > 0, "Should have prompts loaded"
    assert len(workspace.functions) > 0, "Should have functions loaded"


def test_prompts_config_loading():
    """Test that prompts.toml is loaded correctly."""
    examples_path = Path(__file__).parent.parent / "examples"
    workspace = load_workspace(examples_path)

    config = workspace.config

    # Check basic config
    assert config.name == "gemini-cli-agent"
    assert "development" in config.environments
    assert "production" in config.environments
    assert "sandbox" in config.environments

    # Check defaults
    defaults = config.defaults
    assert defaults["agent_type"] == "cli_agent"
    assert defaults["domain"] == "software_engineering"
    assert defaults["tone"] == "concise_direct"
    assert defaults["max_output_lines"] == 3

    # Check environment configurations
    dev_env = config.environments["development"]
    assert dev_env["debug_mode"] is True
    assert dev_env["max_output_lines"] == 8

    prod_env = config.environments["production"]
    assert prod_env["debug_mode"] is False
    assert prod_env["max_output_lines"] == 2


def test_snippets_loading():
    """Test that all snippets are loaded correctly."""
    examples_path = Path(__file__).parent.parent / "examples"
    workspace = load_workspace(examples_path)

    # Check expected snippets
    expected_snippets = [
        "core_mandates",
        "tone_guidelines",
        "environment_detection",
        "examples",
    ]

    for snippet_name in expected_snippets:
        assert snippet_name in workspace.snippets, f"Missing snippet: {snippet_name}"
        snippet = workspace.snippets[snippet_name]
        assert isinstance(snippet, Snippet)
        assert snippet.content.strip(), f"Snippet {snippet_name} should have content"


def test_templates_loading():
    """Test that templates are loaded correctly."""
    examples_path = Path(__file__).parent.parent / "examples"
    workspace = load_workspace(examples_path)

    # Check expected templates
    expected_templates = ["gemini_cli_system_prompt", "simple_agent"]

    for template_name in expected_templates:
        assert template_name in workspace.templates, (
            f"Missing template: {template_name}"
        )
        template = workspace.templates[template_name]
        assert isinstance(template, Template)
        assert template.content.strip(), f"Template {template_name} should have content"


def test_prompts_loading():
    """Test that pre-built prompts are loaded correctly."""
    examples_path = Path(__file__).parent.parent / "examples"
    workspace = load_workspace(examples_path)

    # Check expected prompts (3 core variants)
    expected_prompts = ["full_cli_system", "basic_cli_system", "simple_agent"]

    for prompt_name in expected_prompts:
        assert prompt_name in workspace.prompts, f"Missing prompt: {prompt_name}"
        prompt = workspace.prompts[prompt_name]
        assert isinstance(prompt, Template)  # Prompts are stored as templates
        assert prompt.content.strip(), f"Prompt {prompt_name} should have content"

        # Check metadata
        assert prompt.description, f"Prompt {prompt_name} should have description"

        # Pre-built prompts should have source template info
        if "source_template" in prompt.metadata:
            source = prompt.metadata["source_template"]
            assert source in ["gemini_cli_system_prompt", "simple_agent"], (
                f"Invalid source template: {source}"
            )


def test_functions_loading():
    """Test that functions are loaded correctly."""
    examples_path = Path(__file__).parent.parent / "examples"
    workspace = load_workspace(examples_path)

    # Check that functions are loaded
    assert len(workspace.functions) > 0, "Should have functions loaded"

    # Check expected function categories
    expected_functions = [
        # From environment.py
        "get_sandbox_status",
        "is_git_repository",
        "get_git_workflow_instructions",
        "detect_sandbox_environment",
        "detect_git_repository",
        "get_environment_summary",
        "should_show_git_warning",
        "should_show_sandbox_warning",
        "get_sandbox_warning_message",
        # From tools.py
        "should_explain_command",
        "get_security_guidelines",
        "format_tool_usage_guidelines",
        "get_available_tools",
        # From workflows.py
        "get_software_engineering_workflow",
        "get_new_application_workflow",
        "format_workflow_reminder",
    ]

    for func_name in expected_functions:
        assert func_name in workspace.functions, f"Missing function: {func_name}"
        func = workspace.functions[func_name]
        assert isinstance(func, Function)
        assert func.language == "python"
        assert callable(func.callable), f"Function {func_name} should be callable"


def test_template_rendering():
    """Test that templates can be rendered correctly."""
    examples_path = Path(__file__).parent.parent / "examples"
    workspace = load_workspace(examples_path)

    # Test Google system prompt template
    template = workspace.templates["gemini_cli_system_prompt"]

    # Render with custom variables
    prompt = render(
        template,
        {
            "domain": "data_science",
            "max_output_lines": 7,
            "user_memory": "User prefers Python over R",
        },
        workspace,
    )

    # Check that rendering worked
    assert "data_science" in prompt.content
    assert "User prefers Python over R" in prompt.content

    # Check that snippets were included
    assert "Core Mandates" in prompt.content  # From core_mandates
    assert "Concise" in prompt.content  # From tone_guidelines

    # Check that functions were called
    assert (
        "Software Engineering Workflow" in prompt.content
    )  # From get_software_engineering_workflow()


def test_simple_template_rendering():
    """Test simple agent template rendering."""
    examples_path = Path(__file__).parent.parent / "examples"
    workspace = load_workspace(examples_path)

    template = workspace.templates["simple_agent"]
    prompt = render(template, {"domain": "general_assistance"}, workspace)

    # Check basic rendering
    assert "general_assistance" in prompt.content
    assert "Core Mandates" in prompt.content  # From core_mandates
    assert "Ready to help!" in prompt.content


def test_prebuilt_prompts_usage():
    """Test that pre-built prompts can be used directly."""
    examples_path = Path(__file__).parent.parent / "examples"
    workspace = load_workspace(examples_path)

    # Test full CLI system prompt
    full_cli = workspace.prompts["full_cli_system"]
    content = full_cli.content

    # Should be already rendered and ready to use
    assert "software_engineering" in content
    assert "interactive CLI agent" in content  # Check for actual content
    assert "specializing in" in content
    assert "Core Mandates" in content
    assert "Software Engineering Workflow" in content

    # Test basic CLI system prompt
    basic_cli = workspace.prompts["basic_cli_system"]
    content = basic_cli.content

    assert "general_assistance" in content
    assert "interactive CLI agent" in content
    assert "Core Mandates" in content
    # Should have fewer output lines than full version
    assert "2 lines of text output" in content

    # Test simple agent
    simple_agent = workspace.prompts["simple_agent"]
    content = simple_agent.content

    assert "general_assistance" in content
    assert "Ready to help!" in content
    # Simple agent doesn't include Core Mandates since use_tools is false
    assert "Tone and Style" in content


def test_environment_configurations():
    """Test that environment configurations work correctly."""
    examples_path = Path(__file__).parent.parent / "examples"

    # Load with development environment
    workspace_dev = load_workspace(examples_path, environment="development")
    template = workspace_dev.templates["gemini_cli_system_prompt"]

    # Development should have debug settings
    assert template.variables.get("debug_mode") is True
    # Note: max_output_lines might be string from TOML parsing
    max_output_lines = template.variables.get("max_output_lines")
    assert int(max_output_lines) == 8

    # Load with production environment
    workspace_prod = load_workspace(examples_path, environment="production")
    template = workspace_prod.templates["gemini_cli_system_prompt"]

    # Production should have minimal settings
    assert template.variables.get("debug_mode") is False
    # Note: max_output_lines might be string from TOML parsing
    max_output_lines = template.variables.get("max_output_lines")
    assert int(max_output_lines) == 2


def test_function_calls_in_templates():
    """Test that functions are called correctly in templates."""
    examples_path = Path(__file__).parent.parent / "examples"
    workspace = load_workspace(examples_path)

    # Test individual function calls
    sandbox_status = workspace.functions["get_sandbox_status"].callable()
    assert sandbox_status in ["macos_seatbelt", "generic_sandbox", "no_sandbox"]

    git_status = workspace.functions["is_git_repository"].callable()
    assert isinstance(git_status, bool)

    # Test command safety check
    should_explain = workspace.functions["should_explain_command"].callable
    assert should_explain("rm -rf /") is True  # Dangerous command
    assert should_explain("ls -la") is False  # Safe command

    # Test workflow generation
    workflow = workspace.functions["get_software_engineering_workflow"].callable()
    assert "Understand" in workflow
    assert "Plan" in workflow
    assert "Implement" in workflow


def test_workspace_validation():
    """Test that workspace validation works correctly."""
    examples_path = Path(__file__).parent.parent / "examples"
    workspace = load_workspace(examples_path)

    # Should not have missing snippet references
    missing_snippets = workspace.validate_snippet_references()
    assert len(missing_snippets) == 0, f"Missing snippets: {missing_snippets}"


def test_workspace_contents_summary():
    """Test workspace contents summary for debugging."""
    examples_path = Path(__file__).parent.parent / "examples"
    workspace = load_workspace(examples_path)

    from republic_prompt.loader import list_workspace_contents

    contents = list_workspace_contents(workspace)

    # Check summary structure
    assert contents["name"] == "gemini-cli-agent"
    assert "counts" in contents
    assert "snippets" in contents
    assert "templates" in contents
    assert "prompts" in contents
    assert "functions" in contents

    # Check counts
    counts = contents["counts"]
    assert counts["snippets"] >= 4
    assert counts["templates"] >= 2
    assert counts["prompts"] == 3  # Exactly 3 core prompts
    assert counts["functions"] >= 9


def test_directory_roles_demonstration():
    """Test that each directory serves its intended role."""
    examples_path = Path(__file__).parent.parent / "examples"
    workspace = load_workspace(examples_path)

    # 1. Snippets should be small, reusable components
    for name, snippet in workspace.snippets.items():
        assert len(snippet.content.split("\n")) < 50, f"Snippet {name} should be small"
        assert snippet.description, f"Snippet {name} should have description"

    # 2. Templates should require variables and use snippets
    for name, template in workspace.templates.items():
        # Should have Jinja2 syntax
        content = template.content
        has_jinja = "{{" in content or "{%" in content
        assert has_jinja, f"Template {name} should have Jinja2 syntax"

        # Should reference snippets
        if template.snippets:
            for snippet_name in template.snippets:
                assert snippet_name in workspace.snippets, (
                    f"Template {name} references missing snippet {snippet_name}"
                )

    # 3. Prompts should be ready-to-use (minimal variables needed)
    for name, prompt in workspace.prompts.items():
        # Should have metadata indicating it's pre-built
        assert prompt.description, f"Prompt {name} should have description"

        # Content should be substantial (already rendered)
        # Simple agent is intentionally lightweight
        min_length = 500 if name == "simple_agent" else 1000
        assert len(prompt.content) > min_length, f"Prompt {name} should be substantial (got {len(prompt.content)}, expected > {min_length})"

    # 4. Functions should be callable and documented
    for name, func in workspace.functions.items():
        assert callable(func.callable), f"Function {name} should be callable"
        assert func.language == "python", f"Function {name} should have language"
        assert func.source_file, f"Function {name} should have source file"


def test_custom_message_roles():
    """Test that custom message roles work correctly."""
    # Test standard roles still work
    msg1 = PromptMessage(role="system", content="System message")
    assert msg1.role == "system"

    # Test custom roles work
    msg2 = PromptMessage(role="DEVELOPER", content="Developer message")
    assert msg2.role == "developer"  # Should be normalized to lowercase

    msg3 = PromptMessage(role="Custom_Role", content="Custom message")
    assert msg3.role == "custom_role"  # Should be normalized

    # Test role normalization
    assert MessageRole.normalize("  SYSTEM  ") == "system"
    assert MessageRole.normalize("Custom_Role") == "custom_role"

    # Test standard role checking
    assert MessageRole.is_standard("system")
    assert MessageRole.is_standard("USER")
    assert not MessageRole.is_standard("custom_role")

    # Test parsing custom roles from message blocks
    content = """
[SYSTEM]
System prompt

[DEVELOPER] Alice
Developer instructions

[CUSTOM_ROLE] Bob
Custom role message

[USER]
User query
"""

    messages = parse_message_blocks(content)
    assert len(messages) == 4

    assert messages[0].role == "system"
    assert messages[0].name is None

    assert messages[1].role == "developer"
    assert messages[1].name == "Alice"

    assert messages[2].role == "custom_role"
    assert messages[2].name == "Bob"

    assert messages[3].role == "user"
    assert messages[3].name is None


if __name__ == "__main__":
    pytest.main([__file__])
