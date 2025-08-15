"""
Example implementations of the context system.

Demonstrates clean, practical usage patterns for context-aware agents.
Shows how to build real agents with the context framework.
"""

from typing import Any, List
from context import (
    AgentContext, ContextualAgent, ContextAware, ContextualMixin,
    ContextMemory, create_context, agent_context, get_current_context
)


class ChatAgent(ContextualAgent):
    """
    Simple chat agent that maintains conversation context.
    
    Shows basic contextual agent pattern - clean and focused.
    """
    
    def __init__(self, name: str):
        self.name = name
        self.memory = ContextMemory()
    
    def process(self, context: AgentContext) -> str:
        """Process chat message with context awareness."""
        user_message = context.get('message', '')
        
        # Update memory with user message
        self.memory = self.memory.add_message('user', user_message)
        
        # Simple response logic
        response = f"Hello from {self.name}! You said: {user_message}"
        
        # Add agent response to memory
        self.memory = self.memory.add_message('assistant', response)
        
        return response


class TaskAgent(ContextualAgent):
    """
    Task-oriented agent that tracks execution state.
    
    Demonstrates stateful agent with context-driven behavior.
    """
    
    def __init__(self):
        self.tasks_completed = 0
    
    def process(self, context: AgentContext) -> dict:
        """Execute task based on context."""
        task_type = context.get('task_type', 'unknown')
        task_data = context.get('task_data', {})
        
        # Simulate task processing
        result = {
            'agent_id': context.agent_id,
            'task_type': task_type,
            'status': 'completed',
            'data': task_data,
            'completed_at': context.timestamp,
            'total_completed': self.tasks_completed + 1
        }
        
        self.tasks_completed += 1
        return result


class AnalyticsCollector(ContextualMixin):
    """
    Analytics collector using mixin pattern.
    
    Shows how to add context awareness to existing classes.
    """
    
    def __init__(self):
        super().__init__()
        self.events: List[dict] = []
    
    def track_event(self, event_type: str, data: dict = None):
        """Track event with current context."""
        context = self.context
        
        event = {
            'type': event_type,
            'data': data or {},
            'timestamp': context.timestamp if context else None,
            'session_id': context.session_id if context else None,
            'agent_id': context.agent_id if context else None,
        }
        
        self.events.append(event)
        return event


# Protocol implementation example
class SimpleProcessor:
    """
    Simple processor implementing ContextAware protocol.
    
    Duck typing approach - no inheritance needed.
    """
    
    def execute(self, context: AgentContext) -> str:
        """Execute with context - implements ContextAware protocol."""
        return f"Processed by {context.agent_id} at {context.timestamp}"


def demonstrate_basic_usage():
    """Show basic context system usage."""
    print("=== Basic Context Usage ===")
    
    # Create context
    ctx = create_context(
        agent_id="demo_agent",
        user_id="user_123",
        message="Hello, world!",
        priority="high"
    )
    
    print(f"Created context: {ctx.agent_id} / {ctx.session_id}")
    print(f"Message: {ctx.get('message')}")
    print(f"Priority: {ctx.get('priority')}")
    
    # Use with chat agent
    chat_agent = ChatAgent("Demo Bot")
    response = chat_agent(ctx)
    print(f"Agent response: {response}")


def demonstrate_context_scoping():
    """Show context manager usage."""
    print("\n=== Context Scoping ===")
    
    ctx1 = create_context("agent_1", user_id="user_1")
    ctx2 = create_context("agent_2", user_id="user_2")
    
    # No context initially
    print(f"Current context: {get_current_context()}")
    
    with agent_context(ctx1):
        print(f"In ctx1 scope: {get_current_context().agent_id}")
        
        with agent_context(ctx2):
            print(f"In ctx2 scope: {get_current_context().agent_id}")
        
        print(f"Back to ctx1: {get_current_context().agent_id}")
    
    print(f"Outside scope: {get_current_context()}")


def demonstrate_mixin_pattern():
    """Show mixin pattern for context awareness."""
    print("\n=== Mixin Pattern ===")
    
    collector = AnalyticsCollector()
    ctx = create_context("analytics_agent", user_id="user_456")
    
    with collector.with_context(ctx):
        collector.track_event("page_view", {"page": "home"})
        collector.track_event("click", {"button": "submit"})
    
    print(f"Tracked {len(collector.events)} events")
    for event in collector.events:
        print(f"  {event['type']}: {event['session_id']}")


def demonstrate_task_processing():
    """Show task agent with context state."""
    print("\n=== Task Processing ===")
    
    task_agent = TaskAgent()
    
    # Process different tasks
    tasks = [
        {"task_type": "data_processing", "task_data": {"records": 100}},
        {"task_type": "email_send", "task_data": {"recipients": 5}},
        {"task_type": "report_generation", "task_data": {"format": "pdf"}}
    ]
    
    for i, task in enumerate(tasks):
        ctx = create_context(f"task_agent_{i}", **task)
        result = task_agent.process(ctx)
        print(f"Task {i+1}: {result['task_type']} -> {result['status']}")
    
    print(f"Total tasks completed: {task_agent.tasks_completed}")


def demonstrate_protocol_usage():
    """Show protocol-based context awareness."""
    print("\n=== Protocol Usage ===")
    
    processor = SimpleProcessor()
    ctx = create_context("protocol_demo")
    
    # Works with any ContextAware implementation
    def run_processor(proc: ContextAware, context: AgentContext):
        return proc.execute(context)
    
    result = run_processor(processor, ctx)
    print(f"Protocol result: {result}")


def demonstrate_memory_management():
    """Show context memory usage."""
    print("\n=== Memory Management ===")
    
    memory = ContextMemory()
    
    # Build conversation
    memory = memory.add_message("user", "What's the weather?")
    memory = memory.add_message("assistant", "It's sunny today!")
    memory = memory.add_message("user", "Great, should I go for a walk?")
    memory = memory.add_message("assistant", "Yes, it's perfect weather for walking!")
    
    # Update state
    memory = memory.update_state(
        weather="sunny",
        activity_recommendation="walking",
        user_mood="positive"
    )
    
    print(f"Conversation length: {len(memory.messages)}")
    print("Recent messages:")
    for msg in memory.get_recent_messages(2):
        print(f"  {msg['role']}: {msg['content']}")
    
    print(f"State: {memory.state}")


if __name__ == "__main__":
    """Run all demonstrations."""
    demonstrate_basic_usage()
    demonstrate_context_scoping()
    demonstrate_mixin_pattern()
    demonstrate_task_processing()
    demonstrate_protocol_usage()
    demonstrate_memory_management()
    
    print("\n=== All demonstrations completed! ===")