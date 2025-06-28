import pytest
import tempfile
import shutil
from pathlib import Path

from republic_prompt import load_workspace


class EquivalenceTestSetup:
    """Helper class to create test workspaces demonstrating equivalent functionality."""

    def __init__(self):
        self.temp_dir = Path(tempfile.mkdtemp())

    def create_workspace(self) -> Path:
        """Creates a workspace demonstrating equivalent functionality."""
        (self.temp_dir / "snippets").mkdir()
        (self.temp_dir / "templates").mkdir()
        (self.temp_dir / "functions").mkdir(exist_ok=True)
        (self.temp_dir / "functions" / "__init__.py").touch()

        self._create_config()
        self._create_snippets()
        self._create_templates()
        self._create_functions()

        return self.temp_dir

    def _create_config(self):
        """Create a simplified config."""
        (self.temp_dir / "prompts.toml").write_text("""
name = "equivalence-test"
description = "Workspace for testing equivalence"
version = "1.0.0"
""")

    def _create_snippets(self):
        """Create snippets for testing."""
        (self.temp_dir / "snippets" / "system_instructions.md").write_text("""---
character_name: "Assistant"
---
Your name is {{ character_name }}.""")
        (self.temp_dir / "snippets" / "audio_instructions.md").write_text("""---
username: "User"
---
{% if modality == "audio" %}
{{ username }} is using audio. Keep answers succinct.
{% endif %}""")
        (self.temp_dir / "snippets" / "homework_examples.md").write_text("""{% if "homework" in user_query %}
Homework example.
{% endif %}""")

    def _create_templates(self):
        """Create templates for testing."""
        (self.temp_dir / "templates" / "conversation.md").write_text("""---
username: "Jeff"
user_query: "Can you help me with my homework?"
---
## System
{% include 'system_instructions' %}
{% include 'audio_instructions' %}
{% include 'homework_examples' %}

## User
{{ username }}: {{ user_query }}

## Assistant
{{ character_name }}: I'll help you with that.
""")
        (self.temp_dir / "templates" / "debug.md").write_text("""---
token_limit: 8000
---
## System
{% if debug_mode %}
**Debug Mode Active**
{% else %}
Normal Mode
{% endif %}
- Token limit: {{ token_limit }}
""")
        (self.temp_dir / "templates" / "multimessage.md").write_text("""
## System
System message.
## User
First user message.
## Assistant
First assistant response.
## User
Second user message.
""")

    def _create_functions(self):
        # Functions are no longer auto-loaded from arbitrary python files.
        # They are passed at render time or workspace load time.
        pass

    def cleanup(self):
        shutil.rmtree(self.temp_dir)


@pytest.fixture
def equivalence_workspace():
    """Fixture providing a workspace for equivalence testing."""
    setup = EquivalenceTestSetup()
    workspace_path = setup.create_workspace()
    # In the new API, functions are passed in explicitly.
    custom_functions = {
        "extract_user_query_topic": lambda q: "homework_help" if "homework" in q.lower() else "general"
    }
    workspace = load_workspace(workspace_path, custom_functions=custom_functions)
    yield workspace
    setup.cleanup()


class TestEquivalence:
    """Test new API's equivalence to old functionality."""

    def test_basic_rendering(self, equivalence_workspace):
        """Test basic template rendering."""
        result = equivalence_workspace.render("conversation", character_name="TestBot")
        messages = result.to_openai_format()
        assert len(messages) == 3
        system_msg = messages[0]["content"]
        assert "Your name is TestBot" in system_msg
        assert "Jeff: Can you help me with my homework?" in messages[1]["content"]

    def test_environment_driven_behavior(self, equivalence_workspace):
        """Test simulating environments by passing variables at render time."""
        # Dev environment
        dev_result = equivalence_workspace.render("debug", debug_mode=True, token_limit=4000)
        assert "Debug Mode Active" in dev_result.content
        assert "Token limit: 4000" in dev_result.content

        # Prod environment (uses template default)
        prod_result = equivalence_workspace.render("debug", debug_mode=False)
        assert "Normal Mode" in prod_result.content
        assert "Token limit: 8000" in prod_result.content

    def test_message_format_handling(self, equivalence_workspace):
        """Verify that multiple message blocks are parsed correctly."""
        result = equivalence_workspace.render("multimessage")
        messages = result.to_openai_format()
        assert len(messages) == 4
        assert [m["role"] for m in messages] == ["system", "user", "assistant", "user"]
        assert messages[3]["content"].strip() == "Second user message."

    def test_conditional_content_inclusion(self, equivalence_workspace):
        """Test Jinja2's conditional logic for including content."""
        # Test case where condition is met
        result_homework = equivalence_workspace.render(
            "conversation", user_query="I need help with my physics homework."
        )
        assert "Homework example." in result_homework.content

        # Test case where condition is NOT met
        result_no_homework = equivalence_workspace.render(
            "conversation", user_query="What is the weather today?"
        )
        assert "Homework example." not in result_no_homework.content

    def test_modality_handling(self, equivalence_workspace):
        """Test modality-specific behavior using conditional logic."""
        # Audio modality
        audio_result = equivalence_workspace.render(
            "conversation", modality="audio", username="Speaker"
        )
        assert "Speaker is using audio. Keep answers succinct." in audio_result.content

        # Text modality (default behavior, no keyword)
        text_result = equivalence_workspace.render("conversation", modality="text")
        assert "is using audio" not in text_result.content 