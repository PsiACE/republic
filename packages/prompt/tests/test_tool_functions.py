"""Tests for tool functions and command safety."""

from republic_prompt.loader import load_workspace


class TestToolFunctions:
    """Test tool-related functionality."""

    def setup_method(self):
        """Set up test workspace."""
        self.workspace = load_workspace("packages/prompt/examples")
        # Get the actual callable functions
        self.functions = self.workspace.get_functions_dict()

    def test_get_available_tools(self):
        """Test that available tools are properly listed."""
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

        assert isinstance(tools, list)
        assert len(tools) == len(expected_tools)

        for tool in expected_tools:
            assert tool in tools

    def test_get_dangerous_command_examples(self):
        """Test dangerous command examples for template rendering."""
        examples = self.functions["get_dangerous_command_examples"]()

        assert isinstance(examples, list)
        assert len(examples) > 0

        # Check structure of examples
        for example in examples:
            assert isinstance(example, dict)
            assert "command" in example
            assert "explanation" in example
            assert isinstance(example["command"], str)
            assert isinstance(example["explanation"], str)
            assert len(example["command"]) > 0
            assert len(example["explanation"]) > 0

        # Check for specific dangerous commands
        commands = [ex["command"] for ex in examples]
        assert any("rm -rf" in cmd for cmd in commands)
        assert any("git reset --hard" in cmd for cmd in commands)
        assert any("chmod 777" in cmd for cmd in commands)

    def test_get_background_command_examples(self):
        """Test background command examples for template rendering."""
        examples = self.functions["get_background_command_examples"]()

        assert isinstance(examples, list)
        assert len(examples) > 0

        # Check structure of examples
        for example in examples:
            assert isinstance(example, dict)
            assert "command" in example
            assert "explanation" in example
            assert isinstance(example["command"], str)
            assert isinstance(example["explanation"], str)
            assert len(example["command"]) > 0
            assert len(example["explanation"]) > 0

        # Check for specific background commands
        commands = [ex["command"] for ex in examples]
        assert any("server" in cmd for cmd in commands)
        assert any("npm run dev" in cmd for cmd in commands)
        assert any("webpack --watch" in cmd for cmd in commands)

    def test_get_dangerous_patterns(self):
        """Test dangerous command patterns."""
        patterns = self.functions["get_dangerous_patterns"]()

        assert isinstance(patterns, list)
        assert len(patterns) > 0

        expected_patterns = [
            "rm ",
            "sudo",
            "chmod",
            "git reset --hard",
            "shutdown",
            "kill",
        ]

        for pattern in expected_patterns:
            assert pattern in patterns

    def test_get_background_patterns(self):
        """Test background command patterns."""
        patterns = self.functions["get_background_patterns"]()

        assert isinstance(patterns, list)
        assert len(patterns) > 0

        expected_patterns = ["server", "watch", "dev", "daemon", "service"]

        for pattern in expected_patterns:
            assert pattern in patterns

    def test_should_explain_command_dangerous(self):
        """Test command explanation detection for dangerous commands."""
        should_explain = self.functions["should_explain_command"]

        dangerous_commands = [
            "rm -rf /tmp/test",
            "sudo rm file.txt",
            "chmod 777 ~/.ssh/",
            "git reset --hard HEAD~5",
            "kill -9 1234",
            "shutdown now",
            "npm install -g package",
        ]

        for cmd in dangerous_commands:
            assert should_explain(cmd) is True, (
                f"Should explain dangerous command: {cmd}"
            )

    def test_should_explain_command_safe(self):
        """Test command explanation detection for safe commands."""
        should_explain = self.functions["should_explain_command"]

        safe_commands = [
            "ls -la",
            "cat file.txt",
            "echo hello",
            "pwd",
            "whoami",
            "date",
            "git status",
        ]

        for cmd in safe_commands:
            assert should_explain(cmd) is False, (
                f"Should not explain safe command: {cmd}"
            )

    def test_should_run_in_background_long_running(self):
        """Test background detection for long-running commands."""
        should_run_bg = self.functions["should_run_in_background"]

        background_commands = [
            "node server.js",
            "python -m http.server 8000",
            "npm run dev",
            "webpack --watch",
            "nodemon app.js",
            "webpack-dev-server",
        ]

        for cmd in background_commands:
            assert should_run_bg(cmd) is True, f"Should run in background: {cmd}"

    def test_should_run_in_background_short_running(self):
        """Test background detection for short-running commands."""
        should_run_bg = self.functions["should_run_in_background"]

        foreground_commands = [
            "ls -la",
            "cat file.txt",
            "git status",
            "npm test",
            "python script.py",
            "make build",
        ]

        for cmd in foreground_commands:
            assert should_run_bg(cmd) is False, f"Should not run in background: {cmd}"

    def test_format_tool_usage_guidelines(self):
        """Test tool usage guidelines formatting."""
        guidelines = self.functions["format_tool_usage_guidelines"]()

        assert isinstance(guidelines, str)
        assert len(guidelines) > 0

        # Check for key content
        assert "Tool Usage" in guidelines
        assert "File Paths" in guidelines
        assert "Parallelism" in guidelines
        assert "Command Execution" in guidelines
        assert "Background Processes" in guidelines
        assert "Interactive Commands" in guidelines
        assert "Respect User Confirmations" in guidelines

        # Check that all tools are mentioned
        tools = self.functions["get_available_tools"]()
        for tool in tools:
            assert tool in guidelines

    def test_get_security_guidelines(self):
        """Test security guidelines generation."""
        guidelines = self.functions["get_security_guidelines"]()

        assert isinstance(guidelines, str)
        assert len(guidelines) > 0

        # Check for key security content
        assert "Security and Safety Rules" in guidelines
        assert "Explain Critical Commands" in guidelines
        assert "Security First" in guidelines
        assert "secrets" in guidelines.lower()
        assert "api keys" in guidelines.lower()

    def test_tool_functions_are_callable(self):
        """Test that all tool functions are properly callable."""
        required_functions = [
            "get_available_tools",
            "get_dangerous_command_examples",
            "get_background_command_examples",
            "get_dangerous_patterns",
            "get_background_patterns",
            "should_explain_command",
            "should_run_in_background",
            "format_tool_usage_guidelines",
            "get_security_guidelines",
        ]

        for func_name in required_functions:
            assert func_name in self.functions
            assert callable(self.functions[func_name])

    def test_command_safety_edge_cases(self):
        """Test edge cases for command safety detection."""
        should_explain = self.functions["should_explain_command"]
        should_run_bg = self.functions["should_run_in_background"]

        # Empty command
        assert should_explain("") is False
        assert should_run_bg("") is False

        # Case sensitivity
        assert should_explain("RM -RF /tmp") is True
        assert should_run_bg("NODE SERVER.JS") is True

        # Commands with arguments
        assert should_explain("rm -rf /tmp/test && ls") is True
        assert should_run_bg("node server.js --port 3000") is True

        # Partial matches - "remove file" contains "move" which IS a dangerous pattern
        assert should_explain("remove file") is True  # "remove file" contains "move"
        assert should_explain("show file") is False  # "show" doesn't match any pattern
        assert should_run_bg("start application") is True  # contains "start"

    def test_function_return_types(self):
        """Test that functions return expected data types."""
        # Array functions should return lists
        assert isinstance(self.functions["get_available_tools"](), list)
        assert isinstance(self.functions["get_dangerous_command_examples"](), list)
        assert isinstance(self.functions["get_background_command_examples"](), list)
        assert isinstance(self.functions["get_dangerous_patterns"](), list)
        assert isinstance(self.functions["get_background_patterns"](), list)

        # String functions should return strings
        assert isinstance(self.functions["format_tool_usage_guidelines"](), str)
        assert isinstance(self.functions["get_security_guidelines"](), str)

        # Boolean functions should return booleans
        assert isinstance(self.functions["should_explain_command"]("test"), bool)
        assert isinstance(self.functions["should_run_in_background"]("test"), bool)
