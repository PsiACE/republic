"""Republic Prompt - A modern prompt engineering toolkit.

This package provides a simple yet powerful API for managing prompt templates,
snippets, and functions in a workspace-based structure.

Usage:
    # Simple usage (90% of users)
    workspace = PromptWorkspace.load("./workspace")
    result = workspace.render("template", name="Alice")

    # With custom functions
    workspace = PromptWorkspace.load(
        "./workspace",
        custom_functions={"my_func": lambda x: x.upper()}
    )
    
    # Advanced customization
    from republic_prompt.loaders import function_loaders
    function_loaders.register("rust", RustFunctionLoader())
"""

from .workspace import PromptWorkspace, load_workspace, quick_render
from .models import PromptModel, SnippetModel, TemplateModel

__version__ = "0.4.0"
__all__ = ["PromptWorkspace", "PromptModel", "SnippetModel", "TemplateModel", "load_workspace", "quick_render"] 