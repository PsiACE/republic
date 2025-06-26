class LoaderError(Exception):
    """Base exception for loader errors."""

    pass


class FunctionLoadError(LoaderError):
    """Exception raised when function loading fails."""

    pass


class WorkspaceValidationError(LoaderError):
    """Exception raised when workspace validation fails."""

    pass


class RenderError(Exception):
    """Base exception for rendering errors."""

    pass


class TemplateRenderError(RenderError):
    """Exception raised when template rendering fails."""

    pass
