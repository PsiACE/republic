"""Core data structures for prompt engineering."""

from pathlib import Path
from typing import Dict, Any, Optional, List, Literal, Set
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from enum import Enum
from abc import ABC, abstractmethod


class MessageRole(str, Enum):
    """Standard message roles for LLM conversations with extensibility."""

    # Standard roles as class constants
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"

    # Additional common roles
    FUNCTION = "function"
    DEVELOPER = "developer"
    MODERATOR = "moderator"

    @classmethod
    def is_standard(cls, role: str) -> bool:
        """Check if a role is one of the standard roles."""
        standard_roles = {cls.SYSTEM, cls.USER, cls.ASSISTANT, cls.TOOL, cls.FUNCTION}
        return role.lower() in standard_roles

    @classmethod
    def normalize(cls, role: str) -> str:
        """Normalize role string (lowercase, stripped)."""
        return role.strip().lower()


class PromptMessage(BaseModel):
    """A structured message for LLM conversations."""

    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = None
    role: str  # Changed from MessageRole enum to str for flexibility
    content: str
    truncation_priority: Optional[int] = Field(
        None, ge=0, description="Priority for truncation (lower = keep longer)"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Message content cannot be empty")
        return v

    @field_validator("role")
    @classmethod
    def normalize_role(cls, v):
        if not v or not v.strip():
            raise ValueError("Message role cannot be empty")
        return MessageRole.normalize(v)


class Snippet(BaseModel):
    """A reusable prompt snippet with validation."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=1)
    description: Optional[str] = Field(None, max_length=500)
    variables: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def name_valid_identifier(cls, v):
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                "Snippet name must be alphanumeric with underscores/hyphens"
            )
        return v

    @classmethod
    def from_file(cls, path: Path) -> "Snippet":
        """Load snippet from markdown file with optional frontmatter."""
        if not path.exists():
            raise FileNotFoundError(f"Snippet file not found: {path}")

        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as e:
            raise ValueError(f"Cannot read snippet file {path}: {e}")

        # Parse frontmatter
        metadata = {}
        variables = {}
        description = None

        if content.startswith("---\n"):
            parts = content.split("---\n", 2)
            if len(parts) >= 3:
                frontmatter = parts[1].strip()

                for line in frontmatter.split("\n"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        key = key.strip()
                        value = value.strip().strip("\"'")

                        if key == "description":
                            description = value
                        elif key.startswith("var_"):
                            variables[key[4:]] = value
                        else:
                            metadata[key] = value

                content = parts[2]

        return cls(
            name=path.stem,
            content=content.strip(),
            description=description,
            variables=variables,
            metadata=metadata,
        )


class Template(BaseModel):
    """A prompt template with Jinja2 support and validation."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=1)
    description: Optional[str] = Field(None, max_length=500)
    snippets: List[str] = Field(default_factory=list)
    variables: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    output_format: Literal["text", "messages"] = "text"

    @field_validator("name")
    @classmethod
    def name_valid_identifier(cls, v):
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                "Template name must be alphanumeric with underscores/hyphens"
            )
        return v

    @field_validator("snippets")
    @classmethod
    def snippets_unique(cls, v):
        if len(v) != len(set(v)):
            raise ValueError("Snippet names must be unique")
        return v

    @classmethod
    def from_file(cls, path: Path) -> "Template":
        """Load template from markdown file with validation."""
        if not path.exists():
            raise FileNotFoundError(f"Template file not found: {path}")

        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as e:
            raise ValueError(f"Cannot read template file {path}: {e}")

        # Parse frontmatter
        metadata = {}
        variables = {}
        snippets = []
        output_format = "text"
        description = None

        if content.startswith("---\n"):
            parts = content.split("---\n", 2)
            if len(parts) >= 3:
                frontmatter = parts[1].strip()

                for line in frontmatter.split("\n"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        key = key.strip()
                        value = value.strip().strip("\"'")

                        if key == "description":
                            description = value
                        elif key == "snippets":
                            snippets = [
                                s.strip() for s in value.split(",") if s.strip()
                            ]
                        elif key == "output_format":
                            if value not in ["text", "messages"]:
                                raise ValueError(f"Invalid output_format: {value}")
                            output_format = value
                        elif key.startswith("var_"):
                            variables[key[4:]] = value
                        else:
                            metadata[key] = value

                content = parts[2]

        return cls(
            name=path.stem,
            content=content.strip(),
            description=description,
            snippets=snippets,
            variables=variables,
            metadata=metadata,
            output_format=output_format,
        )


class Prompt(BaseModel):
    """A complete prompt with all components resolved."""

    model_config = ConfigDict(extra="forbid")

    content: str = ""
    messages: List[PromptMessage] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    source_template: Optional[str] = None
    used_snippets: List[str] = Field(default_factory=list)
    output_format: Literal["text", "messages"] = "text"

    @model_validator(mode="after")
    def validate_output_format(self):
        if self.output_format == "messages" and not self.messages:
            raise ValueError("Messages output format requires at least one message")
        if self.output_format == "text" and not self.content:
            raise ValueError("Text output format requires content")
        return self

    def __str__(self) -> str:
        if self.output_format == "messages" and self.messages:
            # Convert messages to string representation
            parts = []
            for msg in self.messages:
                role_prefix = f"[{msg.role.upper()}]"
                if msg.name:
                    role_prefix += f" {msg.name}:"
                parts.append(f"{role_prefix}\n{msg.content}")
            return "\n\n".join(parts)
        return self.content

    def to_openai_format(self) -> List[Dict[str, Any]]:
        """Convert to OpenAI-compatible message format."""
        if self.output_format == "messages" and self.messages:
            return [
                {
                    "role": msg.role,  # Already normalized string
                    "content": msg.content,
                    **({"name": msg.name} if msg.name else {}),
                }
                for msg in self.messages
            ]
        else:
            # Fallback: treat as single user message
            return [{"role": "user", "content": self.content}]


class Function(BaseModel):
    """Language-agnostic function metadata."""

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    name: str = Field(..., min_length=1, max_length=100)
    callable: Any  # Can be Python callable, JS function reference, etc.
    description: Optional[str] = Field(None, max_length=500)
    language: str = Field(default="python", max_length=50)
    source_file: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def name_valid_identifier(cls, v):
        # More relaxed validation for cross-language compatibility
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                "Function name must be alphanumeric with underscores/hyphens"
            )
        return v


class FunctionLoader(ABC):
    """Abstract base class for function loaders."""

    @abstractmethod
    def load_functions(self, workspace_path: Path) -> Dict[str, Function]:
        """
        Load functions from workspace.

        Args:
            workspace_path: Path to the workspace directory

        Returns:
            Dictionary of function name -> Function
        """
        pass

    @property
    @abstractmethod
    def language(self) -> str:
        """Return the language this loader supports."""
        pass

    @property
    @abstractmethod
    def supported_extensions(self) -> List[str]:
        """Return file extensions this loader can handle."""
        pass


class WorkspaceConfig(BaseModel):
    """Workspace configuration with validation."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    version: str = Field(default="1.0.0")
    defaults: Dict[str, Any] = Field(default_factory=dict)
    environments: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    function_loaders: List[str] = Field(
        default_factory=lambda: ["python"]
    )  # Default to Python

    @field_validator("name")
    @classmethod
    def name_valid(cls, v):
        if not v.replace("_", "").replace("-", "").replace(" ", "").isalnum():
            raise ValueError(
                "Workspace name must be alphanumeric with underscores, hyphens, or spaces"
            )
        return v


class Workspace(BaseModel):
    """A complete workspace with validation."""

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    name: str = Field(..., min_length=1, max_length=100)
    path: Path
    config: WorkspaceConfig
    snippets: Dict[str, Snippet] = Field(default_factory=dict)
    templates: Dict[str, Template] = Field(default_factory=dict)
    prompts: Dict[str, Template] = Field(default_factory=dict)  # Prompts are templates
    functions: Dict[str, Function] = Field(default_factory=dict)
    function_loaders: Dict[str, FunctionLoader] = Field(default_factory=dict)

    @model_validator(mode="after")
    def name_matches_config(self):
        if self.config and self.config.name != self.name:
            raise ValueError("Workspace name must match config name")
        return self

    def register_function_loader(self, loader: FunctionLoader) -> None:
        """Register a function loader for a specific language."""
        self.function_loaders[loader.language] = loader

    def get_function(self, name: str) -> Optional[Any]:
        """Get a function by name."""
        func = self.functions.get(name)
        return func.callable if func else None

    def list_functions(self) -> List[str]:
        """List all available function names."""
        return list(self.functions.keys())

    def get_functions_dict(self) -> Dict[str, Any]:
        """Get all functions as a dictionary for template rendering."""
        return {name: func.callable for name, func in self.functions.items()}

    def get_functions_by_language(self, language: str) -> Dict[str, Function]:
        """Get functions filtered by language."""
        return {
            name: func
            for name, func in self.functions.items()
            if func.language == language
        }

    def validate_snippet_references(self) -> Set[str]:
        """Validate that all snippet references in templates exist."""
        missing_snippets = set()

        for template in list(self.templates.values()) + list(self.prompts.values()):
            for snippet_name in template.snippets:
                if snippet_name not in self.snippets:
                    missing_snippets.add(snippet_name)

        return missing_snippets

    def get_environment_config(self, environment: str) -> Dict[str, Any]:
        """Get environment-specific configuration."""
        if environment in self.config.environments:
            return {**self.config.defaults, **self.config.environments[environment]}
        return self.config.defaults.copy()


# Registry for function loaders
_function_loader_registry: Dict[str, type] = {}


def register_function_loader(language: str):
    """Decorator to register function loaders."""

    def decorator(loader_class: type):
        if not issubclass(loader_class, FunctionLoader):
            msg = "Loader class must inherit from FunctionLoader"
            raise ValueError(msg)
        _function_loader_registry[language] = loader_class
        return loader_class

    return decorator


def get_function_loader(language: str) -> Optional[type]:
    """Get a registered function loader class by language."""
    return _function_loader_registry.get(language)


def list_supported_languages() -> List[str]:
    """List all supported languages."""
    return list(_function_loader_registry.keys())
