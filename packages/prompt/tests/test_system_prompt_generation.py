"""Tests for system prompt generation."""

from republic_prompt.loader import load_workspace
from republic_prompt.renderer import render


class TestSystemPromptGeneration:
    """Test system prompt generation functionality."""

    def setup_method(self):
        """Set up test workspace."""
        self.workspace = load_workspace("packages/prompt/examples")

    def test_gemini_cli_system_prompt_renders(self):
        """Test that the main Gemini CLI system prompt template renders successfully."""
        template = self.workspace.templates["gemini_cli_system_prompt"]

        # Test with full configuration
        variables = {
            "use_tools": True,
            "include_workflows": True,
            "include_examples": True,
            "max_output_lines": 8,
        }

        result = render(template, variables, workspace=self.workspace)

        assert isinstance(result.content, str)
        assert len(result.content) > 0
        assert "You are an interactive CLI agent" in result.content

    def test_simple_agent_template_renders(self):
        """Test that the simple agent template renders successfully."""
        template = self.workspace.templates["simple_agent"]

        variables = {
            "use_tools": False,
            "include_workflows": False,
            "include_examples": False,
            "max_output_lines": 3,
        }

        result = render(template, variables, workspace=self.workspace)

        assert isinstance(result.content, str)
        assert len(result.content) > 0
        assert "agent" in result.content.lower()

    def test_command_safety_snippet_renders_with_arrays(self):
        """Test that command safety snippet renders using array-based functions."""
        from republic_prompt.renderer import render_snippet

        snippet = self.workspace.snippets["command_safety"]

        result = render_snippet(snippet, {}, workspace=self.workspace)

        assert isinstance(result, str)
        assert len(result) > 0

        # Should contain rendered examples from arrays
        assert "rm -rf" in result
        assert "server" in result.lower()
        assert "Example" in result
        assert "Background Process" in result

    def test_environment_detection_snippet_renders(self):
        """Test that environment detection snippet renders successfully."""
        from republic_prompt.renderer import render_snippet

        snippet = self.workspace.snippets["environment_detection"]

        result = render_snippet(snippet, {}, workspace=self.workspace)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_core_mandates_snippet_renders(self):
        """Test that core mandates snippet renders successfully."""
        from republic_prompt.renderer import render_snippet

        snippet = self.workspace.snippets["core_mandates"]

        result = render_snippet(snippet, {}, workspace=self.workspace)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_tone_guidelines_snippet_renders(self):
        """Test that tone guidelines snippet renders successfully."""
        from republic_prompt.renderer import render_snippet

        snippet = self.workspace.snippets["tone_guidelines"]

        result = render_snippet(snippet, {}, workspace=self.workspace)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_template_with_conditional_rendering(self):
        """Test template rendering with conditional logic."""
        template = self.workspace.templates["gemini_cli_system_prompt"]

        # Test with tools enabled
        with_tools = render(template, {"use_tools": True}, workspace=self.workspace)

        # Test with tools disabled
        without_tools = render(template, {"use_tools": False}, workspace=self.workspace)

        # With tools should be longer and contain tool information
        assert len(with_tools.content) > len(without_tools.content)

        # Tool-specific content should only appear when tools are enabled
        if "Tool Usage" in with_tools.content:
            assert "Tool Usage" not in without_tools.content or len(
                with_tools.content
            ) > len(without_tools.content)

    def test_template_variable_substitution(self):
        """Test that template variables are properly substituted."""
        template = self.workspace.templates["gemini_cli_system_prompt"]

        # Test different max_output_lines values
        result_8 = render(template, {"max_output_lines": 8}, workspace=self.workspace)
        result_2 = render(template, {"max_output_lines": 2}, workspace=self.workspace)

        # Both should render successfully
        assert isinstance(result_8.content, str) and len(result_8.content) > 0
        assert isinstance(result_2.content, str) and len(result_2.content) > 0

        # Should contain the specified values
        assert "8" in result_8.content
        assert "2" in result_2.content

    def test_function_calls_in_templates(self):
        """Test that function calls work properly in templates."""
        template = self.workspace.templates["gemini_cli_system_prompt"]

        result = render(template, {"use_tools": True}, workspace=self.workspace)

        # Should contain content from function calls
        functions_dict = self.workspace.get_functions_dict()
        tools = functions_dict["get_available_tools"]()
        for tool in tools:
            assert tool in result.content

    def test_array_iteration_in_templates(self):
        """Test that array iteration works in templates."""
        # Create a simple test template that uses array iteration
        test_template_content = """
        {% for example in get_dangerous_command_examples() %}
        Command: {{ example.command }}
        Explanation: {{ example.explanation }}
        {% endfor %}
        """

        from republic_prompt.core import Template

        test_template = Template(name="test_template", content=test_template_content)

        result = render(test_template, {}, workspace=self.workspace)

        # Should contain rendered examples
        assert "Command:" in result.content
        assert "Explanation:" in result.content
        assert "rm -rf" in result.content

    def test_nested_function_calls(self):
        """Test that nested function calls work in templates."""
        template = self.workspace.templates["gemini_cli_system_prompt"]

        result = render(
            template,
            {"use_tools": True, "include_workflows": True, "include_examples": True},
            workspace=self.workspace,
        )

        # Should contain content from multiple function calls
        assert len(result.content) > 0

        # Check for content from different function categories
        functions_dict = self.workspace.get_functions_dict()
        tools = functions_dict["get_available_tools"]()

        for tool in tools:
            assert tool in result.content

    def test_error_handling_in_rendering(self):
        """Test error handling during template rendering."""
        template = self.workspace.templates["gemini_cli_system_prompt"]

        # Test with missing required variables - should still render
        result = render(template, {}, workspace=self.workspace)
        assert isinstance(result.content, str)
        assert len(result.content) > 0

    def test_examples_snippet_renders(self):
        """Test that examples snippet renders successfully."""
        from republic_prompt.renderer import render_snippet

        snippet = self.workspace.snippets["examples"]

        result = render_snippet(snippet, {}, workspace=self.workspace)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_all_snippets_render_independently(self):
        """Test that all snippets can render independently."""
        from republic_prompt.renderer import render_snippet

        for snippet_name, snippet in self.workspace.snippets.items():
            result = render_snippet(snippet, {}, workspace=self.workspace)
            assert isinstance(result, str), f"Snippet {snippet_name} failed to render"
            assert len(result) > 0, f"Snippet {snippet_name} rendered empty"

    def test_template_output_contains_expected_sections(self):
        """Test that rendered templates contain expected sections."""
        template = self.workspace.templates["gemini_cli_system_prompt"]

        result = render(
            template,
            {
                "use_tools": True,
                "include_workflows": True,
                "include_examples": True,
                "max_output_lines": 8,
            },
            workspace=self.workspace,
        )

        # Should contain major sections
        expected_sections = ["Core Mandates", "Tool Usage", "Security and Safety Rules"]

        for section in expected_sections:
            assert section in result.content, f"Missing section: {section}"

    def test_command_examples_properly_rendered(self):
        """Test that command examples are properly rendered from arrays."""
        from republic_prompt.renderer import render_snippet

        snippet = self.workspace.snippets["command_safety"]

        result = render_snippet(snippet, {}, workspace=self.workspace)

        # Should contain examples from the arrays
        functions_dict = self.workspace.get_functions_dict()
        dangerous_examples = functions_dict["get_dangerous_command_examples"]()
        background_examples = functions_dict["get_background_command_examples"]()

        # Check that at least some examples are rendered
        found_dangerous = any(ex["command"] in result for ex in dangerous_examples)
        found_background = any(ex["command"] in result for ex in background_examples)

        assert found_dangerous, "No dangerous command examples found in rendered output"
        assert found_background, (
            "No background command examples found in rendered output"
        )

    def test_function_return_values_used_correctly(self):
        """Test that function return values are used correctly in templates."""
        # Test that array functions return arrays
        functions_dict = self.workspace.get_functions_dict()
        dangerous_examples = functions_dict["get_dangerous_command_examples"]()
        background_examples = functions_dict["get_background_command_examples"]()

        assert isinstance(dangerous_examples, list)
        assert isinstance(background_examples, list)
        assert len(dangerous_examples) > 0
        assert len(background_examples) > 0

        # Test that each example has the expected structure
        for example in dangerous_examples:
            assert "command" in example
            assert "explanation" in example

        for example in background_examples:
            assert "command" in example
            assert "explanation" in example
