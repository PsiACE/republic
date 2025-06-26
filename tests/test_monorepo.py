import tempfile
from pathlib import Path
from republic.prompt import load_workspace, render


def test_basic_workspace_usage():
    """Test basic workspace functionality with a minimal example."""
    # Create a temporary workspace
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_path = Path(temp_dir)

        # Create minimal workspace structure
        (workspace_path / "prompts.toml").write_text("""
[prompts]
name = "test-workspace"
function_loaders = []

[prompts.defaults]
greeting = "Hello"
""")

        # Create a simple template
        templates_dir = workspace_path / "templates"
        templates_dir.mkdir()
        (templates_dir / "simple.md").write_text("""
{{ greeting }}, {{ name }}! Welcome to the workspace.
""")

        # Load workspace and render template
        workspace = load_workspace(workspace_path)
        template = workspace.templates["simple"]

        # Render the template
        prompt = render(template, {"name": "John"}, workspace)

        assert "Hello, John!" in prompt.content
        assert "Welcome to the workspace" in prompt.content


def test_workspace_with_snippets():
    """Test workspace functionality with snippets."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_path = Path(temp_dir)

        # Create workspace config
        (workspace_path / "prompts.toml").write_text("""
[prompts]
name = "snippet-workspace"
function_loaders = []
""")

        # Create snippets
        snippets_dir = workspace_path / "snippets"
        snippets_dir.mkdir()
        (snippets_dir / "greeting.md").write_text("""
Hello! I'm your AI assistant.
""")

        # Create template that uses snippet
        templates_dir = workspace_path / "templates"
        templates_dir.mkdir()
        (templates_dir / "agent.md").write_text("""
---
snippets: greeting
---
{% include 'greeting' %}

How can I help you with {{ domain }} today?
""")

        # Load and render
        workspace = load_workspace(workspace_path)
        template = workspace.templates["agent"]
        prompt = render(template, {"domain": "coding"}, workspace)

        assert "Hello! I'm your AI assistant." in prompt.content
        assert "How can I help you with coding today?" in prompt.content
