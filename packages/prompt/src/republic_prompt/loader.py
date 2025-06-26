"""Lightweight loaders for prompts, snippets, and workspaces with pluggable function loaders."""

import toml
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from .core import (
    Prompt,
    Snippet,
    Template,
    Workspace,
    Function,
    WorkspaceConfig,
    FunctionLoader,
    get_function_loader,
    list_supported_languages,
)
from .exception import LoaderError, FunctionLoadError, WorkspaceValidationError

# Set up logging
logger = logging.getLogger(__name__)


def load_snippet(path: Union[str, Path]) -> Snippet:
    """
    Load a single snippet from file with error handling.

    Args:
        path: Path to the snippet file

    Returns:
        Loaded snippet

    Raises:
        LoaderError: If loading fails
    """
    try:
        return Snippet.from_file(Path(path))
    except (FileNotFoundError, ValueError) as e:
        raise LoaderError(f"Failed to load snippet from {path}: {e}")


def load_template(path: Union[str, Path]) -> Template:
    """
    Load a single template from file, with optional TOML config.

    Args:
        path: Path to the template file

    Returns:
        Loaded template with merged TOML configuration

    Raises:
        LoaderError: If loading fails
    """
    path = Path(path)

    try:
        # Load the markdown template first
        template = Template.from_file(path)

        # Check for accompanying TOML config
        toml_path = path.parent / f"{path.stem}.toml"
        if toml_path.exists():
            try:
                config = toml.load(toml_path)
                template_config = config.get("template", {})

                # Merge TOML config with template (TOML takes precedence)
                template.metadata.update(template_config.get("metadata", {}))
                template.variables.update(template_config.get("variables", {}))

                # Handle snippets
                toml_snippets = template_config.get("snippets", [])
                if isinstance(toml_snippets, str):
                    toml_snippets = [
                        s.strip() for s in toml_snippets.split(",") if s.strip()
                    ]
                template.snippets.extend(toml_snippets)

                # Remove duplicates while preserving order
                seen = set()
                template.snippets = [
                    x for x in template.snippets if not (x in seen or seen.add(x))
                ]

                # Set output format from config
                if "output_format" in template_config:
                    template.output_format = template_config["output_format"]

                # Update description if provided
                if "description" in template_config:
                    template.description = template_config["description"]

            except (toml.TomlDecodeError, KeyError, ValueError) as e:
                logger.warning(f"Failed to load TOML config for {path}: {e}")

        return template

    except (FileNotFoundError, ValueError) as e:
        raise LoaderError(f"Failed to load template from {path}: {e}")


def load_prompt(path: Union[str, Path], variables: Optional[Dict] = None) -> Prompt:
    """
    Load and render a prompt from template file.

    Args:
        path: Path to the template file
        variables: Variables to pass to the template

    Returns:
        Rendered prompt

    Raises:
        LoaderError: If loading or rendering fails
    """
    try:
        from .renderer import render

        template = load_template(path)
        return render(template, variables or {})
    except Exception as e:
        raise LoaderError(f"Failed to load prompt from {path}: {e}")


def load_functions_with_loaders(
    workspace_path: Path, function_loaders: Dict[str, FunctionLoader]
) -> Dict[str, Function]:
    """
    Load functions using provided function loaders.

    Args:
        workspace_path: Path to the workspace directory
        function_loaders: Dictionary of language -> loader instances

    Returns:
        Dictionary of function name -> Function

    Raises:
        FunctionLoadError: If loading fails
    """
    all_functions = {}

    for language, loader in function_loaders.items():
        try:
            functions = loader.load_functions(workspace_path)

            # Check for conflicts across languages
            conflicts = set(functions.keys()) & set(all_functions.keys())
            if conflicts:
                logger.warning(
                    f"Cross-language function conflicts from {language}: {conflicts}"
                )
                for conflict in conflicts:
                    old_func = all_functions[conflict]
                    logger.warning(
                        f"  '{conflict}' redefined (was {old_func.language} from {old_func.source_file})"
                    )

            all_functions.update(functions)

            if functions:
                logger.info(f"Loaded {len(functions)} {language} functions")

        except Exception as e:
            logger.error(f"Failed to load {language} functions: {e}")
            # Continue with other loaders instead of failing completely
            continue

    return all_functions


def create_default_function_loaders(languages: List[str]) -> Dict[str, FunctionLoader]:
    """
    Create default function loaders for specified languages.

    Args:
        languages: List of language names to create loaders for

    Returns:
        Dictionary of language -> loader instances

    Raises:
        FunctionLoadError: If loader creation fails
    """
    loaders = {}
    supported = list_supported_languages()

    for language in languages:
        if language not in supported:
            logger.warning(f"Unsupported language: {language}. Supported: {supported}")
            continue

        loader_class = get_function_loader(language)
        if loader_class:
            try:
                loaders[language] = loader_class()
            except Exception as e:
                logger.error(f"Failed to create {language} loader: {e}")
        else:
            logger.warning(f"No loader found for language: {language}")

    return loaders


def load_prompts_config(config_path: Path) -> WorkspaceConfig:
    """
    Load prompts workspace configuration from TOML file.

    Args:
        config_path: Path to prompts.toml file

    Returns:
        Loaded workspace configuration

    Raises:
        LoaderError: If loading fails
    """
    if not config_path.exists():
        # Return default config
        return WorkspaceConfig(name=config_path.parent.name)

    try:
        config_data = toml.load(config_path)
        prompts_section = config_data.get("prompts", {})

        return WorkspaceConfig(
            name=prompts_section.get("name", config_path.parent.name),
            description=prompts_section.get("description"),
            version=prompts_section.get("version", "1.0.0"),
            defaults=prompts_section.get("defaults", {}),
            environments=prompts_section.get("environments", {}),
            function_loaders=prompts_section.get("function_loaders", ["python"]),
        )
    except (toml.TomlDecodeError, ValueError) as e:
        raise LoaderError(f"Failed to load prompts config from {config_path}: {e}")


def load_workspace(
    path: Union[str, Path],
    custom_function_loaders: Optional[Dict[str, FunctionLoader]] = None,
    environment: Optional[str] = None,
) -> Workspace:
    """
    Load workspace using file system conventions and pluggable function loaders.

    Expected structure:
    workspace/
    ├── snippets/           # Reusable prompt snippets
    │   ├── greeting.md
    │   └── instructions.md
    ├── templates/          # Prompt templates (need rendering)
    │   ├── code_review.md
    │   ├── code_review.toml  # Optional TOML config
    │   └── system_agent.md
    ├── prompts/           # Pre-built prompts (ready to use)
    │   └── python_review.md
    ├── functions.py       # Single file functions (Python)
    ├── functions.js       # Single file functions (JavaScript)
    ├── functions/         # Multi-file functions (any language)
    │   ├── utils.py
    │   ├── helpers.js
    │   └── formatters.lua
    └── prompts.toml       # Workspace configuration

    Args:
        path: Path to the workspace directory
        custom_function_loaders: Optional custom function loaders to use
        environment: Optional environment to use

    Returns:
        Loaded workspace

    Raises:
        WorkspaceValidationError: If workspace validation fails
        LoaderError: If loading fails
    """
    workspace_path = Path(path)

    if not workspace_path.exists():
        raise LoaderError(f"Workspace directory does not exist: {workspace_path}")

    if not workspace_path.is_dir():
        raise LoaderError(f"Workspace path is not a directory: {workspace_path}")

    try:
        # Load workspace configuration
        config_path = workspace_path / "prompts.toml"
        config = load_prompts_config(config_path)

        # Create workspace object
        workspace = Workspace(
            name=config.name,
            path=workspace_path,
            config=config,
        )

        # Set up function loaders
        if custom_function_loaders:
            # Use provided custom loaders
            for language, loader in custom_function_loaders.items():
                workspace.register_function_loader(loader)
            function_loaders = custom_function_loaders
        else:
            # Create default loaders based on config
            function_loaders = create_default_function_loaders(config.function_loaders)
            for language, loader in function_loaders.items():
                workspace.register_function_loader(loader)

        # Load functions using the configured loaders
        if function_loaders:
            workspace.functions = load_functions_with_loaders(
                workspace_path, function_loaders
            )

        # Load snippets
        snippets_dir = workspace_path / "snippets"
        if snippets_dir.exists():
            for snippet_file in snippets_dir.glob("*.md"):
                try:
                    snippet = load_snippet(snippet_file)
                    workspace.snippets[snippet.name] = snippet
                except LoaderError as e:
                    logger.warning(f"Failed to load snippet {snippet_file}: {e}")

        # Load templates (with TOML support)
        templates_dir = workspace_path / "templates"
        if templates_dir.exists():
            for template_file in templates_dir.glob("*.md"):
                try:
                    template = load_template(template_file)
                    # Apply workspace defaults to template variables
                    defaults = workspace.config.defaults

                    # Start with template variables, then apply defaults, then environment
                    merged_vars = {**template.variables}
                    merged_vars.update(defaults)

                    # Apply environment-specific settings if specified (highest precedence)
                    if environment and environment in workspace.config.environments:
                        env_config = workspace.config.environments[environment]
                        merged_vars.update(env_config)

                    template.variables = merged_vars
                    workspace.templates[template.name] = template
                except LoaderError as e:
                    logger.warning(f"Failed to load template {template_file}: {e}")

        # Load prompts (as templates, but treated as pre-built)
        prompts_dir = workspace_path / "prompts"
        if prompts_dir.exists():
            for prompt_file in prompts_dir.glob("*.md"):
                try:
                    template = load_template(prompt_file)
                    # Apply workspace defaults to prompt variables
                    defaults = workspace.config.defaults

                    # Start with template variables, then apply defaults, then environment
                    merged_vars = {**template.variables}
                    merged_vars.update(defaults)

                    # Apply environment-specific settings if specified (highest precedence)
                    if environment and environment in workspace.config.environments:
                        env_config = workspace.config.environments[environment]
                        merged_vars.update(env_config)

                    template.variables = merged_vars
                    workspace.prompts[template.name] = template
                except LoaderError as e:
                    logger.warning(f"Failed to load prompt {prompt_file}: {e}")

        # Validate workspace
        missing_snippets = workspace.validate_snippet_references()
        if missing_snippets:
            raise WorkspaceValidationError(
                f"Missing snippet references: {missing_snippets}"
            )

        logger.info(
            f"Loaded workspace '{workspace.name}' with {len(workspace.snippets)} snippets, "
            f"{len(workspace.templates)} templates, {len(workspace.prompts)} prompts, "
            f"and {len(workspace.functions)} functions across {len(function_loaders)} languages"
        )

        return workspace

    except (WorkspaceValidationError, FunctionLoadError) as e:
        raise e
    except Exception as e:
        raise LoaderError(f"Failed to load workspace from {workspace_path}: {e}")


def discover_workspaces(search_path: Union[str, Path] = ".") -> List[Workspace]:
    """
    Discover workspaces by looking for directories with prompt structure.

    A workspace is identified by having at least one of:
    - snippets/ directory
    - templates/ directory
    - prompts/ directory
    - prompts.toml file
    - functions.* files (any language)
    - functions/ directory

    Args:
        search_path: Path to search for workspaces

    Returns:
        List of discovered workspaces
    """
    search_path = Path(search_path)
    workspaces = []

    if not search_path.exists():
        logger.warning(f"Search path does not exist: {search_path}")
        return workspaces

    for item in search_path.iterdir():
        if not item.is_dir():
            continue

        # Check if this directory looks like a workspace
        indicators = [
            item / "snippets",
            item / "templates",
            item / "prompts",
            item / "prompts.toml",
            item / "functions",
        ]

        # Check for functions.* files
        for func_file in item.glob("functions.*"):
            if func_file.is_file():
                indicators.append(func_file)

        if any(indicator.exists() for indicator in indicators):
            try:
                workspace = load_workspace(item)
                workspaces.append(workspace)
            except Exception as e:
                logger.warning(f"Failed to load workspace from {item}: {e}")

    return workspaces


def list_workspace_contents(workspace: Workspace) -> Dict[str, Any]:
    """
    Get a summary of workspace contents for debugging/inspection.

    Args:
        workspace: Loaded workspace object

    Returns:
        Dictionary with counts and lists of available items
    """
    return {
        "name": workspace.name,
        "path": str(workspace.path),
        "config": {
            "description": workspace.config.description,
            "version": workspace.config.version,
            "environments": list(workspace.config.environments.keys()),
            "function_loaders": workspace.config.function_loaders,
        },
        "counts": {
            "snippets": len(workspace.snippets),
            "templates": len(workspace.templates),
            "prompts": len(workspace.prompts),
            "functions": len(workspace.functions),
            "function_loaders": len(workspace.function_loaders),
        },
        "snippets": [
            {
                "name": name,
                "description": snippet.description,
                "variables": list(snippet.variables.keys()),
            }
            for name, snippet in workspace.snippets.items()
        ],
        "templates": [
            {
                "name": name,
                "description": template.description,
                "snippets": template.snippets,
                "variables": list(template.variables.keys()),
                "output_format": template.output_format,
            }
            for name, template in workspace.templates.items()
        ],
        "prompts": [
            {
                "name": name,
                "description": template.description,
                "snippets": template.snippets,
                "variables": list(template.variables.keys()),
            }
            for name, template in workspace.prompts.items()
        ],
        "functions": [
            {
                "name": name,
                "description": func.description,
                "language": func.language,
                "source_file": func.source_file,
            }
            for name, func in workspace.functions.items()
        ],
        "function_loaders": [
            {
                "language": language,
                "loader_class": loader.__class__.__name__,
                "supported_extensions": loader.supported_extensions,
            }
            for language, loader in workspace.function_loaders.items()
        ],
    }
