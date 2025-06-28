# tests/test_readme.py
import tempfile
from pathlib import Path

from republic_prompt import quick_render, load_workspace

def test_readme_quick_start_example():
    """Verify the Quick Start example from README.md works."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_path = Path(temp_dir)
        templates_dir = workspace_path / "templates"
        templates_dir.mkdir()

        (templates_dir / "greeting.md").write_text(
            """---
message: "Hello from Republic Prompt!"
---
{{ message }} - You are asking about {{ topic }}."""
        )

        # This call must match the README
        result = quick_render(workspace_path, "greeting", topic="Python")
        
        expected_output = "Hello from Republic Prompt! - You are asking about Python."
        assert result.content.strip() == expected_output

def test_readme_workspace_structure_and_yaml_template():
    """Verify workspace structure and YAML template example from README.md (Features 1 & 2)."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_path = Path(temp_dir)
        templates_dir = workspace_path / "templates"
        templates_dir.mkdir()

        # This template example is from "2. Powerful Templates" in the README
        (templates_dir / "agent_prompt.md").write_text(
            """---
description: "A friendly and helpful AI agent."
agent_name: "Republic Assistant"
---
You are **{{ agent_name }}**."""
        )
        workspace = load_workspace(workspace_path)
        result = workspace.render("agent_prompt")
        assert "You are **Republic Assistant**." in result.content.strip()

def test_readme_snippet_inclusion_example():
    """Verify snippet inclusion example from README.md (Feature 3)."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_path = Path(temp_dir)
        
        # Create a template that includes a snippet
        templates_dir = workspace_path / "templates"
        templates_dir.mkdir()
        (templates_dir / "main.md").write_text("Rules: {% include 'rules' %}")

        # Create the snippet as described in the README
        snippets_dir = workspace_path / "snippets"
        snippets_dir.mkdir()
        (snippets_dir / "rules.md").write_text(
            """Your core rules are:
1. Be helpful and harmless.
2. Provide accurate information."""
        )

        workspace = load_workspace(workspace_path)
        result = workspace.render("main")
        assert "Your core rules are:" in result.content
        assert "Be helpful and harmless" in result.content

def test_readme_plug_and_play_functions_example():
    """Verify plug-and-play functions example from README.md (Feature 4)."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_path = Path(temp_dir)
        
        # Create a template that calls an auto-loaded function
        templates_dir = workspace_path / "templates"
        templates_dir.mkdir()
        (templates_dir / "main.md").write_text(
            "Items:\n{{ format_list(['one', 'two']) }}"
        )

        # Create the function file as described in the README
        functions_dir = workspace_path / "functions"
        functions_dir.mkdir()
        (functions_dir / "text_utils.py").write_text(
            """
def format_list(items):
    '''Takes a list and formats it as a Markdown list.'''
    return "\\n".join(f"- {item}" for item in items)
"""
        )
        workspace = load_workspace(workspace_path)
        result = workspace.render("main")
        assert "- one" in result.content
        assert "- two" in result.content

def test_readme_structured_output_example():
    """Verify the structured output example from README.md works."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_path = Path(temp_dir)
        templates_dir = workspace_path / "templates"
        templates_dir.mkdir()

        # Create the chat template as shown in the README
        (templates_dir / "chat.md").write_text(
            """## System
You are a helpful assistant.

## User
I need help with {{ topic }}."""
        )

        workspace = load_workspace(workspace_path)
        result = workspace.render("chat", topic="Python lists")

        # Verify the structured message output
        messages = result.to_openai_format()
        
        assert len(messages) == 2
        
        assert messages[0]["role"] == "system"
        assert messages[0]["content"].strip() == "You are a helpful assistant."
        
        assert messages[1]["role"] == "user"
        assert messages[1]["content"].strip() == "I need help with Python lists."

def test_readme_custom_function_injection_example():
    """Verify the custom function injection example from README.md works."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_path = Path(temp_dir)
        templates_dir = workspace_path / "templates"
        templates_dir.mkdir()
        
        # Template that uses the injected function
        (templates_dir / "summarizer.md").write_text("Summary: {{ summarize(text) }}")

        # The function to be injected
        def summarize(text: str) -> str:
            return text[:10] + "..."

        # This call must match the README
        workspace = load_workspace(
            workspace_path,
            custom_functions={"summarize": summarize}
        )

        long_text = "This is a very long text that needs to be summarized."
        result = workspace.render("summarizer", text=long_text)

        expected_output = "Summary: This is a ...".strip()
        assert result.content.strip() == expected_output

def test_readme_cross_workspace_example():
    """Verify the cross-workspace import example from README.md works."""
    with tempfile.TemporaryDirectory() as temp_dir:
        base_path = Path(temp_dir)

        # Create the shared workspace in a "workspaces" subdirectory to match the README
        shared_ws_path = base_path / "workspaces" / "shared_assets"
        (shared_ws_path / "snippets").mkdir(parents=True)
        (shared_ws_path / "snippets" / "common_header.md").write_text(
            "This is a shared header."
        )

        # Create the main workspace
        main_ws_path = base_path / "workspaces" / "main_project"
        (main_ws_path / "templates").mkdir(parents=True)
        (main_ws_path / "templates" / "main.md").write_text(
            """{% include 'shared::common_header' %}\nThis is the main project prompt."""
        )

        # These lines must match the README
        main_ws = load_workspace(main_ws_path)
        shared_ws = load_workspace(shared_ws_path)

        # Attach the shared workspace with the alias "shared"
        main_ws.add_external_workspace("shared", shared_ws)

        result = main_ws.render("main")

        # Verify the content is combined correctly by comparing line by line
        expected_lines = [
            "This is a shared header.",
            "This is the main project prompt."
        ]
        actual_lines = [line.strip() for line in result.content.strip().splitlines()]
        
        assert actual_lines == expected_lines

def test_readme_toml_frontmatter_example():
    """Verify that TOML frontmatter (+++) works as described in README.md."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_path = Path(temp_dir)
        templates_dir = workspace_path / "templates"
        templates_dir.mkdir()

        # Create a template with TOML frontmatter
        (templates_dir / "toml_template.md").write_text(
            '''+++
framework = "Republic"
version = 1.0
+++
This is the {{ framework }} template, version {{ version }}.'''
        )

        workspace = load_workspace(workspace_path)
        result = workspace.render("toml_template")

        expected_output = "This is the Republic template, version 1.0."
        assert result.content.strip() == expected_output

def test_readme_declarative_cross_workspace_example():
    """Verify cross-workspace import via prompts.toml works as described."""
    with tempfile.TemporaryDirectory() as temp_dir:
        base_path = Path(temp_dir)

        # 1. Create the shared workspace
        shared_ws_path = base_path / "workspaces" / "shared_assets"
        (shared_ws_path / "snippets").mkdir(parents=True)
        (shared_ws_path / "snippets" / "common_header.md").write_text(
            "This is a declarative shared header."
        )

        # 2. Create the main workspace with a prompts.toml pointing to shared
        main_ws_path = base_path / "workspaces" / "main_project"
        (main_ws_path / "templates").mkdir(parents=True)
        
        # The template that uses the shared snippet
        (main_ws_path / "templates" / "main.md").write_text(
            "{% include 'shared::common_header' %}"
        )
        
        # The prompts.toml that defines the external workspace
        (main_ws_path / "prompts.toml").write_text(
            """
            name = "main_project"

            [external_workspaces]
            shared = "../shared_assets"
            """
        )

        # 3. Load the main workspace and render
        # This must match the README's description of automatic loading
        main_ws = load_workspace(main_ws_path)
        result = main_ws.render("main")

        # 4. Verify the content is combined correctly
        assert "This is a declarative shared header." in result.content.strip() 