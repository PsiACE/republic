"""Tests for environment detection functions."""

import os
from unittest.mock import patch, MagicMock
from republic_prompt.loader import load_workspace


class TestEnvironmentDetection:
    """Test environment detection functionality."""

    def setup_method(self):
        """Set up test workspace."""
        self.workspace = load_workspace("packages/prompt/examples")
        # Get the actual callable functions
        self.functions = self.workspace.get_functions_dict()

    @patch("subprocess.run")
    def test_should_show_git_warning_in_git_repo(self, mock_run):
        """Test git warning detection when in git repository."""
        # Mock successful git command (in git repo)
        mock_run.return_value = MagicMock(returncode=0)

        result = self.functions["should_show_git_warning"]()
        assert result is True

        # Verify git command was called
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "git" in args
        assert "rev-parse" in args

    @patch("subprocess.run")
    def test_should_show_git_warning_not_in_git_repo(self, mock_run):
        """Test git warning detection when not in git repository."""
        # Mock failed git command (not in git repo)
        mock_run.return_value = MagicMock(returncode=1)

        result = self.functions["should_show_git_warning"]()
        assert result is False

        mock_run.assert_called_once()

    @patch.dict(os.environ, {"SANDBOX": "sandbox-exec"})
    def test_should_show_sandbox_warning_macos_seatbelt(self):
        """Test sandbox warning for macOS seatbelt environment."""
        result = self.functions["should_show_sandbox_warning"]()
        assert result is True

    @patch.dict(os.environ, {"SANDBOX": "generic"})
    def test_should_show_sandbox_warning_generic(self):
        """Test sandbox warning for generic sandbox environment."""
        result = self.functions["should_show_sandbox_warning"]()
        assert result is True

    @patch.dict(os.environ, {}, clear=True)
    def test_should_show_sandbox_warning_no_sandbox(self):
        """Test sandbox warning when not in sandbox."""
        result = self.functions["should_show_sandbox_warning"]()
        assert result is False

    def test_get_sandbox_status_values(self):
        """Test sandbox status detection returns valid values."""
        get_sandbox_status = self.functions["get_sandbox_status"]

        with patch.dict(os.environ, {"SANDBOX": "sandbox-exec"}):
            assert get_sandbox_status() == "macos_seatbelt"

        with patch.dict(os.environ, {"SANDBOX": "generic"}):
            assert get_sandbox_status() == "generic_sandbox"

        with patch.dict(os.environ, {}, clear=True):
            assert get_sandbox_status() == "no_sandbox"

    @patch("subprocess.run")
    def test_is_git_repository_detection(self, mock_run):
        """Test git repository detection logic."""
        is_git_repository = self.functions["is_git_repository"]

        # Test when in git repository
        mock_run.return_value = MagicMock(returncode=0)
        assert is_git_repository() is True

        # Test when not in git repository
        mock_run.return_value = MagicMock(returncode=1)
        assert is_git_repository() is False

        # Test when git command fails
        mock_run.side_effect = FileNotFoundError()
        assert is_git_repository() is False

    def test_environment_functions_are_callable(self):
        """Test that all environment functions are properly callable."""
        required_functions = [
            "should_show_git_warning",
            "should_show_sandbox_warning",
            "get_sandbox_status",
            "is_git_repository",
            "get_git_workflow_instructions",
        ]

        for func_name in required_functions:
            assert func_name in self.functions
            assert callable(self.functions[func_name])

    def test_environment_data_types(self):
        """Test that environment functions return expected data types."""
        # Boolean functions should return booleans
        assert isinstance(self.functions["should_show_git_warning"](), bool)
        assert isinstance(self.functions["should_show_sandbox_warning"](), bool)
        assert isinstance(self.functions["is_git_repository"](), bool)

        # Sandbox status should be a string
        sandbox_status = self.functions["get_sandbox_status"]()
        assert isinstance(sandbox_status, str)
        assert sandbox_status in ["macos_seatbelt", "generic_sandbox", "no_sandbox"]

        # Git workflow instructions should be a string
        git_instructions = self.functions["get_git_workflow_instructions"]()
        assert isinstance(git_instructions, str)
        assert len(git_instructions) > 0
