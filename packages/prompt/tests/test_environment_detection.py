"""Test cases for environment detection functions."""

import subprocess
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

# Import the functions we want to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "examples" / "functions"))

from environment import (
    detect_sandbox_environment,
    detect_git_repository,
    get_environment_summary,
    should_show_git_warning,
    should_show_sandbox_warning,
    get_sandbox_warning_message
)


class TestSandboxDetection:
    """Test sandbox environment detection."""

    @patch('platform.system')
    @patch('subprocess.run')
    def test_macos_app_sandbox_detection(self, mock_run, mock_platform):
        """Test macOS App Sandbox detection."""
        mock_platform.return_value = "Darwin"
        mock_run.return_value = MagicMock(
            stdout="com.apple.security.app-sandbox",
            returncode=0
        )
        
        result = detect_sandbox_environment()
        
        assert result["is_sandboxed"] is True
        assert result["sandbox_type"] == "macos_app_sandbox"
        assert "seatbelt" in result["detected_features"]
        assert "file_system" in result["restrictions"]

    @patch('platform.system')
    @patch('subprocess.run')
    def test_macos_no_sandbox(self, mock_run, mock_platform):
        """Test macOS without sandbox."""
        mock_platform.return_value = "Darwin"
        mock_run.return_value = MagicMock(
            stdout="no sandbox entitlements",
            returncode=0
        )
        
        result = detect_sandbox_environment()
        
        assert result["is_sandboxed"] is False

    @patch('platform.system')
    @patch('os.path.exists')
    def test_linux_docker_detection(self, mock_exists, mock_platform):
        """Test Docker container detection on Linux."""
        mock_platform.return_value = "Linux"
        mock_exists.return_value = True  # /.dockerenv exists
        
        result = detect_sandbox_environment()
        
        assert result["is_sandboxed"] is True
        assert result["sandbox_type"] == "linux_container"
        assert "docker" in result["detected_features"]

    @patch('platform.system')
    @patch('os.environ.get')
    def test_linux_systemd_nspawn_detection(self, mock_env_get, mock_platform):
        """Test systemd-nspawn container detection."""
        mock_platform.return_value = "Linux"
        mock_env_get.return_value = "systemd-nspawn"
        
        result = detect_sandbox_environment()
        
        assert result["is_sandboxed"] is True
        assert "systemd-nspawn" in result["detected_features"]

    @patch('platform.system')
    @patch('builtins.open', mock_open(read_data="1:name=systemd:/docker/123abc"))
    def test_linux_cgroup_container_detection(self, mock_platform):
        """Test container detection via cgroup."""
        mock_platform.return_value = "Linux"
        
        result = detect_sandbox_environment()
        
        assert result["is_sandboxed"] is True
        assert "cgroup_container" in result["detected_features"]

    @patch('builtins.open', side_effect=PermissionError())
    def test_filesystem_restriction_detection(self, mock_open):
        """Test detection of filesystem restrictions."""
        result = detect_sandbox_environment()
        
        assert "limited_filesystem_access" in result["restrictions"]

    @patch('os.environ.get')
    def test_network_restriction_detection(self, mock_env_get):
        """Test detection of network restrictions."""
        mock_env_get.return_value = "1"  # NO_NETWORK=1
        
        result = detect_sandbox_environment()
        
        assert "no_network_access" in result["restrictions"]


class TestGitDetection:
    """Test Git repository detection."""

    @patch('subprocess.run')
    def test_git_repository_detection_success(self, mock_run):
        """Test successful Git repository detection."""
        # Mock successful git commands
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="/path/to/repo"),  # git rev-parse --show-toplevel
            MagicMock(returncode=0, stdout="main"),           # git branch --show-current
            MagicMock(returncode=0, stdout="M file.txt"),     # git status --porcelain
            MagicMock(returncode=0, stdout="https://github.com/user/repo.git")  # git remote get-url origin
        ]
        
        result = detect_git_repository()
        
        assert result["is_git_repo"] is True
        assert result["repo_root"] == "/path/to/repo"
        assert result["current_branch"] == "main"
        assert result["has_uncommitted_changes"] is True
        assert result["remote_url"] == "https://github.com/user/repo.git"

    @patch('subprocess.run')
    def test_git_repository_detection_failure(self, mock_run):
        """Test Git repository detection when not in a repo."""
        mock_run.return_value = MagicMock(returncode=128)  # Not a git repository
        
        result = detect_git_repository()
        
        assert result["is_git_repo"] is False
        assert result["repo_root"] is None

    @patch('subprocess.run')
    def test_git_no_uncommitted_changes(self, mock_run):
        """Test Git detection with no uncommitted changes."""
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="/path/to/repo"),
            MagicMock(returncode=0, stdout="main"),
            MagicMock(returncode=0, stdout=""),  # Empty status output
            MagicMock(returncode=0, stdout="https://github.com/user/repo.git")
        ]
        
        result = detect_git_repository()
        
        assert result["has_uncommitted_changes"] is False

    @patch('subprocess.run')
    def test_git_subprocess_error(self, mock_run):
        """Test Git detection with subprocess error."""
        mock_run.side_effect = subprocess.SubprocessError()
        
        result = detect_git_repository()
        
        assert result["is_git_repo"] is False


class TestEnvironmentSummary:
    """Test environment summary generation."""

    @patch('environment.detect_sandbox_environment')
    @patch('environment.detect_git_repository')
    def test_sandboxed_git_repo_summary(self, mock_git, mock_sandbox):
        """Test summary for sandboxed Git repository."""
        mock_sandbox.return_value = {
            "is_sandboxed": True,
            "sandbox_type": "docker",
            "restrictions": ["filesystem", "network"]
        }
        mock_git.return_value = {
            "is_git_repo": True,
            "current_branch": "main",
            "has_uncommitted_changes": True
        }
        
        summary = get_environment_summary()
        
        assert "Sandboxed environment (docker)" in summary
        assert "Git repository (branch: main)" in summary
        assert "Uncommitted changes present" in summary

    @patch('environment.detect_sandbox_environment')
    @patch('environment.detect_git_repository')
    def test_unrestricted_non_git_summary(self, mock_git, mock_sandbox):
        """Test summary for unrestricted, non-Git environment."""
        mock_sandbox.return_value = {"is_sandboxed": False}
        mock_git.return_value = {"is_git_repo": False}
        
        summary = get_environment_summary()
        
        assert "Unrestricted environment" in summary
        assert "Not a Git repository" in summary


class TestWarningLogic:
    """Test warning display logic."""

    @patch('environment.detect_git_repository')
    def test_should_show_git_warning_with_repo(self, mock_git):
        """Test that git warning is shown when in a repo."""
        mock_git.return_value = {"is_git_repo": True}
        
        assert should_show_git_warning() is True

    @patch('environment.detect_git_repository')
    def test_should_not_show_git_warning_without_repo(self, mock_git):
        """Test that git warning is not shown when not in a repo."""
        mock_git.return_value = {"is_git_repo": False}
        
        assert should_show_git_warning() is False

    @patch('environment.detect_sandbox_environment')
    def test_should_show_sandbox_warning_when_sandboxed(self, mock_sandbox):
        """Test that sandbox warning is shown when sandboxed."""
        mock_sandbox.return_value = {"is_sandboxed": True}
        
        assert should_show_sandbox_warning() is True

    @patch('environment.detect_sandbox_environment')
    def test_should_not_show_sandbox_warning_when_not_sandboxed(self, mock_sandbox):
        """Test that sandbox warning is not shown when not sandboxed."""
        mock_sandbox.return_value = {"is_sandboxed": False}
        
        assert should_show_sandbox_warning() is False

    @patch('environment.detect_sandbox_environment')
    def test_sandbox_warning_message_generation(self, mock_sandbox):
        """Test sandbox warning message generation."""
        mock_sandbox.return_value = {
            "is_sandboxed": True,
            "sandbox_type": "macos_app_sandbox",
            "restrictions": ["file_system", "network"]
        }
        
        message = get_sandbox_warning_message()
        
        assert "sandbox" in message.lower()
        assert "limitations" in message.lower() or "restricted" in message.lower()


class TestEnvironmentIntegration:
    """Integration tests for environment detection."""

    def test_real_environment_detection(self):
        """Test environment detection on the actual system."""
        # This test runs against the real environment
        sandbox_info = detect_sandbox_environment()
        git_info = detect_git_repository()
        
        # Basic sanity checks
        assert isinstance(sandbox_info["is_sandboxed"], bool)
        assert isinstance(git_info["is_git_repo"], bool)
        
        # If sandboxed, should have sandbox type
        if sandbox_info["is_sandboxed"]:
            assert sandbox_info["sandbox_type"] is not None
        
        # If git repo, should have repo root
        if git_info["is_git_repo"]:
            assert git_info["repo_root"] is not None

    def test_environment_summary_real(self):
        """Test environment summary generation on real system."""
        summary = get_environment_summary()
        
        assert isinstance(summary, str)
        assert len(summary) > 0
        assert "|" in summary  # Should contain separators 