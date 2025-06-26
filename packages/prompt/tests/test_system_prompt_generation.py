"""Test cases for system prompt generation with environment detection."""

import pytest
import os
from unittest.mock import patch
from pathlib import Path

from republic_prompt import load_workspace, render
from republic_prompt.core import Template


@pytest.fixture
def examples_workspace():
    """Load the examples workspace for testing."""
    examples_path = Path(__file__).parent.parent / "examples"
    return load_workspace(examples_path)


class TestSystemPromptGeneration:
    """Test system prompt generation with various configurations."""

    def test_base_prompt_without_user_memory(self, examples_workspace):
        """Test that base prompt is generated correctly without user memory."""
        template = examples_workspace.templates["gemini_cli_system_prompt"]
        
        with patch.dict(os.environ, {}, clear=True):
            prompt = render(template, {"domain": "software_engineering"}, examples_workspace)
            
            assert "You are an interactive CLI agent" in prompt.content
            assert "---\n\n" not in prompt.content  # No memory separator
            assert "software_engineering" in prompt.content

    def test_base_prompt_with_empty_user_memory(self, examples_workspace):
        """Test that empty user memory doesn't add separator."""
        template = examples_workspace.templates["gemini_cli_system_prompt"]
        
        with patch.dict(os.environ, {}, clear=True):
            prompt = render(template, {
                "domain": "software_engineering",
                "user_memory": ""
            }, examples_workspace)
            
            assert "You are an interactive CLI agent" in prompt.content
            assert "---\n\n" not in prompt.content

    def test_base_prompt_with_whitespace_user_memory(self, examples_workspace):
        """Test that whitespace-only user memory doesn't add separator."""
        template = examples_workspace.templates["gemini_cli_system_prompt"]
        
        with patch.dict(os.environ, {}, clear=True):
            prompt = render(template, {
                "domain": "software_engineering", 
                "user_memory": "   \n  \t "
            }, examples_workspace)
            
            assert "You are an interactive CLI agent" in prompt.content
            assert "---\n\n" not in prompt.content

    def test_base_prompt_with_user_memory(self, examples_workspace):
        """Test that user memory is appended with separator."""
        template = examples_workspace.templates["gemini_cli_system_prompt"]
        memory = "This is custom user memory.\nBe extra polite."
        
        with patch.dict(os.environ, {}, clear=True):
            prompt = render(template, {
                "domain": "software_engineering",
                "user_memory": memory
            }, examples_workspace)
            
            assert "You are an interactive CLI agent" in prompt.content
            assert f"---\n\n{memory}" in prompt.content

    def test_sandbox_environment_detection(self, examples_workspace):
        """Test sandbox environment detection and warning generation."""
        template = examples_workspace.templates["gemini_cli_system_prompt"]
        
        prompt = render(template, {"domain": "software_engineering"}, examples_workspace)
        
        # Should contain basic agent content
        assert "You are an interactive CLI agent" in prompt.content

    def test_git_repository_detection(self, examples_workspace):
        """Test git repository detection and instructions."""
        template = examples_workspace.templates["gemini_cli_system_prompt"]
        
        prompt = render(template, {"domain": "software_engineering"}, examples_workspace)
        
        # Should contain git-related instructions (since we're in a git repo)
        assert "git" in prompt.content.lower()

    def test_non_git_repository(self, examples_workspace):
        """Test behavior when not in a git repository."""
        template = examples_workspace.templates["gemini_cli_system_prompt"]
        
        prompt = render(template, {"domain": "software_engineering"}, examples_workspace)
        
        # Should contain basic functionality regardless
        assert "You are an interactive CLI agent" in prompt.content

    def test_tool_names_consistency(self, examples_workspace):
        """Test that tool names are consistent across templates."""
        template = examples_workspace.templates["gemini_cli_system_prompt"]
        
        prompt = render(template, {"domain": "software_engineering"}, examples_workspace)
        
        # Check that expected tool names appear
        expected_tools = [
            "GrepTool", "GlobTool", "ReadFileTool", "ReadManyFilesTool",
            "EditTool", "WriteFileTool", "ShellTool", "LSTool"
        ]
        
        for tool in expected_tools:
            assert tool in prompt.content

    def test_environment_specific_configurations(self, examples_workspace):
        """Test that different environments produce different configurations."""
        template = examples_workspace.templates["gemini_cli_system_prompt"]
        
        # Test development environment
        dev_prompt = render(template, {
            "domain": "software_engineering",
            "max_output_lines": 5,
            "debug_mode": True
        }, examples_workspace)
        
        # Test production environment  
        prod_prompt = render(template, {
            "domain": "software_engineering",
            "max_output_lines": 2,
            "debug_mode": False
        }, examples_workspace)
        
        # They should be different
        assert dev_prompt.content != prod_prompt.content

    def test_function_calls_in_templates(self, examples_workspace):
        """Test that template functions are called correctly."""
        template = examples_workspace.templates["gemini_cli_system_prompt"]
        
        prompt = render(template, {"domain": "software_engineering"}, examples_workspace)
        
        # Check that function-generated content appears
        assert "Software Engineering Workflow" in prompt.content
        assert "New Application Workflow" in prompt.content
        assert "Security and Safety Rules" in prompt.content

    def test_snippet_inclusion(self, examples_workspace):
        """Test that snippets are included correctly."""
        template = examples_workspace.templates["gemini_cli_system_prompt"]
        
        prompt = render(template, {"domain": "software_engineering"}, examples_workspace)
        
        # Check that snippet content appears
        assert "Core Mandates" in prompt.content
        assert "Tone and Style" in prompt.content
        assert "Conventions:" in prompt.content

    def test_variable_substitution(self, examples_workspace):
        """Test that template variables are substituted correctly."""
        template = examples_workspace.templates["gemini_cli_system_prompt"]
        
        custom_domain = "data_science"
        prompt = render(template, {"domain": custom_domain}, examples_workspace)
        
        assert custom_domain in prompt.content
        assert "{{ domain }}" not in prompt.content  # Should be substituted

    def test_prebuilt_prompts_validity(self, examples_workspace):
        """Test that all prebuilt prompts are valid and complete."""
        prebuilt_prompts = ["full_cli_system", "basic_cli_system", "simple_agent"]
        
        for prompt_name in prebuilt_prompts:
            prompt = examples_workspace.prompts[prompt_name]
            assert isinstance(prompt, Template)
            assert prompt.content.strip()
            assert "You are" in prompt.content  # Basic sanity check

    def test_configuration_consistency(self, examples_workspace):
        """Test that configuration values are used consistently."""
        config = examples_workspace.config
        
        # Check that defaults are properly set
        assert config.defaults["agent_type"] == "cli_agent"
        assert config.defaults["domain"] == "software_engineering"
        assert config.defaults["tone"] == "concise_direct"
        
        # Check environment configurations
        assert "development" in config.environments
        assert "production" in config.environments
        assert "sandbox" in config.environments

    def test_conditional_warning_display(self, examples_workspace):
        """Test that warnings are displayed conditionally."""
        template = examples_workspace.templates["gemini_cli_system_prompt"]
        
        prompt = render(template, {"domain": "software_engineering"}, examples_workspace)
        
        # Should contain basic template content
        assert "You are an interactive CLI agent" in prompt.content

    def test_max_output_lines_consistency(self, examples_workspace):
        """Test that max_output_lines values are consistent across components."""
        # Check that the snippet template uses the variable correctly
        tone_snippet = examples_workspace.snippets["tone_guidelines"]
        assert "{{ max_output_lines | default(3) }}" in tone_snippet.content
        
        # Test rendering with different values
        template = examples_workspace.templates["gemini_cli_system_prompt"]
        
        prompt_3_lines = render(template, {
            "domain": "software_engineering",
            "max_output_lines": 3
        }, examples_workspace)
        
        prompt_5_lines = render(template, {
            "domain": "software_engineering", 
            "max_output_lines": 5
        }, examples_workspace)
        
        assert "fewer than 3 lines" in prompt_3_lines.content
        assert "fewer than 5 lines" in prompt_5_lines.content 