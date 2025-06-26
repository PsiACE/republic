"""Modern Jinja2-based template renderer with improved error handling."""

import re
import logging
from typing import Dict, Any, Optional, List
from jinja2 import Environment, BaseLoader, TemplateError, meta
from jinja2.exceptions import TemplateNotFound, TemplateSyntaxError, UndefinedError
from .core import Template, Snippet, Prompt, PromptMessage, MessageRole, Workspace
from .exception import TemplateRenderError

# Set up logging
logger = logging.getLogger(__name__)


class SnippetLoader(BaseLoader):
    """Custom Jinja2 loader for snippets."""

    def __init__(self, snippets: Dict[str, Snippet]):
        self.snippets = snippets

    def get_source(self, environment: Environment, template: str) -> tuple:
        """Load snippet content as Jinja2 template source."""
        if template not in self.snippets:
            raise TemplateNotFound(f"Snippet '{template}' not found")

        snippet = self.snippets[template]
        source = snippet.content

        # Return (source, filename, uptodate_func)
        return source, f"snippet:{template}", lambda: True


def create_jinja_environment(
    workspace: Optional[Workspace] = None,
    snippets: Optional[Dict[str, Snippet]] = None,
    functions: Optional[Dict[str, Any]] = None,
) -> Environment:
    """
    Create a Jinja2 environment with workspace support.

    Args:
        workspace: Workspace object (preferred)
        snippets: Snippets dictionary (fallback)
        functions: Functions dictionary (fallback)

    Returns:
        Configured Jinja2 environment
    """
    # Use workspace if provided, otherwise use individual components
    if workspace:
        snippet_dict = workspace.snippets
        function_dict = workspace.get_functions_dict()
    else:
        snippet_dict = snippets or {}
        function_dict = functions or {}

    # Create environment with snippet loader
    env = Environment(
        loader=SnippetLoader(snippet_dict),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )

    # Add workspace functions to global context
    env.globals.update(function_dict)

    # Add useful built-in functions
    env.globals.update(
        {
            "len": len,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict,
            "set": set,
            "tuple": tuple,
            "enumerate": enumerate,
            "range": range,
            "zip": zip,
            "sorted": sorted,
            "reversed": reversed,
            "min": min,
            "max": max,
            "sum": sum,
            "abs": abs,
            "round": round,
        }
    )

    return env


def parse_message_blocks(content: str) -> List[PromptMessage]:
    """
    Parse message blocks from template content.

    Expected format:
    [SYSTEM]
    System message content

    [USER] Alice
    User message content

    [ASSISTANT]
    Assistant response

    [CUSTOM_ROLE] Optional Name
    Custom role message content

    Args:
        content: Template content with message blocks

    Returns:
        List of parsed messages

    Raises:
        RenderError: If parsing fails
    """
    messages = []

    # Pattern to match message blocks: [ROLE] optional_name
    pattern = r"^\[(\w+)\](?:\s+(.+?))?$"

    current_role = None
    current_name = None
    current_content = []

    for line in content.split("\n"):
        match = re.match(pattern, line.strip())

        if match:
            # Save previous message if exists
            if current_role and current_content:
                content_str = "\n".join(current_content).strip()
                if content_str:
                    # Use role directly as string, no enum validation needed
                    role = MessageRole.normalize(current_role)
                    messages.append(
                        PromptMessage(role=role, name=current_name, content=content_str)
                    )

            # Start new message
            current_role = match.group(1)
            current_name = match.group(2) if match.group(2) else None
            current_content = []
        else:
            # Accumulate content for current message
            if current_role:
                current_content.append(line)

    # Save final message
    if current_role and current_content:
        content_str = "\n".join(current_content).strip()
        if content_str:
            # Use role directly as string, no enum validation needed
            role = MessageRole.normalize(current_role)
            messages.append(
                PromptMessage(role=role, name=current_name, content=content_str)
            )

    return messages


def render_template_content(
    content: str,
    variables: Dict[str, Any],
    workspace: Optional[Workspace] = None,
    snippets: Optional[Dict[str, Snippet]] = None,
    functions: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Render template content using Jinja2.

    Args:
        content: Template content to render
        variables: Variables to pass to template
        workspace: Workspace object (preferred)
        snippets: Snippets dictionary (fallback)
        functions: Functions dictionary (fallback)

    Returns:
        Rendered content

    Raises:
        TemplateRenderError: If rendering fails
    """
    try:
        env = create_jinja_environment(workspace, snippets, functions)
        template = env.from_string(content)

        # Render with provided variables
        return template.render(**variables)

    except TemplateSyntaxError as e:
        raise TemplateRenderError(f"Template syntax error: {e}")
    except UndefinedError as e:
        raise TemplateRenderError(f"Undefined variable in template: {e}")
    except TemplateError as e:
        raise TemplateRenderError(f"Template rendering error: {e}")
    except Exception as e:
        raise TemplateRenderError(f"Unexpected error during rendering: {e}")


def render(
    template: Template,
    variables: Optional[Dict[str, Any]] = None,
    workspace: Optional[Workspace] = None,
    snippets: Optional[Dict[str, Snippet]] = None,
    functions: Optional[Dict[str, Any]] = None,
    environment: Optional[str] = None,
) -> Prompt:
    """
    Render a template into a complete prompt.

    Args:
        template: Template to render
        variables: Variables to pass to template (merged with template defaults)
        workspace: Workspace object (preferred for context)
        snippets: Snippets dictionary (fallback)
        functions: Functions dictionary (fallback)
        environment: Environment name for workspace config

    Returns:
        Rendered prompt

    Raises:
        TemplateRenderError: If rendering fails
    """
    try:
        # Merge variables: template defaults < provided variables
        render_variables = {**template.variables}
        if variables:
            render_variables.update(variables)

        # Add environment-specific variables from workspace
        if workspace and environment:
            env_config = workspace.get_environment_config(environment)
            render_variables = {**env_config, **render_variables}

        # Render the template content
        rendered_content = render_template_content(
            template.content, render_variables, workspace, snippets, functions
        )

        # Create prompt based on output format
        if template.output_format == "messages":
            # Parse message blocks
            messages = parse_message_blocks(rendered_content)

            if not messages:
                raise TemplateRenderError(
                    "No valid messages found in template with 'messages' output format"
                )

            return Prompt(
                content="",
                messages=messages,
                metadata=template.metadata.copy(),
                source_template=template.name,
                used_snippets=template.snippets.copy(),
                output_format="messages",
            )
        else:
            # Text format
            return Prompt(
                content=rendered_content,
                messages=[],
                metadata=template.metadata.copy(),
                source_template=template.name,
                used_snippets=template.snippets.copy(),
                output_format="text",
            )

    except TemplateRenderError:
        raise
    except Exception as e:
        raise TemplateRenderError(f"Failed to render template '{template.name}': {e}")


def render_snippet(
    snippet: Snippet,
    variables: Optional[Dict[str, Any]] = None,
    workspace: Optional[Workspace] = None,
    functions: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Render a snippet with variables.

    Args:
        snippet: Snippet to render
        variables: Variables to pass to snippet
        workspace: Workspace object for context
        functions: Functions dictionary (fallback)

    Returns:
        Rendered snippet content

    Raises:
        TemplateRenderError: If rendering fails
    """
    try:
        # Merge variables: snippet defaults < provided variables
        render_variables = {**snippet.variables}
        if variables:
            render_variables.update(variables)

        return render_template_content(
            snippet.content, render_variables, workspace, functions=functions
        )

    except TemplateRenderError:
        raise
    except Exception as e:
        raise TemplateRenderError(f"Failed to render snippet '{snippet.name}': {e}")


def validate_template_syntax(
    template: Template,
    workspace: Optional[Workspace] = None,
    snippets: Optional[Dict[str, Snippet]] = None,
    functions: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """
    Validate template syntax and return any errors.

    Args:
        template: Template to validate
        workspace: Workspace object (preferred)
        snippets: Snippets dictionary (fallback)
        functions: Functions dictionary (fallback)

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []

    try:
        env = create_jinja_environment(workspace, snippets, functions)

        # Parse template to check syntax
        try:
            parsed = env.parse(template.content)
        except TemplateSyntaxError as e:
            errors.append(f"Template syntax error: {e}")
            return errors

        # Check for undefined variables
        try:
            undeclared = meta.find_undeclared_variables(parsed)
            available_vars = set(template.variables.keys())

            if workspace:
                available_vars.update(workspace.get_functions_dict().keys())
            elif functions:
                available_vars.update(functions.keys())

            # Add built-in variables
            available_vars.update(
                {
                    "len",
                    "str",
                    "int",
                    "float",
                    "bool",
                    "list",
                    "dict",
                    "set",
                    "tuple",
                    "enumerate",
                    "range",
                    "zip",
                    "sorted",
                    "reversed",
                    "min",
                    "max",
                    "sum",
                    "abs",
                    "round",
                }
            )

            missing_vars = undeclared - available_vars
            if missing_vars:
                errors.append(f"Undefined variables: {', '.join(sorted(missing_vars))}")

        except Exception as e:
            errors.append(f"Variable analysis error: {e}")

        # Check snippet references
        for snippet_name in template.snippets:
            snippet_dict = workspace.snippets if workspace else (snippets or {})
            if snippet_name not in snippet_dict:
                errors.append(f"Missing snippet: {snippet_name}")

    except Exception as e:
        errors.append(f"Template validation error: {e}")

    return errors


def get_template_variables(
    template: Template,
    workspace: Optional[Workspace] = None,
    snippets: Optional[Dict[str, Snippet]] = None,
) -> Dict[str, Any]:
    """
    Extract all variables used in a template.

    Args:
        template: Template to analyze
        workspace: Workspace object (preferred)
        snippets: Snippets dictionary (fallback)

    Returns:
        Dictionary of variable names and their default values
    """
    variables = template.variables.copy()

    try:
        env = create_jinja_environment(workspace, snippets)
        parsed = env.parse(template.content)
        undeclared = meta.find_undeclared_variables(parsed)

        # Add undeclared variables with None as default
        for var in undeclared:
            if var not in variables:
                variables[var] = None

    except Exception as e:
        logger.warning(
            f"Failed to extract variables from template '{template.name}': {e}"
        )

    return variables


def preview_render(
    template: Template,
    variables: Optional[Dict[str, Any]] = None,
    workspace: Optional[Workspace] = None,
    max_length: int = 500,
) -> str:
    """
    Render a template preview with truncation for debugging.

    Args:
        template: Template to preview
        variables: Variables to pass to template
        workspace: Workspace object for context
        max_length: Maximum length of preview

    Returns:
        Truncated rendered content
    """
    try:
        prompt = render(template, variables, workspace)
        content = str(prompt)

        if len(content) > max_length:
            return content[:max_length] + "..."
        return content

    except Exception as e:
        return f"[Render Error: {e}]"
