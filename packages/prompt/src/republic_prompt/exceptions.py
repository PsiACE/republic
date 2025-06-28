"""Exception classes for Republic Prompt.

This module defines a clear hierarchy of exceptions with helpful error messages
to assist users in debugging their prompt configurations and usage.
"""


class RepublicPromptError(Exception):
    """Base exception for all Republic Prompt errors."""
    pass


class WorkspaceError(RepublicPromptError):
    """Raised when workspace loading or configuration fails."""
    pass


class TemplateError(RepublicPromptError):
    """Raised when template parsing or rendering fails."""
    
    def __init__(self, message: str, template_name: str = None, line_number: int = None):
        self.template_name = template_name
        self.line_number = line_number
        
        if template_name and line_number:
            message = f"{message} (template: {template_name}, line: {line_number})"
        elif template_name:
            message = f"{message} (template: {template_name})"
            
        super().__init__(message)


class LoaderError(RepublicPromptError):
    """Raised when content loading fails."""
    pass


class ValidationError(RepublicPromptError):
    """Raised when data validation fails."""
    pass 