"""Republic Prompt - Modern prompt engineering workspace library."""

__version__ = "0.3.0"

# Core data structures
from .core import (
    MessageRole,
    PromptMessage,
    Snippet,
    Template,
    Prompt,
    Function,
    FunctionLoader,
    WorkspaceConfig,
    Workspace,
    register_function_loader,
    get_function_loader,
    list_supported_languages,
)

# Loaders with pluggable function loading
from .loader import (
    load_snippet,
    load_template,
    load_prompt,
    load_functions_with_loaders,
    create_default_function_loaders,
    load_prompts_config,
    load_workspace,
    discover_workspaces,
    list_workspace_contents,
)

# Function loaders
from .loaders import (
    PythonFunctionLoader,
    BaseFunctionLoader,
)

# Modern Jinja2 renderer
from .renderer import (
    render,
    render_snippet,
    render_template_content,
    validate_template_syntax,
    get_template_variables,
    preview_render,
    create_jinja_environment,
    parse_message_blocks,
)

# Exceptions
from .exception import (
    LoaderError,
    FunctionLoadError,
    WorkspaceValidationError,
    RenderError,
    TemplateRenderError,
)


# Convenience functions
def quick_render(
    template_content: str, variables: dict = None, workspace: Workspace = None
) -> str:
    """Quick render for string templates without creating Template objects."""
    from .renderer import render_template_content

    return render_template_content(template_content, variables or {}, workspace)


def load_and_render(
    template_path: str, variables: dict = None, workspace: Workspace = None
) -> Prompt:
    """Load template from file and render in one step."""
    template = load_template(template_path)
    return render(template, variables, workspace)


# Export main API
__all__ = [
    # Version
    "__version__",
    # Core structures
    "MessageRole",
    "PromptMessage",
    "Snippet",
    "Template",
    "Prompt",
    "Function",
    "FunctionLoader",
    "WorkspaceConfig",
    "Workspace",
    # Core utilities
    "register_function_loader",
    "get_function_loader",
    "list_supported_languages",
    # Exceptions
    "LoaderError",
    "FunctionLoadError",
    "WorkspaceValidationError",
    "RenderError",
    "TemplateRenderError",
    # Loaders
    "load_snippet",
    "load_template",
    "load_prompt",
    "load_functions_with_loaders",
    "create_default_function_loaders",
    "load_prompts_config",
    "load_workspace",
    "discover_workspaces",
    "list_workspace_contents",
    # Function loaders
    "PythonFunctionLoader",
    "BaseFunctionLoader",
    # Renderers
    "render",
    "render_snippet",
    "render_template_content",
    "validate_template_syntax",
    "get_template_variables",
    "preview_render",
    "create_jinja_environment",
    "parse_message_blocks",
    # Convenience
    "quick_render",
    "load_and_render",
]
