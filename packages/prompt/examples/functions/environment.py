"""Environment detection functions - equivalent to Google's environment detection."""

import os
import subprocess
import platform


def get_sandbox_status() -> str:
    """
    Detect sandbox status.
    Equivalent to Google's sandbox detection logic.
    Returns: "macos_seatbelt", "generic_sandbox", or "no_sandbox"
    """
    # Check for macOS Seatbelt (equivalent to process.env.SANDBOX === 'sandbox-exec')
    if platform.system() == "Darwin" and os.environ.get("SANDBOX") == "sandbox-exec":
        return "macos_seatbelt"

    # Check for generic sandbox (equivalent to !!process.env.SANDBOX)
    if os.environ.get("SANDBOX"):
        return "generic_sandbox"

    # Check for container indicators
    if os.path.exists("/.dockerenv") or os.environ.get("container"):
        return "generic_sandbox"

    return "no_sandbox"


def is_git_repository() -> bool:
    """
    Check if current directory is a git repository.
    Equivalent to Google's isGitRepository(process.cwd()) function.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def should_show_git_warning() -> bool:
    """
    Determine if git-related warnings should be shown.
    Based on Google's conditional git section logic.
    """
    return is_git_repository()


def should_show_sandbox_warning() -> bool:
    """
    Determine if sandbox-related warnings should be shown.
    Based on Google's conditional sandbox section logic.
    """
    return get_sandbox_status() != "no_sandbox"


def get_git_workflow_instructions() -> str:
    """
    Get git workflow instructions.
    Based on Google's git repository conditional section.
    """
    return """
# Git Repository
- The current working (project) directory is being managed by a git repository.
- When asked to commit changes or prepare a commit, always start by gathering information using shell commands:
  - `git status` to ensure that all relevant files are tracked and staged, using `git add ...` as needed.
  - `git diff HEAD` to review all changes (including unstaged changes) to tracked files in work tree since last commit.
    - `git diff --staged` to review only staged changes when a partial commit makes sense or was requested by the user.
  - `git log -n 3` to review recent commit messages and match their style (verbosity, formatting, signature line, etc.)
- Combine shell commands whenever possible to save time/steps, e.g. `git status && git diff HEAD && git log -n 3`.
- Always propose a draft commit message. Never just ask the user to give you the full commit message.
- Prefer commit messages that are clear, concise, and focused more on "why" and less on "what".
- Keep the user informed and ask for clarification or confirmation where needed.
- After each commit, confirm that it was successful by running `git status`.
- If a commit fails, never attempt to work around the issues without being asked to do so.
- Never push changes to a remote repository without being asked explicitly by the user.
""".strip()


# Export functions using WORKSPACE_FUNCTIONS convention
WORKSPACE_FUNCTIONS = {
    "get_sandbox_status": get_sandbox_status,
    "is_git_repository": is_git_repository,
    "should_show_git_warning": should_show_git_warning,
    "should_show_sandbox_warning": should_show_sandbox_warning,
    "get_git_workflow_instructions": get_git_workflow_instructions,
}
