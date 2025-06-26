"""Tool usage and safety functions - equivalent to Google's tool usage guidelines."""

from typing import List, Dict


def get_available_tools() -> List[str]:
    """
    Get list of available tools.
    Equivalent to Google's tool enumeration in getCoreSystemPrompt.
    """
    return [
        "LSTool",
        "EditTool",
        "GlobTool",
        "GrepTool",
        "ReadFileTool",
        "ReadManyFilesTool",
        "ShellTool",
        "WriteFileTool",
    ]


def get_dangerous_command_examples() -> List[Dict[str, str]]:
    """
    Get examples of dangerous commands that should be explained.
    Returns array of command examples with explanations for template rendering.
    """
    return [
        {
            "command": "rm -rf /tmp/test",
            "explanation": "This will permanently delete the directory and all its contents.",
        },
        {
            "command": "sudo rm -rf /var/log/*",
            "explanation": "This will delete all system log files, which may affect debugging.",
        },
        {
            "command": "git reset --hard HEAD~5",
            "explanation": "This will permanently discard the last 5 commits and any uncommitted changes.",
        },
        {
            "command": "chmod 777 ~/.ssh/",
            "explanation": "This makes SSH keys readable by all users, creating a security risk.",
        },
    ]


def get_background_command_examples() -> List[Dict[str, str]]:
    """
    Get examples of commands that should run in background.
    Returns array of command examples for template rendering.
    """
    return [
        {
            "command": "node server.js",
            "explanation": "Long-running server should use background execution with `&`",
        },
        {
            "command": "python -m http.server 8000",
            "explanation": "HTTP server should run in background to avoid blocking terminal",
        },
        {
            "command": "npm run dev",
            "explanation": "Development server should run in background for continuous operation",
        },
        {
            "command": "webpack --watch",
            "explanation": "File watcher should run in background to monitor changes",
        },
    ]


def get_dangerous_patterns() -> List[str]:
    """
    Get patterns that indicate dangerous commands.
    Used internally for command analysis.
    """
    return [
        "rm ",
        "del ",
        "delete",
        "mv ",
        "move",
        "cp ",
        "copy",
        "chmod",
        "chown",
        "sudo",
        "su ",
        "install",
        "uninstall",
        "format",
        "fdisk",
        "kill",
        "killall",
        "shutdown",
        "reboot",
        "git push",
        "git reset --hard",
        "npm install -g",
        "pip install",
        "make install",
        "make clean",
    ]


def get_background_patterns() -> List[str]:
    """
    Get patterns that indicate background commands.
    Used internally for command analysis.
    """
    return [
        "server",
        "serve",
        "watch",
        "monitor",
        "daemon",
        "service",
        "dev",
        "start",
        "nodemon",
        "webpack-dev-server",
        "python -m http.server",
        "node server.js",
    ]


def should_explain_command(command: str) -> bool:
    """
    Determine if a shell command should be explained before execution.
    Based on Google's "Explain Critical Commands" rule.
    """
    dangerous_patterns = get_dangerous_patterns()
    command_lower = command.lower()
    return any(pattern in command_lower for pattern in dangerous_patterns)


def should_run_in_background(command: str) -> bool:
    """
    Determine if a command should run in background.
    Based on Google's background process guidelines.
    """
    background_patterns = get_background_patterns()
    command_lower = command.lower()
    return any(pattern in command_lower for pattern in background_patterns)


def format_tool_usage_guidelines() -> str:
    """
    Format tool usage guidelines.
    Based on Google's "Tool Usage" section.
    """
    tools = get_available_tools()
    tool_list = ", ".join(f"'{tool}'" for tool in tools)

    return f"""
## Tool Usage

- **File Paths:** Always use absolute paths when referring to files with tools like 'ReadFileTool' or 'WriteFileTool'. Relative paths are not supported.
- **Parallelism:** Execute multiple independent tool calls in parallel when feasible (i.e. searching the codebase).
- **Command Execution:** Use the 'ShellTool' for running shell commands, remembering the safety rule to explain modifying commands first.
- **Background Processes:** Use background processes (via `&`) for commands that are unlikely to stop on their own, e.g. `node server.js &`. If unsure, ask the user.
- **Interactive Commands:** Try to avoid shell commands that are likely to require user interaction (e.g. `git rebase -i`). Use non-interactive versions when available.
- **Respect User Confirmations:** Most tool calls will first require confirmation from the user. If a user cancels a function call, respect their choice and do not try to make the function call again.

Available tools: {tool_list}
""".strip()


def get_security_guidelines() -> str:
    """
    Get security and safety guidelines.
    Based on Google's security rules.
    """
    return """
## Security and Safety Rules

- **Explain Critical Commands:** Before executing commands that modify the file system, codebase, or system state, you *must* provide a brief explanation of the command's purpose and potential impact. Prioritize user understanding and safety.
- **Security First:** Always apply security best practices. Never introduce code that exposes, logs, or commits secrets, API keys, or other sensitive information.
""".strip()


# Export functions using WORKSPACE_FUNCTIONS convention
WORKSPACE_FUNCTIONS = {
    "get_available_tools": get_available_tools,
    "get_dangerous_command_examples": get_dangerous_command_examples,
    "get_background_command_examples": get_background_command_examples,
    "get_dangerous_patterns": get_dangerous_patterns,
    "get_background_patterns": get_background_patterns,
    "should_explain_command": should_explain_command,
    "should_run_in_background": should_run_in_background,
    "format_tool_usage_guidelines": format_tool_usage_guidelines,
    "get_security_guidelines": get_security_guidelines,
}
