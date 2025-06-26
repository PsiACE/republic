"""Tests for examples directory functionality."""

from republic_prompt.loader import load_workspace


class TestExamplesWorkspace:
    """Test examples workspace loading and functionality."""

    def setup_method(self):
        """Set up test workspace."""
        self.workspace = load_workspace("packages/prompt/examples")
        # Get the actual callable functions
        self.functions = self.workspace.get_functions_dict()

    def test_workspace_loads_successfully(self):
        """Test that examples workspace loads without errors."""
        assert self.workspace is not None
        assert hasattr(self.workspace, "functions")
        assert hasattr(self.workspace, "templates")
        assert hasattr(self.workspace, "snippets")

    def test_all_functions_loaded(self):
        """Test that all expected functions are loaded."""
        expected_functions = [
            # Environment functions
            "should_show_git_warning",
            "should_show_sandbox_warning",
            "get_sandbox_status",
            "is_git_repository",
            "get_git_workflow_instructions",
            # Tool functions
            "get_available_tools",
            "get_dangerous_command_examples",
            "get_background_command_examples",
            "get_dangerous_patterns",
            "get_background_patterns",
            "should_explain_command",
            "should_run_in_background",
            "format_tool_usage_guidelines",
            "get_security_guidelines",
            # Workflow functions
            "get_software_engineering_workflow",
            "get_new_application_workflow",
            "get_example_interactions",
        ]

        for func_name in expected_functions:
            assert func_name in self.functions
            assert callable(self.functions[func_name])

    def test_all_templates_loaded(self):
        """Test that all expected templates are loaded."""
        expected_templates = ["gemini_cli_system_prompt", "simple_agent"]

        for template_name in expected_templates:
            assert template_name in self.workspace.templates

    def test_all_snippets_loaded(self):
        """Test that all expected snippets are loaded."""
        expected_snippets = [
            "command_safety",
            "core_mandates",
            "environment_detection",
            "tone_guidelines",
            "examples",
        ]

        for snippet_name in expected_snippets:
            assert snippet_name in self.workspace.snippets

    def test_functions_return_expected_types(self):
        """Test that functions return expected data types."""
        # Test array functions
        assert isinstance(self.functions["get_available_tools"](), list)
        assert isinstance(self.functions["get_dangerous_command_examples"](), list)
        assert isinstance(self.functions["get_background_command_examples"](), list)
        assert isinstance(self.functions["get_example_interactions"](), list)

        # Test string functions
        assert isinstance(self.functions["format_tool_usage_guidelines"](), str)
        assert isinstance(self.functions["get_security_guidelines"](), str)
        assert isinstance(self.functions["get_git_workflow_instructions"](), str)
        assert isinstance(self.functions["get_software_engineering_workflow"](), str)
        assert isinstance(self.functions["get_new_application_workflow"](), str)

        # Test boolean functions
        assert isinstance(self.functions["should_show_git_warning"](), bool)
        assert isinstance(self.functions["should_show_sandbox_warning"](), bool)
        assert isinstance(self.functions["should_explain_command"]("test"), bool)
        assert isinstance(self.functions["should_run_in_background"]("test"), bool)

    def test_dangerous_command_examples_structure(self):
        """Test structure of dangerous command examples for template usage."""
        examples = self.functions["get_dangerous_command_examples"]()

        assert len(examples) > 0
        for example in examples:
            assert isinstance(example, dict)
            assert "command" in example
            assert "explanation" in example
            assert isinstance(example["command"], str)
            assert isinstance(example["explanation"], str)
            assert len(example["command"]) > 0
            assert len(example["explanation"]) > 0

    def test_background_command_examples_structure(self):
        """Test structure of background command examples for template usage."""
        examples = self.functions["get_background_command_examples"]()

        assert len(examples) > 0
        for example in examples:
            assert isinstance(example, dict)
            assert "command" in example
            assert "explanation" in example
            assert isinstance(example["command"], str)
            assert isinstance(example["explanation"], str)
            assert len(example["command"]) > 0
            assert len(example["explanation"]) > 0

    def test_example_interactions_structure(self):
        """Test structure of example interactions."""
        examples = self.functions["get_example_interactions"]()

        assert isinstance(examples, list)
        assert len(examples) > 0

        for example in examples:
            assert isinstance(example, dict)
            assert "user" in example
            assert "model" in example
            assert isinstance(example["user"], str)
            assert isinstance(example["model"], str)

    def test_available_tools_completeness(self):
        """Test that available tools list is complete and correct."""
        tools = self.functions["get_available_tools"]()

        expected_tools = [
            "LSTool",
            "EditTool",
            "GlobTool",
            "GrepTool",
            "ReadFileTool",
            "ReadManyFilesTool",
            "ShellTool",
            "WriteFileTool",
        ]

        assert len(tools) == len(expected_tools)
        for tool in expected_tools:
            assert tool in tools

    def test_pattern_arrays_not_empty(self):
        """Test that pattern arrays contain expected patterns."""
        dangerous_patterns = self.functions["get_dangerous_patterns"]()
        background_patterns = self.functions["get_background_patterns"]()

        assert len(dangerous_patterns) > 0
        assert len(background_patterns) > 0

        # Check for some expected patterns
        assert "rm " in dangerous_patterns
        assert "sudo" in dangerous_patterns
        assert "server" in background_patterns
        assert "watch" in background_patterns

    def test_guidelines_formatting(self):
        """Test that guidelines are properly formatted."""
        tool_guidelines = self.functions["format_tool_usage_guidelines"]()
        security_guidelines = self.functions["get_security_guidelines"]()

        # All should be non-empty strings
        assert isinstance(tool_guidelines, str) and len(tool_guidelines) > 0
        assert isinstance(security_guidelines, str) and len(security_guidelines) > 0

        # Should contain markdown formatting
        assert "##" in tool_guidelines
        assert "##" in security_guidelines

    def test_sandbox_status_values(self):
        """Test that sandbox status returns valid values."""
        status = self.functions["get_sandbox_status"]()
        valid_statuses = ["macos_seatbelt", "generic_sandbox", "no_sandbox"]
        assert status in valid_statuses

    def test_function_consistency(self):
        """Test consistency between related functions."""
        # Tool list should be consistent
        tools_from_function = self.functions["get_available_tools"]()
        guidelines = self.functions["format_tool_usage_guidelines"]()

        for tool in tools_from_function:
            assert tool in guidelines

        # Dangerous patterns should be used in command detection
        dangerous_patterns = self.functions["get_dangerous_patterns"]()
        should_explain = self.functions["should_explain_command"]

        # Test that at least some dangerous patterns trigger explanation
        for pattern in dangerous_patterns[:3]:  # Test first few patterns
            test_command = f"test {pattern} something"
            assert should_explain(test_command) is True

    def test_array_based_template_usage(self):
        """Test that functions return arrays suitable for template iteration."""
        # Test dangerous command examples
        dangerous_examples = self.functions["get_dangerous_command_examples"]()
        assert isinstance(dangerous_examples, list)
        assert all("command" in ex and "explanation" in ex for ex in dangerous_examples)

        # Test background command examples
        background_examples = self.functions["get_background_command_examples"]()
        assert isinstance(background_examples, list)
        assert all(
            "command" in ex and "explanation" in ex for ex in background_examples
        )

        # Test example interactions
        example_interactions = self.functions["get_example_interactions"]()
        assert isinstance(example_interactions, list)
        assert all("user" in ex and "model" in ex for ex in example_interactions)
