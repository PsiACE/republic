"""Test cases for tool-related functions."""

from pathlib import Path
import sys

# Import the functions we want to test
sys.path.insert(0, str(Path(__file__).parent.parent / "examples" / "functions"))

from tools import (
    get_available_tools,
    should_explain_command,
    get_command_explanation,
    should_run_in_background,
    make_command_non_interactive,
    get_parallel_tool_suggestions,
    format_tool_usage_guidelines,
    get_security_guidelines,
    should_ask_for_confirmation
)

class TestToolListing:
    """Test tool listing functionality."""

    def test_get_available_tools_returns_expected_tools(self):
        """Test that all expected tools are listed."""
        tools = get_available_tools()
        
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
        
        for tool in expected_tools:
            assert tool in tools, f"Expected tool {tool} not found in list"

    def test_get_available_tools_no_memory_tool(self):
        """Test that MemoryTool is not in the list (as it's not implemented)."""
        tools = get_available_tools()
        assert "MemoryTool" not in tools


class TestCommandSafety:
    """Test command safety analysis."""

    def test_should_explain_dangerous_commands(self):
        """Test that dangerous commands are flagged for explanation."""
        dangerous_commands = [
            "rm -rf /tmp/test",
            "sudo apt install package",
            "git push origin main",
            "chmod 777 file.txt",
            "mv important.txt /tmp/",
            "npm install -g package"
        ]
        
        for cmd in dangerous_commands:
            assert should_explain_command(cmd), f"Command should be explained: {cmd}"

    def test_should_not_explain_safe_commands(self):
        """Test that safe commands are not flagged."""
        safe_commands = [
            "ls -la",
            "cat file.txt", 
            "grep pattern file.txt",
            "echo 'hello world'",
            "pwd",
            "date"
        ]
        
        for cmd in safe_commands:
            assert not should_explain_command(cmd), f"Command should not be explained: {cmd}"

    def test_get_command_explanation_provides_context(self):
        """Test that command explanations provide useful context."""
        test_cases = [
            ("rm -rf /tmp/test", "permanently delete"),
            ("sudo apt install", "elevated privileges"),
            ("git push origin", "push changes to remote"),
            ("chmod 755 file", "change file permissions")
        ]
        
        for cmd, expected_phrase in test_cases:
            explanation = get_command_explanation(cmd)
            assert expected_phrase.lower() in explanation.lower()
            assert cmd in explanation

    def test_should_ask_for_confirmation_high_risk(self):
        """Test that high-risk commands require confirmation."""
        high_risk_commands = [
            "rm -rf /",
            "git push --force", 
            "git reset --hard HEAD~5",
            "sudo rm -rf /usr",
            "format C:"
        ]
        
        for cmd in high_risk_commands:
            assert should_ask_for_confirmation(cmd), f"Should ask confirmation for: {cmd}"


class TestBackgroundProcessDetection:
    """Test background process detection."""

    def test_should_run_in_background_server_commands(self):
        """Test that server commands are flagged for background execution."""
        server_commands = [
            "node server.js",
            "python -m http.server 8000",
            "npm run dev",
            "webpack-dev-server",
            "nodemon app.js"
        ]
        
        for cmd in server_commands:
            assert should_run_in_background(cmd), f"Command should run in background: {cmd}"

    def test_should_not_run_in_background_regular_commands(self):
        """Test that regular commands are not flagged for background."""
        regular_commands = [
            "ls -la",
            "npm test",
            "git status", 
            "python script.py"
        ]
        
        for cmd in regular_commands:
            assert not should_run_in_background(cmd), f"Command should not run in background: {cmd}"


class TestInteractiveCommandConversion:
    """Test interactive command conversion."""

    def test_make_command_non_interactive(self):
        """Test conversion of interactive commands to non-interactive."""
        test_cases = [
            ("npm init", "npm init -y"),
            ("yarn init", "yarn init -y"),
            ("pip install package", "pip install --no-input package"),
        ]
        
        for interactive, expected in test_cases:
            result = make_command_non_interactive(interactive)
            assert result == expected, f"Expected {expected}, got {result}"

    def test_non_interactive_commands_unchanged(self):
        """Test that already non-interactive commands remain unchanged."""
        commands = [
            "npm install -y",
            "ls -la",
            "git status"
        ]
        
        for cmd in commands:
            result = make_command_non_interactive(cmd)
            assert result == cmd, f"Command should remain unchanged: {cmd}"


class TestParallelToolSuggestions:
    """Test parallel tool execution suggestions."""

    def test_search_tasks_suggest_parallel_tools(self):
        """Test that search tasks suggest appropriate parallel tools."""
        search_descriptions = [
            "search for function definitions",
            "find all imports",
            "look for usage patterns"
        ]
        
        for desc in search_descriptions:
            suggestions = get_parallel_tool_suggestions(desc)
            assert "GrepTool" in suggestions or "GlobTool" in suggestions

    def test_read_tasks_suggest_parallel_tools(self):
        """Test that read tasks suggest appropriate parallel tools."""
        read_descriptions = [
            "read multiple files",
            "analyze codebase structure", 
            "understand project layout"
        ]
        
        for desc in read_descriptions:
            suggestions = get_parallel_tool_suggestions(desc)
            assert len(suggestions) > 0
            assert any("Read" in tool for tool in suggestions)

    def test_explore_tasks_suggest_multiple_tools(self):
        """Test that exploration tasks suggest multiple tools."""
        explore_descriptions = [
            "understand the codebase",
            "explore project structure"
        ]
        
        for desc in explore_descriptions:
            suggestions = get_parallel_tool_suggestions(desc)
            assert len(suggestions) >= 2  # Should suggest multiple tools


class TestGuidelineFormatting:
    """Test guideline formatting functions."""

    def test_format_tool_usage_guidelines_contains_key_points(self):
        """Test that tool usage guidelines contain key information."""
        guidelines = format_tool_usage_guidelines()
        
        key_points = [
            "absolute paths",
            "parallel",
            "ShellTool",
            "background processes",
            "interactive commands"
        ]
        
        for point in key_points:
            assert point.lower() in guidelines.lower(), f"Missing key point: {point}"

    def test_get_security_guidelines_contains_safety_rules(self):
        """Test that security guidelines contain safety rules."""
        guidelines = get_security_guidelines()
        
        safety_rules = [
            "Critical Commands",
            "Security First",
            "User Control",
            "No Assumptions"
        ]
        
        for rule in safety_rules:
            assert rule in guidelines, f"Missing safety rule: {rule}"

    def test_guidelines_are_properly_formatted(self):
        """Test that guidelines are properly formatted as markdown."""
        tool_guidelines = format_tool_usage_guidelines()
        security_guidelines = get_security_guidelines()
        
        # Should contain markdown headers
        assert "##" in tool_guidelines
        assert "##" in security_guidelines
        
        # Should contain bullet points
        assert "- **" in tool_guidelines
        assert "- **" in security_guidelines 