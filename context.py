"""
Context Engineering for Agents

A clean, KISS-compliant implementation of context structures and traits
for agent systems. Follows Linus-style best practices for simplicity
and maintainability.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Protocol, TypeVar, Generic
from contextlib import contextmanager
from threading import local
import uuid
from datetime import datetime


# Type definitions
T = TypeVar('T')
ContextData = Dict[str, Any]


@dataclass(frozen=True)
class AgentContext:
    """
    Immutable context structure for agent execution.
    
    Keeps it simple - just the essential data an agent needs.
    Immutable to prevent accidental state corruption.
    """
    agent_id: str
    session_id: str
    user_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: ContextData = field(default_factory=dict)
    
    def with_metadata(self, **kwargs: Any) -> 'AgentContext':
        """Create new context with additional metadata."""
        new_metadata = {**self.metadata, **kwargs}
        return AgentContext(
            agent_id=self.agent_id,
            session_id=self.session_id,
            user_id=self.user_id,
            timestamp=self.timestamp,
            metadata=new_metadata
        )
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get metadata value with default."""
        return self.metadata.get(key, default)


class ContextAware(Protocol):
    """
    Protocol defining context-aware behavior.
    
    Using Protocol instead of ABC for duck typing - more Pythonic.
    """
    def execute(self, context: AgentContext) -> Any:
        """Execute with given context."""
        ...


class ContextualAgent(ABC):
    """
    Abstract base for agents that operate with context.
    
    Simple trait-like interface. Agents must implement process().
    """
    
    @abstractmethod
    def process(self, context: AgentContext) -> Any:
        """Process request with context. Override this."""
        pass
    
    def __call__(self, context: AgentContext) -> Any:
        """Make agent callable. Convenience method."""
        return self.process(context)


class ContextManager:
    """
    Thread-safe context management.
    
    Simple, no magic. Just stores and retrieves context per thread.
    """
    
    def __init__(self):
        self._local = local()
    
    def set_context(self, context: AgentContext) -> None:
        """Set current context for this thread."""
        self._local.context = context
    
    def get_context(self) -> Optional[AgentContext]:
        """Get current context for this thread."""
        return getattr(self._local, 'context', None)
    
    def clear_context(self) -> None:
        """Clear current context."""
        if hasattr(self._local, 'context'):
            delattr(self._local, 'context')
    
    @contextmanager
    def context_scope(self, context: AgentContext):
        """Context manager for scoped context execution."""
        old_context = self.get_context()
        try:
            self.set_context(context)
            yield context
        finally:
            if old_context:
                self.set_context(old_context)
            else:
                self.clear_context()


# Global context manager instance
_context_manager = ContextManager()


def get_current_context() -> Optional[AgentContext]:
    """Get current thread's context. Simple global access."""
    return _context_manager.get_context()


def create_context(
    agent_id: str,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    **metadata: Any
) -> AgentContext:
    """
    Factory function for creating contexts.
    
    Generates IDs if not provided. Keeps it simple.
    """
    if not session_id:
        session_id = str(uuid.uuid4())
    
    return AgentContext(
        agent_id=agent_id,
        session_id=session_id,
        user_id=user_id,
        metadata=metadata
    )


@contextmanager
def agent_context(context: AgentContext):
    """Context manager for agent execution scope."""
    with _context_manager.context_scope(context):
        yield context


class ContextualMixin:
    """
    Mixin for adding context awareness to existing classes.
    
    Simple composition pattern. Add context behavior without inheritance.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._context: Optional[AgentContext] = None
    
    def set_context(self, context: AgentContext) -> None:
        """Set context for this instance."""
        self._context = context
    
    @property
    def context(self) -> Optional[AgentContext]:
        """Get current context (instance or thread-local)."""
        return self._context or get_current_context()
    
    def with_context(self, context: AgentContext):
        """Return context manager for scoped execution."""
        return agent_context(context)


# Memory management for context
@dataclass
class ContextMemory:
    """
    Simple memory structure for agents.
    
    Stores conversation history and state. Immutable operations.
    """
    messages: list = field(default_factory=list)
    state: ContextData = field(default_factory=dict)
    
    def add_message(self, role: str, content: str) -> 'ContextMemory':
        """Add message and return new memory instance."""
        new_messages = self.messages + [{'role': role, 'content': content}]
        return ContextMemory(messages=new_messages, state=self.state)
    
    def update_state(self, **updates: Any) -> 'ContextMemory':
        """Update state and return new memory instance."""
        new_state = {**self.state, **updates}
        return ContextMemory(messages=self.messages, state=new_state)
    
    def get_recent_messages(self, limit: int = 10) -> list:
        """Get recent messages up to limit."""
        return self.messages[-limit:] if self.messages else []