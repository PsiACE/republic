"""Unified loader system for Republic Prompt.

This module provides all loading functionality in a single, well-organized file
while maintaining extensibility through registry patterns.
"""

import inspect
import importlib
import importlib.util
from pathlib import Path
from typing import Dict, Any, Optional, Callable, Protocol
from abc import ABC, abstractmethod

try:
    import tomllib
except ImportError:
    tomllib = None

try:
    import yaml
except ImportError:
    yaml = None

from .models import (
    SnippetModel, TemplateModel, FunctionModel, PromptWorkspaceConfig,
)
from .exceptions import LoaderError


# =============================================================================
# Base Loader Protocols and Registry
# =============================================================================

class BaseLoader(Protocol):
    """Protocol for all loaders to ensure consistent interface."""
    
    def can_handle(self, path: Path) -> bool:
        """Check if this loader can handle the given path."""
        ...
    
    def load(self, path: Path, **kwargs) -> Any:
        """Load content from the given path."""
        ...


class LoaderRegistry:
    """Registry for managing different types of loaders."""
    
    def __init__(self):
        self._loaders: Dict[str, Any] = {}
    
    def register(self, name: str, loader: Any) -> None:
        """Register a loader with a given name."""
        self._loaders[name] = loader
    
    def get(self, name: str) -> Optional[Any]:
        """Get a loader by name."""
        return self._loaders.get(name)
    
    def get_all(self) -> Dict[str, Any]:
        """Get all registered loaders."""
        return self._loaders.copy()
    
    def find_loader(self, path: Path) -> Optional[Any]:
        """Find the first loader that can handle the given path."""
        for loader in self._loaders.values():
            if hasattr(loader, 'can_handle') and loader.can_handle(path):
                return loader
        return None


# =============================================================================
# Formatter Loaders (for frontmatter parsing)
# =============================================================================

class FormatterLoader(ABC):
    """Base class for frontmatter format loaders."""
    
    @abstractmethod
    def can_handle(self, content: str) -> bool:
        """Check if this formatter can handle the content."""
        pass
    
    @abstractmethod
    def parse(self, content: str) -> tuple[Dict[str, Any], str]:
        """Parse frontmatter and content, return (metadata, content)."""
        pass


class TomlFormatterLoader(FormatterLoader):
    """Loader for TOML frontmatter (using +++ delimiters)."""
    
    def can_handle(self, content: str) -> bool:
        """Check if content starts with TOML frontmatter."""
        return content.strip().startswith('+++')
    
    def parse(self, content: str) -> tuple[Dict[str, Any], str]:
        """Parse TOML frontmatter."""
        if not self.can_handle(content):
            return {}, content
        
        try:
            # Split on the closing +++
            parts = content.split('+++', 2)
            if len(parts) < 3:
                return {}, content
            
            toml_content = parts[1].strip()
            main_content = parts[2].lstrip('\n')
            
            if not toml_content:
                return {}, main_content
            
            metadata = tomllib.loads(toml_content)
            return metadata, main_content
            
        except Exception as e:
            raise LoaderError(f"Failed to parse TOML frontmatter: {e}")


class YamlFormatterLoader(FormatterLoader):
    """Loader for YAML frontmatter (using --- delimiters)."""
    
    def can_handle(self, content: str) -> bool:
        """Check if content starts with YAML frontmatter."""
        return content.strip().startswith('---')
    
    def parse(self, content: str) -> tuple[Dict[str, Any], str]:
        """Parse YAML frontmatter."""
        if not yaml:
            raise LoaderError("PyYAML is required for YAML frontmatter support")
        
        if not self.can_handle(content):
            return {}, content
        
        try:
            # Split on the closing ---
            parts = content.split('---', 2)
            if len(parts) < 3:
                return {}, content
            
            yaml_content = parts[1].strip()
            main_content = parts[2].lstrip('\n')
            
            if not yaml_content:
                return {}, main_content
            
            metadata = yaml.safe_load(yaml_content) or {}
            return metadata, main_content
            
        except Exception as e:
            raise LoaderError(f"Failed to parse YAML frontmatter: {e}")


class FormatterLoaderRegistry(LoaderRegistry):
    """Registry specifically for formatter loaders with auto-detection."""
    
    def parse_frontmatter(self, content: str) -> tuple[Dict[str, Any], str]:
        """Auto-detect format and parse frontmatter."""
        for formatter in self._loaders.values():
            if formatter.can_handle(content):
                return formatter.parse(content)
        
        # No frontmatter found
        return {}, content


# =============================================================================
# Content Loaders
# =============================================================================

class ContentLoader:
    """Loader for markdown content with frontmatter parsing."""
    
    def __init__(self, formatter_registry: FormatterLoaderRegistry):
        self.formatter_registry = formatter_registry
    
    def can_handle(self, path: Path) -> bool:
        """Check if this loader can handle the file."""
        return path.suffix.lower() in ['.md', '.markdown', '.txt']
    
    def load_snippet(self, path: Path) -> SnippetModel:
        """Load a snippet from a markdown file."""
        if not path.exists():
            raise LoaderError(f"Snippet file not found: {path}")
        
        try:
            content = path.read_text(encoding='utf-8')
            metadata, main_content = self.formatter_registry.parse_frontmatter(content)
            
            return SnippetModel(
                name=path.stem,
                content=main_content,
                metadata=metadata,
                file_path=path
            )
        except Exception as e:
            raise LoaderError(f"Failed to load snippet from {path}: {e}")
    
    def load_template(self, path: Path) -> TemplateModel:
        """Load a template from a markdown file."""
        if not path.exists():
            raise LoaderError(f"Template file not found: {path}")
        
        try:
            content = path.read_text(encoding='utf-8')
            metadata, main_content = self.formatter_registry.parse_frontmatter(content)
            
            return TemplateModel(
                name=path.stem,
                content=main_content,
                metadata=metadata,
                file_path=path
            )
        except Exception as e:
            raise LoaderError(f"Failed to load template from {path}: {e}")


# =============================================================================
# Function Loaders
# =============================================================================

class FunctionLoader(ABC):
    """Base class for function loaders."""
    
    @abstractmethod
    def can_handle(self, path: Path) -> bool:
        """Check if this loader can handle the path."""
        pass
    
    @abstractmethod
    def load_functions(self, path: Path) -> Dict[str, FunctionModel]:
        """Load functions from the given path."""
        pass


class PythonFunctionLoader(FunctionLoader):
    """Loader for Python functions."""
    
    def can_handle(self, path: Path) -> bool:
        """Check if this loader can handle Python files."""
        if path.is_file():
            return path.suffix == '.py'
        elif path.is_dir():
            return any(f.suffix == '.py' for f in path.glob('*.py'))
        return False
    
    def load_functions(self, path: Path) -> Dict[str, FunctionModel]:
        """Load Python functions from file or directory."""
        functions = {}
        
        if path.is_file():
            functions.update(self._load_from_file(path))
        elif path.is_dir():
            # Load from all Python files in directory
            for py_file in path.glob('*.py'):
                if py_file.name.startswith('__'):
                    continue
                try:
                    functions.update(self._load_from_file(py_file))
                except Exception as e:
                    # Log warning but continue with other files
                    print(f"Warning: Failed to load functions from {py_file}: {e}")
        
        return functions
    
    def _load_from_file(self, file_path: Path) -> Dict[str, FunctionModel]:
        """Load functions from a single Python file."""
        try:
            # Create module spec and load
            spec = importlib.util.spec_from_file_location(
                f"workspace_functions_{file_path.stem}", 
                file_path
            )
            if not spec or not spec.loader:
                raise LoaderError(f"Could not create module spec for {file_path}")
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            functions = {}
            
            # Check for WORKSPACE_FUNCTIONS convention first
            if hasattr(module, 'WORKSPACE_FUNCTIONS'):
                workspace_funcs = getattr(module, 'WORKSPACE_FUNCTIONS')
                if isinstance(workspace_funcs, dict):
                    for name, func in workspace_funcs.items():
                        if callable(func):
                            functions[name] = self._create_function_model(name, func, module)
            
            # Also load regular functions (not starting with _)
            for name in dir(module):
                if (not name.startswith('_') and 
                    name not in functions and  # Don't override WORKSPACE_FUNCTIONS
                    callable(getattr(module, name))):
                    
                    func = getattr(module, name)
                    # Skip imported functions and classes
                    if (inspect.isfunction(func) and 
                        func.__module__ == module.__name__):
                        functions[name] = self._create_function_model(name, func, module)
            
            return functions
            
        except Exception as e:
            raise LoaderError(f"Failed to load Python functions from {file_path}: {e}")
    
    def _create_function_model(self, name: str, func: Callable, module) -> FunctionModel:
        """Create a FunctionModel from a callable."""
        try:
            signature = str(inspect.signature(func))
        except Exception:
            signature = None
        
        docstring = inspect.getdoc(func)
        module_name = getattr(module, '__name__', None)
        
        return FunctionModel(
            name=name,
            callable=func,
            signature=signature,
            docstring=docstring,
            module=module_name
        )


class FunctionLoaderRegistry(LoaderRegistry):
    """Registry for function loaders with enhanced functionality."""
    
    def load_all_functions(self, path: Path) -> Dict[str, FunctionModel]:
        """Load functions using all available loaders."""
        all_functions = {}
        
        for loader in self._loaders.values():
            if loader.can_handle(path):
                try:
                    functions = loader.load_functions(path)
                    all_functions.update(functions)
                except Exception as e:
                    print(f"Warning: Loader {loader.__class__.__name__} failed: {e}")
        
        return all_functions


# =============================================================================
# Configuration Loader
# =============================================================================

class ConfigLoader:
    """Loader for workspace configuration files."""
    
    def can_handle(self, path: Path) -> bool:
        """Check if this loader can handle the config file."""
        return path.name in ['prompts.toml', 'republic.toml'] and path.exists()
    
    def load_config(self, workspace_path: Path) -> PromptWorkspaceConfig:
        """Load workspace configuration."""
        config_files = ['prompts.toml', 'republic.toml']
        
        for config_file in config_files:
            config_path = workspace_path / config_file
            if config_path.exists():
                return self._load_toml_config(config_path)
        
        # Return default config if no config file found
        return PromptWorkspaceConfig()
    
    def _load_toml_config(self, config_path: Path) -> PromptWorkspaceConfig:
        """Load configuration from TOML file."""
        try:
            content = config_path.read_text(encoding='utf-8')
            data = tomllib.loads(content)
            
            # Extract prompts section if it exists (for republic.toml)
            if 'prompts' in data:
                data = data['prompts']
            
            return PromptWorkspaceConfig(**data)
            
        except Exception as e:
            raise LoaderError(f"Failed to load config from {config_path}: {e}")


# =============================================================================
# Default Registry Instances
# =============================================================================

# Create default registries with built-in loaders
formatter_loaders = FormatterLoaderRegistry()
formatter_loaders.register("toml", TomlFormatterLoader())
formatter_loaders.register("yaml", YamlFormatterLoader())

function_loaders = FunctionLoaderRegistry()
function_loaders.register("python", PythonFunctionLoader())

# Content loader using the default formatter registry
content_loader = ContentLoader(formatter_loaders)
config_loader = ConfigLoader()


# =============================================================================
# Convenience Functions
# =============================================================================

def load_workspace_content(workspace_path: Path, config: PromptWorkspaceConfig) -> tuple[
    Dict[str, SnippetModel], 
    Dict[str, TemplateModel], 
    Dict[str, FunctionModel]
]:
    """Load all workspace content (snippets, templates, functions)."""
    snippets = {}
    templates = {}
    functions = {}
    
    # Load snippets
    snippets_path = workspace_path / config.snippets_dir
    if snippets_path.exists():
        for snippet_file in snippets_path.glob('*.md'):
            try:
                snippet = content_loader.load_snippet(snippet_file)
                snippets[snippet.name] = snippet
            except Exception as e:
                print(f"Warning: Failed to load snippet {snippet_file}: {e}")
    
    # Load templates
    templates_path = workspace_path / config.templates_dir
    if templates_path.exists():
        for template_file in templates_path.glob('*.md'):
            try:
                template = content_loader.load_template(template_file)
                templates[template.name] = template
            except Exception as e:
                print(f"Warning: Failed to load template {template_file}: {e}")
    
    # Load functions
    functions_path = workspace_path / config.functions_dir
    if functions_path.exists():
        functions = function_loaders.load_all_functions(functions_path)
    
    # Also check for single functions.py file
    functions_file = workspace_path / 'functions.py'
    if functions_file.exists():
        single_file_functions = function_loaders.load_all_functions(functions_file)
        functions.update(single_file_functions)
    
    return snippets, templates, functions 