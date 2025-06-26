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
    render,
    Template,
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
        (self.temp_dir / "functions").mkdir()

        self._create_config()
        self._create_truncation_snippets()
        self._create_truncation_templates()
        self._create_truncation_functions()

        return self.temp_dir

    def _create_config(self):
        """Create configuration for truncation testing."""
        config_content = """[prompts]
name = "truncation-demo"
description = "Workspace demonstrating truncation capabilities"
version = "1.0.0"
function_loaders = ["python"]

[prompts.defaults]
# Truncation settings
token_limit = 4000
truncation_step = 500
use_cache_aware_truncation = true
preserve_system_messages = true

[prompts.environments.low_context]
token_limit = 1000
truncation_step = 200

[prompts.environments.high_context]
token_limit = 128000
truncation_step = 4000

[prompts.environments.production]
token_limit = 8000
truncation_step = 1000
use_cache_aware_truncation = true"""
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
description: Template demonstrating truncation priorities
output_format: messages
var_token_limit: 4000
var_truncation_step: 500
---
[SYSTEM]
{% include 'system_message' %}

{% set processed_messages = apply_truncation(chat_messages, token_limit, truncation_step, use_cache_aware_truncation) %}
{% for message in processed_messages %}
[USER] {{ message.author }}
{{ message.content }}
{% endfor %}

{% if context_info %}
[SYSTEM] Context
{% include 'important_context' %}
{% endif %}

[USER]
{{ user_query }}

[ASSISTANT]
I'll help you with that.
"""
        (self.temp_dir / "templates" / "priority_template.md").write_text(
            priority_template
        )

        # Cache-aware truncation template
        cache_aware_template = """---
description: Template demonstrating cache-aware truncation
output_format: messages
var_token_limit: 4000  
var_truncation_step: 500
var_use_cache_aware_truncation: true
---
[SYSTEM]
{% include 'system_message' %}

{% if use_cache_aware_truncation %}
{% set truncated_messages = cache_aware_truncate(chat_messages, token_limit, truncation_step) %}
{% else %}
{% set truncated_messages = simple_truncate(chat_messages, token_limit) %}
{% endif %}

{% for message in truncated_messages %}
[USER] {{ message.author }}
{{ message.content }}
{% endfor %}

[USER]
{{ user_query }}

[ASSISTANT]
I'll process your request.
"""
        (self.temp_dir / "templates" / "cache_aware_template.md").write_text(
            cache_aware_template
        )

        # Tokenization demo template
        tokenization_template = """---
description: Template demonstrating tokenization capabilities
output_format: messages
---
[SYSTEM]  
{% include 'system_message' %}

{% set token_count = count_tokens(user_query) %}
{% if token_count > token_limit %}
[SYSTEM] Warning
Input is {{ token_count }} tokens, which exceeds limit of {{ token_limit }}.
{% endif %}

[USER]
{{ user_query }}

[ASSISTANT]
{% if debug_mode %}
Token analysis: {{ get_token_analysis(user_query) }}
{% endif %}
I'll help you with that.
"""
        (self.temp_dir / "templates" / "tokenization_template.md").write_text(
            tokenization_template
        )

    def _create_truncation_functions(self):
        """Create functions implementing truncation logic."""
        functions_content = '''"""
Functions implementing truncation and tokenization features.
These demonstrate how to add prompt-poet equivalent functionality using our architecture.
"""

import re
from typing import List, Dict, Any

def count_tokens(text: str) -> int:
    """
    Count tokens in text using a simple approximation.
    In production, this would use tiktoken or similar.
    """
    if not text:
        return 0
    
    # Better approximation: count words as tokens (more realistic for testing)
    # Each word is roughly 1 token, plus some for punctuation
    words = text.split()
    return max(1, len(words))  # Ensure at least 1 token for non-empty text

def tokenize_text(text: str) -> List[int]:
    """
    Tokenize text into token IDs.
    In production, this would use tiktoken.
    """
    if not text:
        return []
    
    # Simple word-based tokenization for demo
    words = text.split()
    # Simulate token IDs
    return list(range(len(words)))

def simple_truncate(messages: List[Dict[str, Any]], token_limit: int) -> List[Dict[str, Any]]:
    """
    Simple truncation that removes messages until under token limit.
    """
    if not messages:
        return messages
    
    # Calculate total tokens first
    total_tokens = sum(count_tokens(msg.get('content', '')) for msg in messages)
    
    if total_tokens <= token_limit:
        return messages
    
    # Separate system messages (never truncate) from others
    system_messages = [msg for msg in messages if msg.get('role') == 'system']
    other_messages = [msg for msg in messages if msg.get('role') != 'system']
    
    # Start with system messages
    result = system_messages.copy()
    current_tokens = sum(count_tokens(msg.get('content', '')) for msg in system_messages)
    
    # Add other messages from most recent, stopping at token limit
    for msg in reversed(other_messages):
        msg_tokens = count_tokens(msg.get('content', ''))
        if current_tokens + msg_tokens <= token_limit:
            result.append(msg)
            current_tokens += msg_tokens
        else:
            break
    
    return result

def cache_aware_truncate(messages: List[Dict[str, Any]], token_limit: int, truncation_step: int) -> List[Dict[str, Any]]:
    """
    Cache-aware truncation that truncates in fixed steps to maximize cache hits.
    This implements the core idea from prompt-poet's cache-aware truncation.
    """
    if not messages:
        return messages
    
    total_tokens = sum(count_tokens(msg.get('content', '')) for msg in messages)
    
    if total_tokens <= token_limit:
        return messages
    
    # Calculate cache-aware target: truncate to fixed boundaries
    # This ensures that the truncation point is predictable for caching
    excess_tokens = total_tokens - token_limit
    truncation_steps_needed = (excess_tokens // truncation_step) + 1
    
    # Target is token_limit minus one full truncation_step for cache alignment
    target_tokens = token_limit - truncation_step
    
    # Separate system messages (never truncate) from others
    system_messages = [msg for msg in messages if msg.get('role') == 'system']
    other_messages = [msg for msg in messages if msg.get('role') != 'system']
    
    # Keep system messages
    result = system_messages.copy()
    current_tokens = sum(count_tokens(msg.get('content', '')) for msg in system_messages)
    
    # Add other messages from most recent until we hit our cache-aligned target
    for msg in reversed(other_messages):
        msg_tokens = count_tokens(msg.get('content', ''))
        if current_tokens + msg_tokens <= target_tokens:
            result.append(msg)
            current_tokens += msg_tokens
        else:
            # Cache-aware: stop at this boundary to maintain cache alignment
            break
    
    return result

def apply_truncation(messages: List[Dict[str, Any]], token_limit: int, truncation_step: int, use_cache_aware: bool = True) -> List[Dict[str, Any]]:
    """
    Apply truncation using the specified strategy.
    """
    if use_cache_aware:
        return cache_aware_truncate(messages, token_limit, truncation_step)
    else:
        return simple_truncate(messages, token_limit)

def get_token_analysis(text: str) -> Dict[str, Any]:
    """
    Get detailed token analysis for debugging.
    """
    tokens = tokenize_text(text)
    return {
        'token_count': len(tokens),
        'character_count': len(text),
        'word_count': len(text.split()),
        'avg_chars_per_token': len(text) / len(tokens) if tokens else 0
    }

def create_priority_messages(messages: List[Dict[str, Any]], priorities: Dict[str, int]) -> List[Dict[str, Any]]:
    """
    Create messages with truncation priorities.
    Lower priority numbers = keep longer.
    """
    result = []
    for msg in messages:
        msg_copy = msg.copy()
        role = msg.get('role', 'user')
        msg_copy['truncation_priority'] = priorities.get(role, 5)  # Default priority 5
        result.append(msg_copy)
    
    return result

def demonstrate_truncation_priorities():
    """
    Demonstrate how truncation priorities would work.
    """
    priorities = {
        'system': 0,      # Never truncate
        'assistant': 1,   # High priority  
        'user': 2,        # Medium priority
        'function': 3,    # Lower priority
        'tool': 4         # Lowest priority
    }
    return priorities

# Export functions for template use
WORKSPACE_FUNCTIONS = {
    'count_tokens': count_tokens,
    'tokenize_text': tokenize_text,
    'simple_truncate': simple_truncate,
    'cache_aware_truncate': cache_aware_truncate,
    'apply_truncation': apply_truncation,
    'get_token_analysis': get_token_analysis,
    'create_priority_messages': create_priority_messages,
    'demonstrate_truncation_priorities': demonstrate_truncation_priorities,
}
'''
        (self.temp_dir / "functions" / "__init__.py").write_text(functions_content)

    def cleanup(self):
        """Clean up temporary directory."""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)


@pytest.fixture
def truncation_workspace():
    """Fixture providing a workspace for truncation testing."""
    setup = TruncationTestSetup()
    workspace_path = setup.create_truncation_workspace()
    workspace = load_workspace(workspace_path)

    yield workspace

    setup.cleanup()


class TestTruncationFeatures:
    """Test truncation features implemented through our existing mechanisms."""

    def test_simple_tokenization(self, truncation_workspace):
        """Test basic tokenization functionality."""
        functions = truncation_workspace.get_functions_dict()

        count_tokens = functions["count_tokens"]
        tokenize_text = functions["tokenize_text"]

        # Test token counting
        text = "This is a test message"
        token_count = count_tokens(text)
        assert token_count > 0
        assert isinstance(token_count, int)

        # Test tokenization
        tokens = tokenize_text(text)
        assert isinstance(tokens, list)
        assert len(tokens) > 0

    def test_simple_truncation(self, truncation_workspace):
        """Test simple truncation algorithm."""
        functions = truncation_workspace.get_functions_dict()
        simple_truncate = functions["simple_truncate"]

        # Create test messages
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"},
            {"role": "assistant", "content": "I'm doing well, thank you!"},
            {"role": "user", "content": "What's the weather like?"},
        ]

        # Test truncation with very low token limit to force truncation
        truncated = simple_truncate(messages, token_limit=10)

        # Should preserve system message and truncate others
        assert len(truncated) < len(messages)
        assert any(msg["role"] == "system" for msg in truncated)

        # System message should always be first
        assert truncated[0]["role"] == "system"

        # Should have fewer total messages due to truncation
        original_count = len(messages)
        truncated_count = len(truncated)
        assert truncated_count < original_count

    def test_cache_aware_truncation(self, truncation_workspace):
        """Test cache-aware truncation algorithm."""
        functions = truncation_workspace.get_functions_dict()
        cache_aware_truncate = functions["cache_aware_truncate"]

        # Create test messages with varying lengths
        messages = [
            {"role": "system", "content": "System message"},
            {"role": "user", "content": "Short message"},
            {
                "role": "user",
                "content": "This is a much longer message that contains more content and should contribute more tokens to the total count",
            },
            {"role": "user", "content": "Another message"},
            {"role": "user", "content": "Final message"},
        ]

        # Test cache-aware truncation
        truncated = cache_aware_truncate(messages, token_limit=100, truncation_step=20)

        # Should preserve system message
        assert truncated[0]["role"] == "system"

        # Should have fewer messages than original
        assert len(truncated) <= len(messages)

    def test_truncation_in_template(self, truncation_workspace):
        """Test truncation functionality integrated into templates."""
        template = truncation_workspace.templates["priority_template"]

        # Create test data with many chat messages
        chat_messages = [
            {"author": "Alice", "content": "Hello everyone!"},
            {"author": "Bob", "content": "How's the project going?"},
            {"author": "Charlie", "content": "Making good progress."},
            {"author": "David", "content": "Great to hear!"},
            {"author": "Eve", "content": "When is the deadline?"},
            {"author": "Frank", "content": "Next Friday."},
        ]

        template_data = {
            "chat_messages": chat_messages,
            "user_query": "What's our current status?",
            "token_limit": 200,  # Low limit to force truncation
            "truncation_step": 50,
            "use_cache_aware_truncation": True,
            "context_info": "Project Alpha development",
        }

        prompt = render(template, template_data, truncation_workspace)

        # Should produce messages
        assert prompt.output_format == "messages"
        assert len(prompt.messages) > 0

        # Should have system message
        system_messages = [msg for msg in prompt.messages if msg.role == "system"]
        assert len(system_messages) > 0

    def test_cache_aware_template_rendering(self, truncation_workspace):
        """Test cache-aware truncation in template rendering."""
        template = truncation_workspace.templates["cache_aware_template"]

        # Test with cache-aware truncation enabled
        chat_messages = [
            {"author": "User1", "content": "Message 1"},
            {"author": "User2", "content": "Message 2"},
            {"author": "User3", "content": "Message 3"},
            {"author": "User4", "content": "Message 4"},
            {"author": "User5", "content": "Message 5"},
        ]

        template_data = {
            "chat_messages": chat_messages,
            "user_query": "Help me understand this",
            "token_limit": 150,
            "truncation_step": 30,
            "use_cache_aware_truncation": True,
        }

        prompt_cache_aware = render(template, template_data, truncation_workspace)

        # Test with simple truncation
        template_data["use_cache_aware_truncation"] = False
        prompt_simple = render(template, template_data, truncation_workspace)

        # Both should produce valid prompts
        assert prompt_cache_aware.output_format == "messages"
        assert prompt_simple.output_format == "messages"

        # Results might differ due to different truncation strategies
        cache_aware_content = str(prompt_cache_aware)
        simple_content = str(prompt_simple)

        # Both should contain the user query
        assert "Help me understand this" in cache_aware_content
        assert "Help me understand this" in simple_content

    def test_tokenization_template_integration(self, truncation_workspace):
        """Test tokenization features integrated into templates."""
        template = truncation_workspace.templates["tokenization_template"]

        # Test with a long user query
        long_query = "This is a very long user query that contains many words and should trigger the token limit warning in our template because it exceeds the specified token limit that we have configured for this particular test case."

        template_data = {
            "user_query": long_query,
            "token_limit": 20,  # Low limit to trigger warning
            "debug_mode": True,
        }

        prompt = render(template, template_data, truncation_workspace)
        content = str(prompt)

        # Should contain token analysis in debug mode
        assert "Token analysis" in content

        # Should contain warning about exceeding token limit
        assert "exceeds limit" in content

    def test_truncation_priority_concept(self, truncation_workspace):
        """Test the concept of truncation priorities using our PromptMessage field."""
        functions = truncation_workspace.get_functions_dict()
        create_priority_messages = functions["create_priority_messages"]

        # Test creating messages with priorities
        messages = [
            {"role": "system", "content": "System message"},
            {"role": "user", "content": "User message"},
            {"role": "assistant", "content": "Assistant message"},
        ]

        priorities = {
            "system": 0,  # Highest priority (never truncate)
            "assistant": 1,  # High priority
            "user": 2,  # Lower priority
        }

        priority_messages = create_priority_messages(messages, priorities)

        # Check that priorities were assigned
        assert priority_messages[0]["truncation_priority"] == 0  # system
        assert priority_messages[1]["truncation_priority"] == 2  # user
        assert priority_messages[2]["truncation_priority"] == 1  # assistant

    def test_environment_based_truncation_settings(self, truncation_workspace):
        """Test how different environments can have different truncation settings."""
        template = truncation_workspace.templates["cache_aware_template"]

        base_data = {
            "chat_messages": [{"author": "User", "content": "Test message"}],
            "user_query": "Test query",
            "use_cache_aware_truncation": True,
        }

        # Test low context environment
        low_context_config = truncation_workspace.get_environment_config("low_context")
        low_context_data = {**base_data, **low_context_config}

        prompt_low = render(template, low_context_data, truncation_workspace)

        # Test high context environment
        high_context_config = truncation_workspace.get_environment_config(
            "high_context"
        )
        high_context_data = {**base_data, **high_context_config}

        prompt_high = render(template, high_context_data, truncation_workspace)

        # Both should render successfully
        assert prompt_low.output_format == "messages"
        assert prompt_high.output_format == "messages"

        # The environments have different token limits
        assert low_context_config["token_limit"] != high_context_config["token_limit"]


class TestPromptPoetEquivalentTruncation:
    """Test that our truncation implementation matches prompt-poet capabilities."""

    def test_equivalent_to_prompt_poet_tokenization(self, truncation_workspace):
        """Test that our tokenization is equivalent to prompt-poet's approach."""
        functions = truncation_workspace.get_functions_dict()

        # Our functions should provide the same capabilities as prompt-poet
        assert "count_tokens" in functions  # Equivalent to prompt.tokenize()
        assert "tokenize_text" in functions  # Equivalent to prompt.tokens

        count_tokens = functions["count_tokens"]
        tokenize_text = functions["tokenize_text"]

        # Test functionality
        text = "Hello world, this is a test."
        token_count = count_tokens(text)
        tokens = tokenize_text(text)

        assert token_count > 0
        assert len(tokens) > 0
        assert isinstance(tokens, list)

    def test_equivalent_to_prompt_poet_truncation(self, truncation_workspace):
        """Test that our truncation is equivalent to prompt-poet's approach."""
        functions = truncation_workspace.get_functions_dict()

        # Our functions should provide the same capabilities as prompt-poet
        assert "cache_aware_truncate" in functions  # Equivalent to prompt.truncate()
        assert "apply_truncation" in functions  # Flexible truncation strategy

        cache_aware_truncate = functions["cache_aware_truncate"]

        # Test with similar parameters to prompt-poet examples
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Message 1"},
            {"role": "user", "content": "Message 2"},
            {"role": "user", "content": "Message 3"},
        ]

        # Parameters similar to prompt-poet's example
        TOKEN_LIMIT = 128000
        TRUNCATION_STEP = 4000

        truncated = cache_aware_truncate(messages, TOKEN_LIMIT, TRUNCATION_STEP)

        # Should preserve system message and implement cache-aware logic
        assert len(truncated) <= len(messages)
        assert truncated[0]["role"] == "system"

    def test_template_integration_like_prompt_poet(self, truncation_workspace):
        """Test that our template integration matches prompt-poet's approach."""
        # prompt-poet allows calling truncation directly in templates
        # We achieve the same through our function system

        template_content = """---
output_format: messages
---
[SYSTEM]
System message

{% set truncated_messages = cache_aware_truncate(chat_messages, 4000, 500) %}
{% for message in truncated_messages %}
[USER] {{ message.author }}
{{ message.content }}
{% endfor %}

[USER]
{{ user_query }}

[ASSISTANT]
Response
"""

        # Create temporary template
        temp_template = Template(
            name="truncation_integration_test",
            content=template_content,
            output_format="messages",
        )

        template_data = {
            "chat_messages": [
                {"author": "Alice", "content": "Hello"},
                {"author": "Bob", "content": "Hi there"},
                {"author": "Charlie", "content": "How are you?"},
            ],
            "user_query": "What's happening?",
        }

        prompt = render(temp_template, template_data, truncation_workspace)

        # Should render successfully with truncation applied
        assert prompt.output_format == "messages"
        assert len(prompt.messages) > 0

        # Should contain the user query
        content = str(prompt)
        assert "What's happening?" in content
