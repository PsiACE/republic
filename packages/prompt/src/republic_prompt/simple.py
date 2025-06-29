"""Simple template formatting for Republic Prompt.

This module provides a lightweight API for users who just need to format
template strings without the full workspace functionality.
"""

from typing import Dict, Optional, Callable

from .renderer import DefaultRenderer
from .models import FunctionModel
from .exceptions import TemplateError


def format(
    template: str,
    custom_functions: Optional[Dict[str, Callable]] = None,
    auto_escape: bool = False,
    **variables,
) -> str:
    """Format a template string with variables.

    This is a simple, lightweight function for users who just need to format
    template strings without setting up a full workspace.

    Args:
        template: Template string using Jinja2 syntax (e.g., "Hello {{ name }}!")
        custom_functions: Optional dict of custom functions to make available
        auto_escape: Whether to auto-escape HTML content
        **variables: Variables to substitute in the template

    Returns:
        Formatted string

    Examples:
        # Basic usage
        result = format("Hello {{ name }}!", name="Alice")
        # Returns: "Hello Alice!"

        # With custom functions
        def upper(text):
            return text.upper()

        result = format(
            "Hello {{ upper(name) }}!",
            custom_functions={"upper": upper},
            name="Alice"
        )
        # Returns: "Hello ALICE!"

        # With conditional logic
        result = format(
            "{% if count > 1 %}{{ count }} items{% else %}1 item{% endif %}",
            count=3
        )
        # Returns: "3 items"
    """
    try:
        # Create a minimal renderer with no snippets
        renderer = DefaultRenderer(snippets={}, functions={}, auto_escape=auto_escape)

        # Add custom functions if provided
        if custom_functions:
            for name, func in custom_functions.items():
                renderer.add_function(
                    name,
                    FunctionModel(
                        name=name,
                        callable=func,
                        signature=str(func.__name__)
                        if hasattr(func, "__name__")
                        else None,
                        docstring=func.__doc__ if hasattr(func, "__doc__") else None,
                    ),
                )

        # Render the template
        return renderer.render_text(template, variables)

    except Exception as e:
        raise TemplateError(f"Failed to format template: {e}")


def format_with_functions(
    template: str,
    functions: Dict[str, Callable],
    auto_escape: bool = False,
    **variables,
) -> str:
    """Format a template string with functions (alternative API).

    This is an alternative to the main format() function that makes the
    functions parameter more explicit.

    Args:
        template: Template string using Jinja2 syntax
        functions: Dict of custom functions to make available
        auto_escape: Whether to auto-escape HTML content
        **variables: Variables to substitute in the template

    Returns:
        Formatted string
    """
    return format(
        template, custom_functions=functions, auto_escape=auto_escape, **variables
    )
