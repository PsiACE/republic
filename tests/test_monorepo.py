import tempfile
from pathlib import Path
from republic_prompt import load_workspace, quick_render


def test_basic_workspace_usage():
    """Test basic workspace functionality with a minimal example."""
    # Create a temporary workspace
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_path = Path(temp_dir)

        # Create minimal workspace structure
        (workspace_path / "prompts.toml").write_text("""
name = "test-workspace"
description = "Test workspace for monorepo testing"
""")

        # Create a simple template
        templates_dir = workspace_path / "templates"
        templates_dir.mkdir()
        (templates_dir / "simple.md").write_text("""---
description: Simple greeting template
greeting: Hello
---
{{ greeting }}, {{ name }}! Welcome to the workspace.
""")

        # Load workspace and render template
        workspace = load_workspace(workspace_path)
        
        # Render the template
        result = workspace.render("simple", name="John")

        assert "Hello, John!" in result.content
        assert "Welcome to the workspace" in result.content


def test_workspace_with_snippets():
    """Test workspace functionality with snippets."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_path = Path(temp_dir)

        # Create workspace config
        (workspace_path / "prompts.toml").write_text("""
name = "snippet-workspace"
description = "Test workspace with snippets"
""")

        # Create snippets
        snippets_dir = workspace_path / "snippets"
        snippets_dir.mkdir()
        (snippets_dir / "greeting.md").write_text("""---
description: Friendly greeting snippet
---
Hello! I'm your AI assistant.
""")

        # Create template that uses snippet
        templates_dir = workspace_path / "templates"
        templates_dir.mkdir()
        (templates_dir / "agent.md").write_text("""---
description: Agent template with snippet inclusion
snippets: greeting
---
{% include 'greeting' %}

How can I help you with {{ domain }} today?
""")

        # Load and render
        workspace = load_workspace(workspace_path)
        result = workspace.render("agent", domain="coding")

        assert "Hello! I'm your AI assistant." in result.content
        assert "How can I help you with coding today?" in result.content


def test_quick_render_functionality():
    """Test the quick_render convenience function."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_path = Path(temp_dir)

        # Create workspace config
        (workspace_path / "prompts.toml").write_text("""
name = "quick-test-workspace"
description = "Test workspace for quick render"
""")

        # Create template
        templates_dir = workspace_path / "templates"
        templates_dir.mkdir()
        (templates_dir / "quick.md").write_text("""---
description: Quick test template
---
Quick test: {{ message }}
""")

        # Use quick_render
        result = quick_render(workspace_path, "quick", message="It works!")

        assert "Quick test: It works!" in result.content


def test_workspace_with_custom_functions():
    """Test workspace with custom functions."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_path = Path(temp_dir)

        # Create workspace config
        (workspace_path / "prompts.toml").write_text("""
name = "custom-functions-workspace"
description = "Test workspace with custom functions"
""")

        # Create template
        templates_dir = workspace_path / "templates"
        templates_dir.mkdir()
        (templates_dir / "with_function.md").write_text("""---
description: Template with custom function
---
Original: {{ text }}
Processed: {{ custom_upper(text) }}
""")

        # Load workspace with custom function
        def custom_upper(text):
            return text.upper()

        workspace = load_workspace(
            workspace_path,
            custom_functions={"custom_upper": custom_upper}
        )
        
        result = workspace.render("with_function", text="hello world")

        assert "Original: hello world" in result.content
        assert "Processed: HELLO WORLD" in result.content


def test_workspace_info_and_properties():
    """Test workspace information and properties."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_path = Path(temp_dir)

        # Create workspace config
        (workspace_path / "prompts.toml").write_text("""
name = "info-test-workspace"
description = "Test workspace for info testing"
version = "1.0.0"
""")

        # Create some content
        templates_dir = workspace_path / "templates"
        templates_dir.mkdir()
        (templates_dir / "test.md").write_text("""---
description: Test template
---
Test content
""")

        snippets_dir = workspace_path / "snippets"
        snippets_dir.mkdir()
        (snippets_dir / "test_snippet.md").write_text("""---
description: Test snippet
---
Test snippet content
""")

        # Load workspace
        workspace = load_workspace(workspace_path)

        # Test properties
        assert workspace.name == "info-test-workspace"
        assert workspace.description == "Test workspace for info testing"
        assert workspace.version == "1.0.0"

        # Test listing methods
        assert "test" in workspace.list_templates()
        assert "test_snippet" in workspace.list_snippets()

        # Test info method
        info = workspace.info()
        assert info["name"] == "info-test-workspace"
        assert info["templates"] >= 1
        assert info["snippets"] >= 1
