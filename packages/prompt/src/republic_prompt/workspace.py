"""Core workspace functionality for Republic Prompt.

This module provides the main PromptWorkspace class with a layered API design:
- Layer 1: Simple usage for 90% of users
- Layer 2: Custom functions for common use cases  
- Layer 3: Advanced customization for power users
"""

from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Callable

from .models import (
    PromptModel, SnippetModel, TemplateModel, FunctionModel, PromptWorkspaceConfig
)
from .loaders import (
    load_workspace_content, config_loader
)
from .renderer import DefaultRenderer, create_renderer
from .exceptions import WorkspaceError, TemplateError


class PromptWorkspace:
    """Main workspace class for managing prompt templates, snippets, and functions.
    
    This class provides a clean, layered API that grows with user needs:
    
    Simple usage:
        workspace = PromptWorkspace.load("./workspace")
        result = workspace.render("template", name="Alice")
    
    With custom functions:
        workspace = PromptWorkspace.load(
            "./workspace",
            custom_functions={"my_func": lambda x: x.upper()}
        )
    
    Advanced customization:
        from republic_prompt.loaders import function_loaders
        function_loaders.register("rust", RustFunctionLoader())
        workspace = PromptWorkspace.load("./workspace", function_loaders=["python", "rust"])
    """
    
    def __init__(self,
                 path: Path,
                 config: PromptWorkspaceConfig,
                 snippets: Dict[str, SnippetModel] = None,
                 templates: Dict[str, TemplateModel] = None,
                 functions: Dict[str, FunctionModel] = None,
                 renderer: Optional[DefaultRenderer] = None):
        """Initialize workspace with loaded content.
        
        Args:
            path: Path to workspace directory
            config: Workspace configuration
            snippets: Loaded snippets
            templates: Loaded templates
            functions: Loaded functions
            renderer: Custom renderer (optional)
        """
        self.path = path
        self.config = config
        self._snippets = snippets or {}
        self._templates = templates or {}
        self._functions = functions or {}
        
        # Create renderer with loaded content
        self._renderer = renderer or DefaultRenderer(
            snippets=self._snippets,
            functions=self._functions,
            auto_escape=self.config.auto_escape
        )
        
        # External workspaces for cross-workspace references
        self._external_workspaces: Dict[str, 'PromptWorkspace'] = {}
    
    @classmethod
    def load(cls,
             path: Union[str, Path],
             custom_functions: Optional[Dict[str, Callable]] = None,
             function_loaders: Optional[List[str]] = None,
             renderer_type: str = "default",
             renderer: Optional[DefaultRenderer] = None,
             **config_overrides) -> 'PromptWorkspace':
        """Load a workspace from a directory (Layer 1-3 API).
        
        Args:
            path: Path to workspace directory
            custom_functions: Dict of custom functions to inject (Layer 2)
            function_loaders: List of loader names to use (Layer 3)
            renderer_type: Type of renderer to create ("default", "message")
            renderer: Custom renderer instance (Layer 3)
            **config_overrides: Override configuration values
            
        Returns:
            Loaded PromptWorkspace instance
        """
        workspace_path = Path(path).resolve()
        
        if not workspace_path.exists():
            raise WorkspaceError(f"Workspace directory not found: {workspace_path}")
        
        if not workspace_path.is_dir():
            raise WorkspaceError(f"Workspace path is not a directory: {workspace_path}")
        
        try:
            # Load configuration
            config = config_loader.load_config(workspace_path)
            
            # Apply configuration overrides
            if config_overrides:
                config_dict = config.dict()
                config_dict.update(config_overrides)
                config = PromptWorkspaceConfig(**config_dict)
            
            # Load workspace content
            snippets, templates, functions = load_workspace_content(workspace_path, config)
            
            # Add custom functions (Layer 2 API)
            if custom_functions:
                for name, func in custom_functions.items():
                    functions[name] = FunctionModel(
                        name=name,
                        callable=func,
                        signature=str(func.__name__) if hasattr(func, '__name__') else None,
                        docstring=func.__doc__ if hasattr(func, '__doc__') else None
                    )
            
            # Handle custom function loaders (Layer 3 API)
            if function_loaders:
                custom_functions_dict = {}
                for loader_name in function_loaders:
                    loader = function_loaders.get(loader_name)
                    if loader:
                        # Load functions from workspace using specific loaders
                        functions_path = workspace_path / config.functions_dir
                        if functions_path.exists():
                            loader_functions = loader.load_functions(functions_path)
                            custom_functions_dict.update(loader_functions)
                
                functions.update(custom_functions_dict)
            
            # Create renderer
            if renderer:
                # Use provided renderer (Layer 3)
                final_renderer = renderer
            else:
                # Create renderer of specified type
                final_renderer = create_renderer(
                    renderer_type,
                    snippets=snippets,
                    functions=functions,
                    auto_escape=config.auto_escape
                )
            
            workspace = cls(
                path=workspace_path,
                config=config,
                snippets=snippets,
                templates=templates,
                functions=functions,
                renderer=final_renderer
            )

            # Load and attach external workspaces from config
            if config.external_workspaces:
                for name, external_path in config.external_workspaces.items():
                    # Path is relative to the config file's directory
                    full_external_path = (workspace_path / external_path).resolve()
                    external_workspace = cls.load(full_external_path)
                    workspace.add_external_workspace(name, external_workspace)
            
            return workspace
            
        except Exception as e:
            raise WorkspaceError(f"Failed to load workspace from {workspace_path}: {e}")
    
    def render(self, template_name: str, **variables) -> PromptModel:
        """Render a template with the given variables.
        
        Args:
            template_name: Name of template to render
            **variables: Template variables
            
        Returns:
            Rendered PromptModel
        """
        if template_name not in self._templates:
            available = ", ".join(self._templates.keys())
            raise TemplateError(
                f"Template '{template_name}' not found. Available templates: {available}",
                template_name=template_name
            )
        
        template = self._templates[template_name]
        return self._renderer.render_template(template, variables)
    
    def get_template(self, name: str) -> Optional[TemplateModel]:
        """Get a template by name."""
        return self._templates.get(name)
    
    def get_snippet(self, name: str) -> Optional[SnippetModel]:
        """Get a snippet by name."""
        return self._snippets.get(name)
    
    def get_function(self, name: str) -> Optional[FunctionModel]:
        """Get a function by name."""
        return self._functions.get(name)
    
    def list_templates(self) -> List[str]:
        """List all available template names."""
        return list(self._templates.keys())
    
    def list_snippets(self) -> List[str]:
        """List all available snippet names."""
        return list(self._snippets.keys())
    
    def list_functions(self) -> List[str]:
        """List all available function names."""
        return list(self._functions.keys())
    
    # ==========================================================================
    # Extension Methods (Layer 3 API)
    # ==========================================================================
    
    def add_function(self, name: str, func: Callable, **metadata):
        """Add a custom function to the workspace.
        
        Args:
            name: Function name
            func: Callable function
            **metadata: Additional metadata
        """
        self._functions[name] = FunctionModel(
            name=name,
            callable=func,
            signature=str(func.__name__) if hasattr(func, '__name__') else None,
            docstring=func.__doc__ if hasattr(func, '__doc__') else None,
            **metadata
        )
        
        # Update renderer
        self._renderer.update_functions(self._functions)
    
    def add_snippet(self, name: str, content: str, **metadata):
        """Add a custom snippet to the workspace.
        
        Args:
            name: Snippet name
            content: Snippet content
            **metadata: Additional metadata
        """
        self._snippets[name] = SnippetModel(
            name=name,
            content=content,
            metadata=metadata
        )
        
        # Update renderer
        self._renderer.update_snippets(self._snippets)
    
    def set_renderer(self, renderer: DefaultRenderer):
        """Set a new renderer for the workspace."""
        self._renderer = renderer

    def add_external_workspace(self, name: str, workspace: 'PromptWorkspace'):
        """Add an external workspace for cross-workspace references.
        
        This allows referencing snippets and functions from another workspace
        using the syntax `workspace_name::item_name`.
        
        Args:
            name: A unique alias for the external workspace.
            workspace: The PromptWorkspace instance to add.
        """
        if name in self._external_workspaces:
            raise WorkspaceError(f"External workspace with name '{name}' already exists.")
        
        self._external_workspaces[name] = workspace
        
        # Add snippets to the renderer with prefixed names
        for snippet_name, snippet_model in workspace._snippets.items():
            prefixed_name = f"{name}::{snippet_name}"
            self._renderer.add_snippet(prefixed_name, snippet_model)
            
        # Add functions to the renderer with prefixed names
        for func_name, func_model in workspace._functions.items():
            prefixed_name = f"{name}::{func_name}"
            self._renderer.add_function(prefixed_name, func_model)

    def render_text(self, content: str, **variables) -> str:
        """Render arbitrary text content with template variables.
        
        Args:
            content: Text content with template variables
            **variables: Template variables
            
        Returns:
            Rendered text
        """
        return self._renderer.render_text(content, variables)
    
    # ==========================================================================
    # Properties and Info
    # ==========================================================================
    
    @property
    def name(self) -> Optional[str]:
        """Get workspace name from config."""
        return self.config.name
    
    @property
    def description(self) -> Optional[str]:
        """Get workspace description from config."""
        return self.config.description
    
    @property
    def version(self) -> str:
        """Get workspace version from config."""
        return self.config.version
    
    def info(self) -> Dict[str, Any]:
        """Get workspace information summary."""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "path": str(self.path),
            "templates": len(self._templates),
            "snippets": len(self._snippets),
            "functions": len(self._functions),
            "external_workspaces": len(self._external_workspaces)
        }
    
    def __repr__(self) -> str:
        """String representation of workspace."""
        return (f"PromptWorkspace(path='{self.path}', "
                f"templates={len(self._templates)}, "
                f"snippets={len(self._snippets)}, "
                f"functions={len(self._functions)})")


# =============================================================================
# Convenience Functions
# =============================================================================

def load_workspace(path: Union[str, Path], **kwargs) -> PromptWorkspace:
    """Convenience function to load a workspace.
    
    Args:
        path: Path to workspace directory
        **kwargs: Additional arguments for PromptWorkspace.load()
        
    Returns:
        Loaded PromptWorkspace instance
    """
    return PromptWorkspace.load(path, **kwargs)


def quick_render(workspace_path: Union[str, Path], 
                 template_name: str, 
                 **variables) -> PromptModel:
    """Quick render a template without keeping workspace in memory.
    
    Args:
        workspace_path: Path to workspace directory
        template_name: Name of template to render
        **variables: Template variables
        
    Returns:
        Rendered PromptModel
    """
    workspace = PromptWorkspace.load(workspace_path)
    return workspace.render(template_name, **variables) 