"""Environment detection functions - equivalent to Google's environment detection."""

import os
import subprocess
import platform
from typing import Dict, Any


def detect_sandbox_environment() -> Dict[str, Any]:
    """
    Detect if running in a sandboxed environment.
    Equivalent to Google's sandbox detection logic.
    """
    sandbox_info = {
        "is_sandboxed": False,
        "sandbox_type": None,
        "restrictions": [],
        "detected_features": [],
    }

    # Check for macOS Seatbelt (App Sandbox)
    if platform.system() == "Darwin":
        try:
            # Check if process is sandboxed
            result = subprocess.run(
                ["codesign", "-d", "--entitlements", "-", "/proc/self/exe"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if "com.apple.security.app-sandbox" in result.stdout:
                sandbox_info.update(
                    {
                        "is_sandboxed": True,
                        "sandbox_type": "macos_app_sandbox",
                        "restrictions": ["file_system", "network", "process_creation"],
                        "detected_features": ["seatbelt"],
                    }
                )
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

    # Check for Linux containers/namespaces
    elif platform.system() == "Linux":
        container_indicators = []

        # Check for Docker
        if os.path.exists("/.dockerenv"):
            container_indicators.append("docker")

        # Check for systemd-nspawn
        if os.environ.get("container") == "systemd-nspawn":
            container_indicators.append("systemd-nspawn")

        # Check cgroup for container hints
        try:
            with open("/proc/1/cgroup", "r") as f:
                cgroup_content = f.read()
                if "docker" in cgroup_content or "lxc" in cgroup_content:
                    container_indicators.append("cgroup_container")
        except (IOError, OSError):
            pass

        if container_indicators:
            sandbox_info.update(
                {
                    "is_sandboxed": True,
                    "sandbox_type": "linux_container",
                    "restrictions": ["process_isolation", "filesystem_isolation"],
                    "detected_features": container_indicators,
                }
            )

    # Generic capability checks
    restricted_capabilities = []

    # Check file system access
    try:
        test_path = "/tmp/republic_prompt_test"
        with open(test_path, "w") as f:
            f.write("test")
        os.remove(test_path)
    except (IOError, OSError, PermissionError):
        restricted_capabilities.append("limited_filesystem_access")

    # Check network access (simplified)
    if os.environ.get("NO_NETWORK") == "1":
        restricted_capabilities.append("no_network_access")

    if restricted_capabilities:
        sandbox_info["restrictions"].extend(restricted_capabilities)
        if not sandbox_info["is_sandboxed"]:
            sandbox_info.update(
                {"is_sandboxed": True, "sandbox_type": "generic_restricted"}
            )

    return sandbox_info


def detect_git_repository() -> Dict[str, Any]:
    """
    Detect Git repository information.
    Equivalent to Google's git detection functionality.
    """
    git_info = {
        "is_git_repo": False,
        "repo_root": None,
        "current_branch": None,
        "has_uncommitted_changes": False,
        "remote_url": None,
    }

    try:
        # Check if we're in a git repository
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode == 0:
            git_info["is_git_repo"] = True
            git_info["repo_root"] = result.stdout.strip()

            # Get current branch
            branch_result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if branch_result.returncode == 0:
                git_info["current_branch"] = branch_result.stdout.strip()

            # Check for uncommitted changes
            status_result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if status_result.returncode == 0:
                git_info["has_uncommitted_changes"] = bool(status_result.stdout.strip())

            # Get remote URL
            remote_result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if remote_result.returncode == 0:
                git_info["remote_url"] = remote_result.stdout.strip()

    except (subprocess.SubprocessError, FileNotFoundError):
        pass

    return git_info


def get_environment_summary() -> str:
    """
    Get a comprehensive environment summary.
    Combines sandbox and git detection for template use.
    """
    sandbox_info = detect_sandbox_environment()
    git_info = detect_git_repository()

    summary_parts = []

    # Sandbox information
    if sandbox_info["is_sandboxed"]:
        sandbox_type = sandbox_info["sandbox_type"]
        restrictions = ", ".join(sandbox_info["restrictions"])
        summary_parts.append(f"Sandboxed environment ({sandbox_type})")
        if restrictions:
            summary_parts.append(f"Restrictions: {restrictions}")
    else:
        summary_parts.append("Unrestricted environment")

    # Git information
    if git_info["is_git_repo"]:
        branch = git_info["current_branch"] or "unknown"
        summary_parts.append(f"Git repository (branch: {branch})")
        if git_info["has_uncommitted_changes"]:
            summary_parts.append("Uncommitted changes present")
    else:
        summary_parts.append("Not a Git repository")

    return " | ".join(summary_parts)


def should_show_git_warning() -> bool:
    """
    Determine if git-related warnings should be shown.
    Based on Google's conditional warning logic.
    """
    git_info = detect_git_repository()

    # Show warning if in git repo (regardless of uncommitted changes)
    return git_info["is_git_repo"]


def should_show_sandbox_warning() -> bool:
    """
    Determine if sandbox-related warnings should be shown.
    """
    sandbox_info = detect_sandbox_environment()

    # Show warning if sandboxed
    return sandbox_info["is_sandboxed"]


def get_sandbox_warning_message() -> str:
    """
    Get appropriate sandbox warning message based on current environment.
    """
    sandbox_info = detect_sandbox_environment()

    if not sandbox_info["is_sandboxed"]:
        return ""

    sandbox_type = sandbox_info["sandbox_type"]
    restrictions = sandbox_info["restrictions"]

    if sandbox_type == "macos_app_sandbox":
        return """⚠️ **Sandbox Limitations**: You are running in a restricted environment. Some operations may be limited:
- File system access may be restricted to specific directories
- Network access might be limited
- System-level operations may require additional permissions

**Recommendations**:
- Test file operations in a safe directory first
- Use relative paths when possible
- Be aware that some tools may not function as expected"""

    elif sandbox_type == "linux_container":
        return """⚠️ **Container Environment**: Running in containerized environment:
- Process isolation is active
- Filesystem may be isolated
- Network access might be restricted

**Recommendations**:
- Verify file paths and permissions
- Check network connectivity if needed
- Be aware of container limitations"""

    else:
        return f"""⚠️ **Restricted Environment**: Limited capabilities detected:
- Restrictions: {", ".join(restrictions)}

**Recommendations**:
- Test operations in a safe environment first
- Verify permissions before proceeding"""


# Export functions using WORKSPACE_FUNCTIONS convention
WORKSPACE_FUNCTIONS = {
    "detect_sandbox_environment": detect_sandbox_environment,
    "detect_git_repository": detect_git_repository,
    "get_environment_summary": get_environment_summary,
    "should_show_git_warning": should_show_git_warning,
    "should_show_sandbox_warning": should_show_sandbox_warning,
    "get_sandbox_warning_message": get_sandbox_warning_message,
    # Aliases for template compatibility
    "get_sandbox_status": lambda: detect_sandbox_environment()["sandbox_type"]
    or "no_sandbox",
    "is_git_repository": lambda: detect_git_repository()["is_git_repo"],
    "get_git_workflow_instructions": lambda: """Always check git status before making changes
- Create feature branches for new work
- Write clear, descriptive commit messages
- Consider running tests before committing
- Use `git stash` to temporarily save work""",
}
