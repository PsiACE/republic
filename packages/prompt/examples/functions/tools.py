"""Tool usage and safety functions - equivalent to Google's tool usage guidelines."""

from typing import List


def get_available_tools() -> List[str]:
    """
    Get list of available tools.
    Equivalent to Google's tool enumeration.
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


def should_explain_command(command: str) -> bool:
    """
    Determine if a shell command should be explained before execution.
    Based on Google's "Explain Critical Commands" rule.
    """
    dangerous_patterns = [
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

    command_lower = command.lower()
    return any(pattern in command_lower for pattern in dangerous_patterns)


def get_command_explanation(command: str) -> str:
    """
    Generate explanation for potentially dangerous commands.
    Following Google's safety-first approach.
    """
    explanations = {
        "rm ": "This will permanently delete files/directories",
        "mv ": "This will move/rename files or directories",
        "chmod": "This will change file permissions",
        "sudo": "This will run commands with elevated privileges",
        "git push": "This will push changes to remote repository",
        "git reset --hard": "This will permanently discard local changes",
        "npm install": "This will install npm packages",
        "pip install": "This will install Python packages",
    }

    command_lower = command.lower()
    for pattern, explanation in explanations.items():
        if pattern in command_lower:
            return f"{explanation}. Command: `{command}`"

    return f"This command may modify the system. Command: `{command}`"


def should_run_in_background(command: str) -> bool:
    """
    Determine if a command should run in background.
    Based on Google's background process guidelines.
    """
    background_patterns = [
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

    command_lower = command.lower()
    return any(pattern in command_lower for pattern in background_patterns)


def make_command_non_interactive(command: str) -> str:
    """
    Convert interactive commands to non-interactive versions.
    Following Google's non-interactive command preference.
    """
    replacements = {
        "npm init": "npm init -y",
        "git rebase -i": "git rebase",
        "yarn init": "yarn init -y",
        "pip install ": "pip install --no-input ",
    }

    for interactive, non_interactive in replacements.items():
        if interactive in command:
            return command.replace(interactive, non_interactive)

    return command


def get_parallel_tool_suggestions(task_description: str) -> List[str]:
    """
    Suggest tools that can be run in parallel for a given task.
    Based on Google's parallelism guidelines.
    """
    task_lower = task_description.lower()
    
    if "search" in task_lower or "find" in task_lower:
        return ["GrepTool", "GlobTool"]

    if "read" in task_lower or "analyze" in task_lower:
        return ["ReadFileTool", "ReadManyFilesTool"]

    if "understand" in task_lower or "explore" in task_lower:
        return ["GrepTool", "GlobTool", "ReadFileTool"]

    # Check for specific keywords that suggest parallel operations
    parallel_keywords = ["definitions", "imports", "patterns", "usage", "multiple", "structure", "layout"]
    if any(keyword in task_lower for keyword in parallel_keywords):
        return ["GrepTool", "GlobTool"]

    return []


def format_tool_usage_guidelines() -> str:
    """
    Format tool usage guidelines.
    Based on Google's tool usage section.
    """
    return """
## Tool Usage Guidelines

- **File Paths:** Always use absolute paths when referring to files with tools
- **Parallelism:** Execute multiple independent tool calls in parallel when feasible  
- **Command Execution:** Use ShellTool for running shell commands, explaining modifying commands first
- **Background Processes:** Use background processes (via `&`) for long-running commands
- **Interactive Commands:** Avoid commands requiring user interaction; use non-interactive versions
- **Safety First:** Explain critical commands before execution
""".strip()


def get_security_guidelines() -> str:
    """
    Get security and safety guidelines.
    Based on Google's security rules.
    """
    return """
## Security and Safety Rules

- **Explain Critical Commands:** Before executing commands that modify the file system, codebase, or system state, provide a brief explanation of the command's purpose and potential impact
- **Security First:** Always apply security best practices. Never introduce code that exposes, logs, or commits secrets, API keys, or other sensitive information
- **User Control:** Always prioritize user control and project conventions
- **No Assumptions:** Never make assumptions on file contents; use ReadFileTool to verify
""".strip()


def should_ask_for_confirmation(command: str) -> bool:
    """
    Determine if user confirmation should be requested.
    Based on Google's user confirmation guidelines.
    """
    high_risk_patterns = [
        "rm -rf",
        "del /s",
        "format",
        "fdisk",
        "git push --force",
        "git reset --hard",
        "sudo rm",
        "sudo chmod",
        "npm uninstall -g",
        "pip uninstall",
    ]

    command_lower = command.lower()
    return any(pattern in command_lower for pattern in high_risk_patterns)
