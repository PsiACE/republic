"""Python function loader implementation."""

import importlib.util
import sys
import inspect
from pathlib import Path
from typing import Dict, List, Any
from ..core import Function, register_function_loader
from .base import BaseFunctionLoader


@register_function_loader("python")
class PythonFunctionLoader(BaseFunctionLoader):
    """Function loader for Python files."""

    @property
    def language(self) -> str:
        return "python"

    @property
    def supported_extensions(self) -> List[str]:
        return [".py"]

    def load_functions(self, workspace_path: Path) -> Dict[str, Function]:
        """Load Python functions from workspace."""
        all_functions = {}
        function_files = self.find_function_files(workspace_path)

        for file_path in function_files:
            try:
                file_functions = self._load_functions_from_file(file_path)

                # Check for name conflicts
                conflicts = set(file_functions.keys()) & set(all_functions.keys())
                if conflicts:
                    self.logger.warning(
                        f"Function name conflicts in {file_path}: {conflicts}"
                    )
                    for conflict in conflicts:
                        old_source = all_functions[conflict].source_file
                        self.logger.warning(
                            f"  '{conflict}' redefined (was from {old_source})"
                        )

                all_functions.update(file_functions)
                self.log_loading_result(file_path, len(file_functions))

            except Exception as e:
                self.logger.error(
                    f"Failed to load Python functions from {file_path}: {e}"
                )
                continue

        return all_functions

    def _load_functions_from_file(self, file_path: Path) -> Dict[str, Function]:
        """Load functions from a single Python file."""
        functions = {}

        if not file_path.suffix == ".py":
            return functions

        try:
            # Load the module dynamically
            module_name = f"workspace_functions_{file_path.stem}"
            spec = importlib.util.spec_from_file_location(module_name, file_path)

            if not spec or not spec.loader:
                raise ImportError(f"Cannot create module spec for {file_path}")

            module = importlib.util.module_from_spec(spec)

            # Add to sys.modules to handle relative imports
            sys.modules[module_name] = module

            try:
                spec.loader.exec_module(module)
            finally:
                # Clean up sys.modules
                sys.modules.pop(module_name, None)

            # Look for WORKSPACE_FUNCTIONS export first (preferred convention)
            if hasattr(module, "WORKSPACE_FUNCTIONS"):
                functions.update(self._load_exported_functions(module, file_path))
            else:
                # Fallback: export all public functions
                functions.update(self._load_public_functions(module, file_path))

        except Exception as e:
            raise ImportError(f"Failed to load Python module {file_path}: {e}")

        return functions

    def _load_exported_functions(
        self, module: Any, file_path: Path
    ) -> Dict[str, Function]:
        """Load functions from WORKSPACE_FUNCTIONS export."""
        functions = {}
        exported_functions = module.WORKSPACE_FUNCTIONS

        if not isinstance(exported_functions, dict):
            raise ValueError(f"WORKSPACE_FUNCTIONS in {file_path} must be a dictionary")

        for name, func in exported_functions.items():
            if not self.validate_function_name(name, file_path):
                continue

            if not callable(func):
                self.logger.warning(f"Skipping non-callable '{name}' in {file_path}")
                continue

            try:
                functions[name] = Function(
                    name=name,
                    callable=func,
                    description=self._extract_docstring(func),
                    language="python",
                    source_file=str(file_path),
                    metadata={
                        "module": module.__name__
                        if hasattr(module, "__name__")
                        else None,
                        "is_exported": True,
                    },
                )
            except Exception as e:
                self.logger.warning(
                    f"Skipping invalid function '{name}' in {file_path}: {e}"
                )

        return functions

    def _load_public_functions(
        self, module: Any, file_path: Path
    ) -> Dict[str, Function]:
        """Load all public functions from module."""
        functions = {}
        module_name = getattr(module, "__name__", file_path.stem)

        for name in dir(module):
            if name.startswith("_"):
                continue

            obj = getattr(module, name)
            if not (callable(obj) and inspect.isfunction(obj)):
                continue

            # Skip imported functions (only include functions defined in this module)
            if hasattr(obj, "__module__") and obj.__module__ != module_name:
                continue

            if not self.validate_function_name(name, file_path):
                continue

            try:
                functions[name] = Function(
                    name=name,
                    callable=obj,
                    description=self._extract_docstring(obj),
                    language="python",
                    source_file=str(file_path),
                    metadata={
                        "module": module_name,
                        "is_exported": False,
                    },
                )
            except Exception as e:
                self.logger.warning(
                    f"Skipping invalid function '{name}' in {file_path}: {e}"
                )

        return functions

    def _extract_docstring(self, func: Any) -> str:
        """Extract first line of docstring as description."""
        if hasattr(func, "__doc__") and func.__doc__:
            return func.__doc__.strip().split("\n")[0]
        return None

    def validate_python_function(self, func: Any) -> bool:
        """Additional Python-specific validation."""
        if not inspect.isfunction(func):
            return False

        # Check if function signature is reasonable
        try:
            sig = inspect.signature(func)
            # Functions with too many required parameters might be problematic in templates
            required_params = sum(
                1
                for p in sig.parameters.values()
                if p.default == inspect.Parameter.empty
                and p.kind != inspect.Parameter.VAR_KEYWORD
            )
            if required_params > 5:  # Arbitrary limit
                self.logger.warning(
                    f"Function {func.__name__} has many required parameters ({required_params})"
                )
        except Exception:
            pass  # Signature inspection failed, but function might still be usable

        return True

    def _should_skip_file(self, file_path: Path) -> bool:
        """Python-specific file filtering logic."""
        # Skip hidden files (from base class)
        if super()._should_skip_file(file_path):
            return True

        # Skip __pycache__ and other special directories, but allow __init__.py
        if file_path.name.startswith("__") and file_path.name != "__init__.py":
            return True

        # Skip .pyc, .pyo files
        if file_path.suffix in [".pyc", ".pyo"]:
            return True

        return False
