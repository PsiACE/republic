"""
Test cases demonstrating how Republic Prompt can implement truncation and cache-aware
truncation features using existing mechanisms without modifying core code.

This shows how our architecture's flexibility allows us to implement advanced features
like prompt-poet's truncation through:
1. Function-based tokenization and truncation
2. Message truncation_priority field
3. Template-level logic for cache-aware behavior
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from republic_prompt import (
    load_workspace,
)


class TruncationTestSetup:
    """Helper class to create workspaces demonstrating truncation features."""

    def __init__(self):
        self.temp_dir = None

    def create_truncation_workspace(self) -> Path:
        """Create a workspace demonstrating truncation capabilities."""
        self.temp_dir = Path(tempfile.mkdtemp())

        # Create workspace structure
        (self.temp_dir / "snippets").mkdir()
        (self.temp_dir / "templates").mkdir()

        self._create_config()
        self._create_truncation_snippets()
        self._create_truncation_templates()

        return self.temp_dir

    def _create_config(self):
        """Create configuration for truncation testing."""
        config_content = """
name = "truncation-demo"
description = "Workspace demonstrating truncation capabilities"
version = "1.0.0"

[defaults]
# Truncation settings
token_limit = 4000
truncation_step = 500
use_cache_aware_truncation = true
preserve_system_messages = true
"""
        (self.temp_dir / "prompts.toml").write_text(config_content)

    def _create_truncation_snippets(self):
        """Create snippets for truncation testing."""

        # System message (high priority - never truncate)
        system_message = """---
description: System message with highest priority
---
You are a helpful AI assistant. This message should never be truncated."""
        (self.temp_dir / "snippets" / "system_message.md").write_text(system_message)

        # Important context (medium priority)
        important_context = """---
description: Important context that should be preserved when possible
---
Important context: {{ context_info }}"""
        (self.temp_dir / "snippets" / "important_context.md").write_text(
            important_context
        )

        # Chat history (low priority - truncate first)
        chat_history = """---
description: Chat history that can be truncated
---
{% for message in chat_messages %}
{{ message.author }}: {{ message.content }}
{% endfor %}"""
        (self.temp_dir / "snippets" / "chat_history.md").write_text(chat_history)

    def _create_truncation_templates(self):
        """Create templates demonstrating truncation features."""
        # Template with explicit truncation priorities
        priority_template = """---
output_format: "chat"
---
[SYSTEM]
{% include 'system_message' %}

{% set processed_messages = apply_truncation(chat_messages, token_limit, truncation_step) %}
{% for message in processed_messages %}
[USER]
{{ message.content }}
{% endfor %}

{% if context_info %}
[SYSTEM]
{% include 'important_context' %}
{% endif %}

[USER]
{{ user_query }}
"""
        (self.temp_dir / "templates" / "priority_template.md").write_text(
            priority_template
        )

    def cleanup(self):
        """Clean up temporary directory."""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)


def count_tokens(text: str) -> int:
    if not text:
        return 0
    return len(text.split())

def simple_truncate(messages: list, token_limit: int, truncation_step: int = 0):
    """Truncates messages from the beginning."""
    total_tokens = sum(count_tokens(msg.get('content', '')) for msg in messages)
    if total_tokens <= token_limit:
        return messages

    truncated_messages = list(messages)
    while total_tokens > token_limit and truncated_messages:
        removed_msg = truncated_messages.pop(0)
        total_tokens -= count_tokens(removed_msg.get('content', ''))
    return truncated_messages


@pytest.fixture
def truncation_workspace():
    """Fixture providing a workspace for truncation testing."""
    setup = TruncationTestSetup()
    workspace_path = setup.create_truncation_workspace()
    
    custom_functions = {
        "apply_truncation": simple_truncate,
        "count_tokens": count_tokens,
    }
    
    workspace = load_workspace(workspace_path, custom_functions=custom_functions)

    yield workspace

    setup.cleanup()


class TestTruncationFeatures:
    """Test truncation features implemented through our existing mechanisms."""

    def test_simple_tokenization(self, truncation_workspace):
        """Test basic tokenization functionality."""
        # Token counting is done via a custom function
        assert count_tokens("This is a test") == 4
        assert count_tokens("") == 0

    def test_simple_truncation_logic(self):
        """Test the logic of the simple_truncate function."""
        messages = [
            {"role": "user", "content": "This is the first message."},
            {"role": "user", "content": "This is the second message which is longer."},
            {"role": "user", "content": "Third and final message."},
        ]
        # Total tokens = 6 + 8 + 5 = 19
        
        # No truncation needed
        assert len(simple_truncate(list(messages), 20)) == 3
        
        # Truncate first message
        truncated = simple_truncate(list(messages), 15)
        assert len(truncated) == 2
        assert truncated[0]['content'] == "This is the second message which is longer."

        # Truncate first two messages
        truncated_2 = simple_truncate(list(messages), 5)
        assert len(truncated_2) == 1
        assert truncated_2[0]['content'] == "Third and final message."

    def test_truncation_in_template(self, truncation_workspace):
        """Test truncation functionality integrated into templates."""
        chat_messages = [
            {"author": "Alice", "content": "This message should be truncated."},
            {"author": "Bob", "content": "This one too, it is quite long."},
            {"author": "Charlie", "content": "This message should remain in the output."},
            {"author": "David", "content": "And this one as well for the final prompt."},
        ]
        # tokens: 5, 7, 7, 8. Total = 27

        template_data = {
            "chat_messages": chat_messages,
            "user_query": "What's our current status?",
            "token_limit": 20, # Should keep last 3 messages (7+8) + query (4) = 19 < 20
            "truncation_step": 10,
            "context_info": "Project Alpha development",
        }

        result = truncation_workspace.render("priority_template", **template_data)

        content = result.content
        assert "This message should be truncated" not in content
        assert "This one too, it is quite long" not in content
        assert "This message should remain in the output" in content
        assert "And this one as well for the final prompt" in content
        assert "Project Alpha development" in content
        assert "What's our current status?" in content 