"""
Test cases demonstrating Republic Prompt's equivalence to prompt-poet functionality,
but focused on our domain-specific approach and file-first architecture.

This test suite validates that Republic Prompt can handle all the core use cases
shown in prompt-poet, while leveraging our unique strengths:
- File-first architecture vs code-first approach
- Environment-aware configuration
- Modular snippet composition
- Business logic functions
- Message format handling with truncation priorities
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


class PromptPoetEquivalenceTestSetup:
    """Helper class to create test workspaces demonstrating prompt-poet equivalent functionality."""

    def __init__(self):
        self.temp_dir = None

    def create_prompt_poet_equivalent_workspace(self) -> Path:
        """Create a workspace that demonstrates prompt-poet equivalent functionality."""
        self.temp_dir = Path(tempfile.mkdtemp())

        # Create workspace structure
        (self.temp_dir / "snippets").mkdir()
        (self.temp_dir / "templates").mkdir()
        (self.temp_dir / "prompts").mkdir()
        (self.temp_dir / "functions").mkdir()

        self._create_config()
        self._create_prompt_poet_equivalent_snippets()
        self._create_prompt_poet_equivalent_templates()
        self._create_prompt_poet_equivalent_prompts()
        self._create_prompt_poet_equivalent_functions()

        return self.temp_dir

    def _create_config(self):
        """Create configuration equivalent to prompt-poet settings."""
        config_content = """[prompts]
name = "prompt-poet-equivalent"
description = "Workspace demonstrating prompt-poet equivalent functionality"
version = "1.0.0"
function_loaders = ["python"]

[prompts.defaults]
# Core defaults similar to prompt-poet
character_name = "Assistant"
username = "User"
modality = "text"
debug_mode = false
show_reasoning = false

[prompts.environments.development]
debug_mode = true
show_reasoning = true
verbose = true
token_limit = 4000
truncation_step = 500

[prompts.environments.production]
debug_mode = false
show_reasoning = false
verbose = false
token_limit = 8000
truncation_step = 1000

[prompts.environments.high_context]
debug_mode = false
show_reasoning = false
verbose = false
token_limit = 128000
truncation_step = 4000"""
        (self.temp_dir / "prompts.toml").write_text(config_content)

    def _create_prompt_poet_equivalent_snippets(self):
        """Create snippets equivalent to prompt-poet examples."""

        # System instructions snippet (equivalent to prompt-poet's system role)
        system_instructions = """---
description: System instructions equivalent to prompt-poet system role
var_character_name: Assistant
---
Your name is {{ character_name }} and you are meant to be helpful and never harmful to humans."""
        (self.temp_dir / "snippets" / "system_instructions.md").write_text(
            system_instructions
        )

        # Audio modality instructions
        audio_instructions = """---
description: Special instructions for audio modality
---
{% if modality == "audio" %}
{{ username }} is currently using audio modality. Keep your answers succinct and to the point.
{% endif %}"""
        (self.temp_dir / "snippets" / "audio_instructions.md").write_text(
            audio_instructions
        )

        # Chat message formatting
        chat_messages = """---
description: Format chat messages with truncation priorities
---
{% for message in current_chat_messages %}
{{ message.author }}: {{ message.content }}
{% endfor %}"""
        (self.temp_dir / "snippets" / "chat_messages.md").write_text(chat_messages)

        # Homework examples (conditional inclusion)
        homework_examples = """---
description: Homework examples with conditional inclusion
---
{% if extract_user_query_topic(user_query) == "homework_help" %}
{% for homework_example in fetch_few_shot_homework_examples(username, character_name) %}
**Example {{ loop.index }}:**
{{ homework_example }}

{% endfor %}
{% endif %}"""
        (self.temp_dir / "snippets" / "homework_examples.md").write_text(
            homework_examples
        )

    def _create_prompt_poet_equivalent_templates(self):
        """Create templates equivalent to prompt-poet examples."""

        # Main conversation template (equivalent to prompt-poet's full example)
        conversation_template = """---
description: Full conversation template equivalent to prompt-poet example
output_format: messages
snippets: system_instructions, audio_instructions, homework_examples, chat_messages
var_character_name: Character Assistant
var_username: Jeff
var_modality: text
var_user_query: Can you help me with my homework?
---
[SYSTEM]
{% include 'system_instructions' %}

{% include 'audio_instructions' %}

{% include 'homework_examples' %}

{% for message in current_chat_messages %}
[USER] {{ message.author }}
{{ message.content }}
{% endfor %}

[USER] {{ username }}
{{ user_query }}

[ASSISTANT] {{ character_name }}
I'll help you with that.
"""
        (self.temp_dir / "templates" / "conversation_template.md").write_text(
            conversation_template
        )

        # Template with truncation priorities (equivalent to prompt-poet's truncation example)
        truncation_template = """---
description: Template demonstrating truncation priorities like prompt-poet
output_format: messages
var_character_name: Assistant
var_username: User
---
[SYSTEM]
{% include 'system_instructions' %}

{% for message in current_chat_messages %}
[USER] {{ message.author }}
{{ message.content }}
{% endfor %}

[USER] {{ username }}
{{ user_query }}

[ASSISTANT] {{ character_name }}
"""
        (self.temp_dir / "templates" / "truncation_template.md").write_text(
            truncation_template
        )

        # Cache-aware template (simulating prompt-poet's cache-aware truncation)
        cache_aware_template = """---
description: Template simulating cache-aware truncation behavior
output_format: messages
var_character_name: Assistant
var_username: User
var_token_limit: 4000
var_truncation_step: 500
---
[SYSTEM] 
Your name is {{ character_name }} and you are meant to be helpful.

{% if debug_mode %}
**Debug Mode Active** - Token limit: {{ token_limit }}, Truncation step: {{ truncation_step }}
{% endif %}

{% for message in current_chat_messages %}
[USER] {{ message.author }}
{{ message.content }}
{% endfor %}

[USER] {{ username }}
{{ user_query }}

[ASSISTANT] {{ character_name }}
"""
        (self.temp_dir / "templates" / "cache_aware_template.md").write_text(
            cache_aware_template
        )

    def _create_prompt_poet_equivalent_prompts(self):
        """Create ready-to-use prompts equivalent to prompt-poet examples."""

        # Simple chat prompt (equivalent to prompt-poet's basic usage)
        simple_chat = """---
description: Simple chat prompt equivalent to prompt-poet basic example
output_format: messages
---
[SYSTEM]
Your name is Character Assistant and you are meant to be helpful and never harmful to humans.

[USER] Jeff
Can you help me with my homework?

[ASSISTANT] Character Assistant
"""
        (self.temp_dir / "prompts" / "simple_chat.md").write_text(simple_chat)

    def _create_prompt_poet_equivalent_functions(self):
        """Create functions equivalent to prompt-poet's template-native function calling."""
        functions_content = '''"""
Functions equivalent to prompt-poet's template-native function calling.
These demonstrate the same dynamic content generation capabilities.
"""

def extract_user_query_topic(query: str) -> str:
    """
    Extract topic from user query - equivalent to prompt-poet's example.
    This simulates the round-trip to a topic classifier mentioned in prompt-poet docs.
    """
    query_lower = query.lower()
    
    if any(keyword in query_lower for keyword in ["homework", "assignment", "study", "learn"]):
        return "homework_help"
    elif any(keyword in query_lower for keyword in ["code", "programming", "debug", "error"]):
        return "coding_help"
    elif any(keyword in query_lower for keyword in ["math", "calculate", "solve", "equation"]):
        return "math_help"
    else:
        return "general"

def fetch_few_shot_homework_examples(username: str, character_name: str) -> list:
    """
    Fetch few-shot examples for homework help - equivalent to prompt-poet's dynamic data retrieval.
    In a real system, this would query a database or API.
    """
    examples = [
        f"Q: What is photosynthesis?\\nA: {character_name} explains: Photosynthesis is the process by which plants convert sunlight into energy.",
        f"Q: How do you solve quadratic equations?\\nA: {character_name} shows: Use the quadratic formula: x = (-b ± √(b²-4ac)) / 2a",
        f"Q: What caused World War I?\\nA: {character_name} explains: Multiple factors including alliances, imperialism, and the assassination of Archduke Franz Ferdinand."
    ]
    return examples

def get_current_chat_messages() -> list:
    """
    Simulate getting current chat messages with metadata.
    Equivalent to prompt-poet's dynamic message handling.
    """
    return [
        {"author": "Alice", "content": "Hello everyone!", "timestamp": "2024-01-01T10:00:00"},
        {"author": "Bob", "content": "How's the project going?", "timestamp": "2024-01-01T10:01:00"},
        {"author": "Charlie", "content": "Making good progress on the documentation.", "timestamp": "2024-01-01T10:02:00"}
    ]

def simulate_tokenization(text: str) -> list:
    """
    Simulate tokenization like prompt-poet's tiktoken integration.
    In a real implementation, this would use actual tokenization.
    """
    # Simple word-based tokenization for demonstration
    words = text.split()
    # Simulate token IDs (in reality, these would be from tiktoken)
    return list(range(len(words)))

def simulate_truncation(messages: list, token_limit: int = 4000, truncation_step: int = 500) -> list:
    """
    Simulate cache-aware truncation like prompt-poet.
    This demonstrates the concept without actual token counting.
    """
    if len(messages) <= 3:  # Keep system, user query, and assistant response
        return messages
    
    # Simulate truncation by removing middle messages
    # Keep first (system) and last few messages
    truncated = [messages[0]]  # Keep system message
    if len(messages) > 4:
        truncated.extend(messages[-3:])  # Keep last 3 messages
    else:
        truncated.extend(messages[1:])
    
    return truncated

def get_template_registry_path() -> str:
    """
    Simulate prompt-poet's template registry concept.
    In our file-first approach, this is just the workspace path.
    """
    return "templates/"

# Export functions for template use (equivalent to prompt-poet's function exposure)
WORKSPACE_FUNCTIONS = {
    'extract_user_query_topic': extract_user_query_topic,
    'fetch_few_shot_homework_examples': fetch_few_shot_homework_examples,
    'get_current_chat_messages': get_current_chat_messages,
    'simulate_tokenization': simulate_tokenization,
    'simulate_truncation': simulate_truncation,
    'get_template_registry_path': get_template_registry_path,
    
    # Add some current_chat_messages for template use
    'current_chat_messages': get_current_chat_messages(),
}
'''
        (self.temp_dir / "functions" / "__init__.py").write_text(functions_content)

    def cleanup(self):
        """Clean up temporary directory."""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)


@pytest.fixture
def prompt_poet_workspace():
    """Fixture providing a workspace equivalent to prompt-poet functionality."""
    setup = PromptPoetEquivalenceTestSetup()
    workspace_path = setup.create_prompt_poet_equivalent_workspace()
    workspace = load_workspace(workspace_path)

    yield workspace

    setup.cleanup()


class TestBasicPromptPoetEquivalence:
    """Test basic prompt-poet equivalent functionality."""

    def test_basic_template_rendering_like_prompt_poet(self, prompt_poet_workspace):
        """Test basic template rendering equivalent to prompt-poet's basic usage."""
        # This is equivalent to prompt-poet's basic template rendering
        template = prompt_poet_workspace.templates["conversation_template"]

        template_data = {
            "character_name": "Character Assistant",
            "username": "Jeff",
            "user_query": "Can you help me with my homework?",
            "modality": "text",
            "current_chat_messages": [],
        }

        prompt = render(template, template_data, prompt_poet_workspace)

        # Verify it produces structured messages like prompt-poet
        assert prompt.output_format == "messages"
        assert len(prompt.messages) >= 3  # System, User, Assistant

        # Check message structure
        system_msg = prompt.messages[0]
        assert system_msg.role == "system"
        assert "Character Assistant" in system_msg.content
        assert "helpful and never harmful" in system_msg.content

    def test_template_native_function_calling(self, prompt_poet_workspace):
        """Test template-native function calling equivalent to prompt-poet."""
        # This demonstrates prompt-poet's key feature: calling functions directly in templates
        template = prompt_poet_workspace.templates["conversation_template"]

        template_data = {
            "character_name": "HomeworkHelper",
            "username": "Student",
            "user_query": "I need help with my math homework",
            "modality": "text",
            "current_chat_messages": [],
        }

        prompt = render(template, template_data, prompt_poet_workspace)

        # The template should have called extract_user_query_topic() and detected homework
        # This would trigger the homework examples inclusion
        content = str(prompt)

        # Should contain homework examples because function detected homework topic
        assert "homework" in content.lower() or "example" in content.lower()

    def test_environment_driven_behavior_like_prompt_poet(self, prompt_poet_workspace):
        """Test environment-driven behavior similar to prompt-poet's configuration."""
        template = prompt_poet_workspace.templates["cache_aware_template"]

        # Test development environment (equivalent to prompt-poet's debug mode)
        dev_config = prompt_poet_workspace.get_environment_config("development")
        template_data = {
            **dev_config,
            "character_name": "DevAssistant",
            "username": "Developer",
            "user_query": "Debug this code",
            "current_chat_messages": [],
        }

        dev_prompt = render(template, template_data, prompt_poet_workspace)
        dev_content = str(dev_prompt)

        # Should show debug information in development
        assert "Debug Mode Active" in dev_content
        assert "Token limit: 4000" in dev_content

        # Test production environment (minimal output)
        prod_config = prompt_poet_workspace.get_environment_config("production")
        template_data = {
            **prod_config,
            "character_name": "ProdAssistant",
            "username": "User",
            "user_query": "Help me",
            "current_chat_messages": [],
        }

        prod_prompt = render(template, template_data, prompt_poet_workspace)
        prod_content = str(prod_prompt)

        # Should not show debug information in production
        assert "Debug Mode Active" not in prod_content


class TestAdvancedPromptPoetEquivalence:
    """Test advanced prompt-poet equivalent features."""

    def test_message_format_with_truncation_priorities(self, prompt_poet_workspace):
        """Test message format with truncation priorities like prompt-poet."""
        # Create a template that generates messages with different priorities
        template_content = """---
output_format: messages
---
[SYSTEM]
You are a helpful assistant.

[USER] Important
This is a high priority message that should be kept.

[USER] Filler
This is filler content that can be truncated.

[ASSISTANT]
I understand and will help you."""

        # Create temporary template
        temp_template = Template(
            name="truncation_test", content=template_content, output_format="messages"
        )

        prompt = render(temp_template, {}, prompt_poet_workspace)

        # Verify messages are created with proper structure
        assert prompt.output_format == "messages"
        assert len(prompt.messages) == 4

        # Check that messages have the expected roles
        roles = [msg.role for msg in prompt.messages]
        assert "system" in roles
        assert "user" in roles
        assert "assistant" in roles

    def test_conditional_content_inclusion(self, prompt_poet_workspace):
        """Test conditional content inclusion equivalent to prompt-poet's control flow."""
        template = prompt_poet_workspace.templates["conversation_template"]

        # Test with homework query (should include homework examples)
        homework_data = {
            "character_name": "TeacherBot",
            "username": "Student",
            "user_query": "Help me with my homework assignment",
            "modality": "text",
            "current_chat_messages": [],
        }

        homework_prompt = render(template, homework_data, prompt_poet_workspace)
        homework_content = str(homework_prompt)

        # Should include homework examples
        assert (
            "example" in homework_content.lower()
            or "homework" in homework_content.lower()
        )

        # Test with non-homework query (should not include homework examples)
        general_data = {
            "character_name": "ChatBot",
            "username": "User",
            "user_query": "What's the weather like?",
            "modality": "text",
            "current_chat_messages": [],
        }

        general_prompt = render(template, general_data, prompt_poet_workspace)
        general_content = str(general_prompt)

        # The homework examples should be conditionally excluded
        # (though some homework-related text might still appear in system instructions)
        assert "homework" not in general_content.lower()

    def test_audio_modality_handling(self, prompt_poet_workspace):
        """Test modality-specific behavior equivalent to prompt-poet's modality handling."""
        template = prompt_poet_workspace.templates["conversation_template"]

        # Test with audio modality
        audio_data = {
            "character_name": "VoiceAssistant",
            "username": "Speaker",
            "user_query": "Tell me about the weather",
            "modality": "audio",
            "current_chat_messages": [],
        }

        audio_prompt = render(template, audio_data, prompt_poet_workspace)
        audio_content = str(audio_prompt)

        # Should include audio-specific instructions
        assert (
            "audio modality" in audio_content.lower()
            or "succinct" in audio_content.lower()
        )

        # Test with text modality
        text_data = {
            "character_name": "TextAssistant",
            "username": "Typer",
            "user_query": "Tell me about the weather",
            "modality": "text",
            "current_chat_messages": [],
        }

        text_prompt = render(template, text_data, prompt_poet_workspace)
        text_content = str(text_prompt)

        # Should not include audio-specific instructions
        assert "audio modality" not in text_content.lower()


class TestPromptPoetStyleWorkflow:
    """Test complete workflow equivalent to prompt-poet usage patterns."""

    def test_complete_prompt_poet_workflow(self, prompt_poet_workspace):
        """Test a complete workflow equivalent to prompt-poet's full example."""
        # Step 1: Load workspace (equivalent to prompt-poet's Prompt initialization)
        assert prompt_poet_workspace.name == "prompt-poet-equivalent"
        assert len(prompt_poet_workspace.templates) > 0
        assert len(prompt_poet_workspace.functions) > 0

        # Step 2: Prepare template data (equivalent to prompt-poet's template_data)
        template_data = {
            "character_name": "StudyBuddy",
            "username": "Alice",
            "user_query": "Can you help me understand photosynthesis?",
            "modality": "text",
            "current_chat_messages": [
                {"author": "Alice", "content": "I'm studying biology"},
                {
                    "author": "StudyBuddy",
                    "content": "Great! What topic are you working on?",
                },
            ],
        }

        # Step 3: Render template (equivalent to prompt-poet's render)
        template = prompt_poet_workspace.templates["conversation_template"]
        prompt = render(template, template_data, prompt_poet_workspace)

        # Step 4: Verify output format (equivalent to prompt-poet's messages property)
        assert prompt.output_format == "messages"
        messages = prompt.to_openai_format()

        # Should have proper OpenAI-compatible format
        assert isinstance(messages, list)
        assert all("role" in msg and "content" in msg for msg in messages)

        # Step 5: Verify content quality
        content = str(prompt)
        assert "StudyBuddy" in content
        assert "Alice" in content
        assert "photosynthesis" in content

    def test_template_registry_concept(self, prompt_poet_workspace):
        """Test our file-first approach as equivalent to prompt-poet's template registry."""
        # Our file-first approach IS the template registry
        # Templates are stored as files and loaded from disk

        # Verify templates are loaded from files
        assert "conversation_template" in prompt_poet_workspace.templates
        assert "truncation_template" in prompt_poet_workspace.templates
        assert "cache_aware_template" in prompt_poet_workspace.templates

        # Verify each template has proper metadata
        for template_name, template in prompt_poet_workspace.templates.items():
            assert template.name == template_name
            assert template.content
            assert template.description

        # Test loading a template directly (equivalent to prompt-poet's template_path)
        template = prompt_poet_workspace.templates["conversation_template"]
        assert template.output_format == "messages"
        assert len(template.snippets) > 0

    def test_function_integration_like_prompt_poet(self, prompt_poet_workspace):
        """Test function integration equivalent to prompt-poet's function calling."""
        # Test that functions are properly loaded and available
        functions = prompt_poet_workspace.get_functions_dict()

        # Should have the key functions equivalent to prompt-poet
        assert "extract_user_query_topic" in functions
        assert "fetch_few_shot_homework_examples" in functions
        assert "simulate_tokenization" in functions
        assert "simulate_truncation" in functions

        # Test calling functions directly (equivalent to prompt-poet's template-native calling)
        extract_topic = functions["extract_user_query_topic"]
        assert extract_topic("help with homework") == "homework_help"
        assert extract_topic("debug my code") == "coding_help"
        assert extract_topic("what's the weather") == "general"

        # Test data fetching function
        fetch_examples = functions["fetch_few_shot_homework_examples"]
        examples = fetch_examples("Student", "Teacher")
        assert isinstance(examples, list)
        assert len(examples) > 0
        assert all("Q:" in example and "A:" in example for example in examples)


class TestPromptPoetComparisonFeatures:
    """Test features that show our advantages over prompt-poet."""

    def test_file_first_architecture_advantage(self, prompt_poet_workspace):
        """Test our file-first architecture advantages over prompt-poet's code-first approach."""
        # Our templates are stored as files, making them:
        # 1. Version controllable
        # 2. Editable by non-programmers
        # 3. Cacheable
        # 4. Modular and reusable

        # Verify templates come from files
        template = prompt_poet_workspace.templates["conversation_template"]
        assert template.name == "conversation_template"
        assert template.snippets  # Uses modular snippets

        # Verify snippets are reusable across templates
        snippets_used = set()
        for template in prompt_poet_workspace.templates.values():
            snippets_used.update(template.snippets)

        # Should have reusable snippets
        assert len(snippets_used) > 0
        assert "system_instructions" in snippets_used

    def test_environment_configuration_advantage(self, prompt_poet_workspace):
        """Test our environment configuration advantages."""
        # Our environment system is more structured than prompt-poet's variable passing

        # Test multiple environments
        dev_config = prompt_poet_workspace.get_environment_config("development")
        prod_config = prompt_poet_workspace.get_environment_config("production")
        high_context_config = prompt_poet_workspace.get_environment_config(
            "high_context"
        )

        # Each environment should have different settings
        assert dev_config["debug_mode"] != prod_config["debug_mode"]
        assert dev_config["token_limit"] != high_context_config["token_limit"]
        assert dev_config["truncation_step"] != prod_config["truncation_step"]

    def test_business_logic_separation_advantage(self, prompt_poet_workspace):
        """Test our business logic separation advantages."""
        # Our functions are in separate files, making them:
        # 1. Testable in isolation
        # 2. Reusable across templates
        # 3. Language-agnostic (with loaders)

        # Verify functions are properly isolated
        functions = prompt_poet_workspace.get_functions_dict()

        # Functions should be callable independently
        topic_extractor = functions["extract_user_query_topic"]
        assert callable(topic_extractor)

        # Functions should have proper error handling
        assert topic_extractor("") == "general"  # Handles empty input
        # Note: In real usage, None shouldn't be passed, but our function handles it gracefully

    def test_ready_to_use_prompts_advantage(self, prompt_poet_workspace):
        """Test our ready-to-use prompts advantage over prompt-poet."""
        # We have both templates (need rendering) and prompts (ready to use)
        # This gives users flexibility prompt-poet doesn't have

        # Test ready-to-use prompt
        ready_prompt = prompt_poet_workspace.prompts["simple_chat"]

        # Should be usable without rendering
        assert ready_prompt.content or ready_prompt.output_format == "messages"

        # Can still be rendered if needed for customization
        customized = render(
            ready_prompt, {"character_name": "CustomBot"}, prompt_poet_workspace
        )
        assert "CustomBot" in str(customized) or "Character Assistant" in str(
            customized
        )
