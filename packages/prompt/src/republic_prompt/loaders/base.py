"""Base function loader with common functionality."""

import logging
from pathlib import Path
from typing import List, Optional
from ..core import FunctionLoader

logger = logging.getLogger(__name__)


class BaseFunctionLoader(FunctionLoader):
    """Base implementation with common functionality."""

    def __init__(self, logger_name: Optional[str] = None):
        self.logger = logging.getLogger(logger_name or self.__class__.__name__)

    def find_function_files(self, workspace_path: Path) -> List[Path]:
        """Find function files in workspace using supported extensions."""
        function_files = []

        # Check for single functions file
        for ext in self.supported_extensions:
            single_file = workspace_path / f"functions{ext}"
            if single_file.exists():
                function_files.append(single_file)

        # Check for functions directory
        functions_dir = workspace_path / "functions"
        if functions_dir.exists() and functions_dir.is_dir():
            for ext in self.supported_extensions:
                for file_path in functions_dir.glob(f"*{ext}"):
                    # Apply language-specific filtering
                    if self._should_skip_file(file_path):
                        continue
                    function_files.append(file_path)

        return sorted(function_files)

    def log_loading_result(
        self, file_path: Path, function_count: int, errors: List[str] = None
    ):
        """Log the result of loading functions from a file."""
        if errors:
            for error in errors:
                self.logger.warning(f"Error loading from {file_path}: {error}")

        if function_count > 0:
            self.logger.info(f"Loaded {function_count} functions from {file_path}")
        else:
            self.logger.debug(f"No functions loaded from {file_path}")

    def validate_function_name(self, name: str, file_path: Path) -> bool:
        """Validate function name for cross-language compatibility."""
        if not name:
            self.logger.warning(f"Empty function name in {file_path}")
            return False

        if not isinstance(name, str):
            self.logger.warning(f"Non-string function name in {file_path}: {name}")
            return False

        # Basic validation for cross-language compatibility
        if not name.replace("_", "").replace("-", "").isalnum():
            self.logger.warning(f"Invalid function name in {file_path}: {name}")
            return False

        return True

    def _should_skip_file(self, file_path: Path) -> bool:
        """
        Determine if a file should be skipped during loading.
        Override in subclasses for language-specific logic.
        """
        # Default: skip hidden files and directories
        return file_path.name.startswith(".")
