"""
Type safety and validation for the context system.

Adds runtime validation and type checking while keeping it simple.
Follows Linus principle: "Good taste" means knowing when to add complexity.
"""

from typing import Any, Dict, Type, Union, get_type_hints, get_origin, get_args
from dataclasses import dataclass, field
from functools import wraps
import inspect
from context import AgentContext, ContextualAgent


class ContextValidationError(Exception):
    """Raised when context validation fails."""
    pass


@dataclass
class ValidationRule:
    """
    Simple validation rule.
    
    No over-engineering - just check if value passes a test.
    """
    name: str
    validator: callable
    message: str = ""
    
    def validate(self, value: Any) -> bool:
        """Run validation. Returns True if valid."""
        try:
            return bool(self.validator(value))
        except Exception:
            return False
    
    def get_message(self) -> str:
        """Get validation error message."""
        return self.message or f"Validation failed for {self.name}"


class ContextValidator:
    """
    Context validator with simple rules.
    
    Validates context fields against defined rules.
    """
    
    def __init__(self):
        self.rules: Dict[str, list[ValidationRule]] = {}
    
    def add_rule(self, field: str, rule: ValidationRule) -> None:
        """Add validation rule for field."""
        if field not in self.rules:
            self.rules[field] = []
        self.rules[field].append(rule)
    
    def require_field(self, field: str, message: str = None) -> None:
        """Require field to be present and not None."""
        rule = ValidationRule(
            name=f"required_{field}",
            validator=lambda x: x is not None,
            message=message or f"Field {field} is required"
        )
        self.add_rule(field, rule)
    
    def validate_type(self, field: str, expected_type: Type, message: str = None) -> None:
        """Validate field type."""
        rule = ValidationRule(
            name=f"type_{field}",
            validator=lambda x: isinstance(x, expected_type),
            message=message or f"Field {field} must be {expected_type.__name__}"
        )
        self.add_rule(field, rule)
    
    def validate_range(self, field: str, min_val: Any = None, max_val: Any = None) -> None:
        """Validate field is within range."""
        def range_check(value):
            if min_val is not None and value < min_val:
                return False
            if max_val is not None and value > max_val:
                return False
            return True
        
        rule = ValidationRule(
            name=f"range_{field}",
            validator=range_check,
            message=f"Field {field} must be between {min_val} and {max_val}"
        )
        self.add_rule(field, rule)
    
    def validate_context(self, context: AgentContext) -> None:
        """
        Validate context against all rules.
        
        Raises ContextValidationError if validation fails.
        """
        errors = []
        
        # Check core fields
        core_fields = {
            'agent_id': context.agent_id,
            'session_id': context.session_id,
            'user_id': context.user_id,
            'timestamp': context.timestamp,
        }
        
        for field, value in core_fields.items():
            if field in self.rules:
                for rule in self.rules[field]:
                    if not rule.validate(value):
                        errors.append(rule.get_message())
        
        # Check metadata fields
        for field in self.rules:
            if field not in core_fields and field in context.metadata:
                value = context.metadata[field]
                for rule in self.rules[field]:
                    if not rule.validate(value):
                        errors.append(rule.get_message())
        
        if errors:
            raise ContextValidationError("; ".join(errors))


def validate_context(validator: ContextValidator):
    """
    Decorator for validating context in agent methods.
    
    Simple decorator pattern - validates context before method execution.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, context: AgentContext, *args, **kwargs):
            validator.validate_context(context)
            return func(self, context, *args, **kwargs)
        return wrapper
    return decorator


class TypedContextualAgent(ContextualAgent):
    """
    Contextual agent with type checking.
    
    Automatically validates context types based on method signatures.
    """
    
    def __init__(self):
        self._validator = self._create_validator()
    
    def _create_validator(self) -> ContextValidator:
        """Create validator from process method signature."""
        validator = ContextValidator()
        
        # Get type hints from process method
        try:
            hints = get_type_hints(self.process)
            if 'context' in hints:
                # Basic validation - ensure it's AgentContext
                validator.validate_type('__context__', AgentContext)
        except Exception:
            # If type hints fail, just do basic validation
            pass
        
        # Add basic required fields
        validator.require_field('agent_id')
        validator.require_field('session_id')
        
        return validator
    
    def process(self, context: AgentContext) -> Any:
        """Override this method. Context will be validated automatically."""
        # Validate context before processing
        try:
            # Basic validation that it's an AgentContext
            if not isinstance(context, AgentContext):
                raise ContextValidationError("Context must be AgentContext instance")
        except Exception as e:
            raise ContextValidationError(f"Context validation failed: {e}")
        
        return super().process(context)


# Common validators
def create_chat_validator() -> ContextValidator:
    """Create validator for chat agents."""
    validator = ContextValidator()
    validator.require_field('agent_id')
    validator.require_field('session_id')
    validator.validate_type('message', str, "Message must be a string")
    return validator


def create_task_validator() -> ContextValidator:
    """Create validator for task agents."""
    validator = ContextValidator()
    validator.require_field('agent_id')
    validator.require_field('session_id')
    validator.require_field('task_type')
    validator.validate_type('task_type', str)
    return validator


# Type-safe context creation
def create_typed_context(
    agent_id: str,
    session_id: str = None,
    user_id: str = None,
    validator: ContextValidator = None,
    **metadata: Any
) -> AgentContext:
    """
    Create context with optional validation.
    
    Validates the created context if validator is provided.
    """
    from context import create_context
    
    context = create_context(
        agent_id=agent_id,
        session_id=session_id,
        user_id=user_id,
        **metadata
    )
    
    if validator:
        validator.validate_context(context)
    
    return context


# Runtime type checking utilities
def check_context_type(context: Any) -> AgentContext:
    """
    Runtime type check for context.
    
    Returns context if valid, raises TypeError otherwise.
    """
    if not isinstance(context, AgentContext):
        raise TypeError(f"Expected AgentContext, got {type(context).__name__}")
    return context


def safe_get_metadata(context: AgentContext, key: str, expected_type: Type[Any]) -> Any:
    """
    Safely get metadata with type checking.
    
    Returns value if type matches, raises TypeError otherwise.
    """
    value = context.get(key)
    if value is not None and not isinstance(value, expected_type):
        raise TypeError(f"Expected {expected_type.__name__} for {key}, got {type(value).__name__}")
    return value


# Context schema definition
@dataclass
class ContextSchema:
    """
    Schema definition for context validation.
    
    Defines expected structure and types for context.
    """
    required_fields: list[str] = field(default_factory=list)
    optional_fields: list[str] = field(default_factory=list)
    field_types: Dict[str, Type] = field(default_factory=dict)
    
    def validate(self, context: AgentContext) -> None:
        """Validate context against schema."""
        errors = []
        
        # Check required fields
        for field in self.required_fields:
            if field not in ['agent_id', 'session_id', 'user_id', 'timestamp']:
                # Check in metadata
                if field not in context.metadata:
                    errors.append(f"Required field {field} missing")
            else:
                # Check core fields
                value = getattr(context, field, None)
                if value is None:
                    errors.append(f"Required field {field} missing")
        
        # Check field types
        for field, expected_type in self.field_types.items():
            if field in context.metadata:
                value = context.metadata[field]
                if not isinstance(value, expected_type):
                    errors.append(f"Field {field} should be {expected_type.__name__}")
        
        if errors:
            raise ContextValidationError("; ".join(errors))


# Schema builder
class SchemaBuilder:
    """Builder for context schemas."""
    
    def __init__(self):
        self.schema = ContextSchema()
    
    def require(self, *fields: str) -> 'SchemaBuilder':
        """Add required fields."""
        self.schema.required_fields.extend(fields)
        return self
    
    def optional(self, *fields: str) -> 'SchemaBuilder':
        """Add optional fields."""
        self.schema.optional_fields.extend(fields)
        return self
    
    def type_field(self, field: str, field_type: Type) -> 'SchemaBuilder':
        """Add type constraint for field."""
        self.schema.field_types[field] = field_type
        return self
    
    def build(self) -> ContextSchema:
        """Build the schema."""
        return self.schema