#!/usr/bin/env python3
"""
Test and demonstration of the context system.

Shows that the implementation works and follows KISS principles.
Run this to verify everything is working correctly.
"""

from context import (
    AgentContext, ContextualAgent, create_context, agent_context,
    get_current_context, ContextMemory, ContextualMixin
)
from validation import (
    ContextValidator, ValidationRule, ContextValidationError,
    validate_context, create_chat_validator, create_typed_context,
    SchemaBuilder, safe_get_metadata
)
from examples import ChatAgent, TaskAgent, AnalyticsCollector


def test_basic_context():
    """Test basic context creation and usage."""
    print("Testing basic context...")
    
    ctx = create_context(
        agent_id="test_agent",
        user_id="user_123",
        message="Hello",
        priority=1
    )
    
    assert ctx.agent_id == "test_agent"
    assert ctx.user_id == "user_123"
    assert ctx.get("message") == "Hello"
    assert ctx.get("priority") == 1
    assert ctx.get("nonexistent") is None
    assert ctx.get("nonexistent", "default") == "default"
    
    # Test immutability
    new_ctx = ctx.with_metadata(extra="data")
    assert ctx.get("extra") is None  # Original unchanged
    assert new_ctx.get("extra") == "data"  # New context has data
    
    print("✓ Basic context tests passed")


def test_context_scoping():
    """Test context manager scoping."""
    print("Testing context scoping...")
    
    ctx1 = create_context("agent_1")
    ctx2 = create_context("agent_2")
    
    # No context initially
    assert get_current_context() is None
    
    with agent_context(ctx1):
        assert get_current_context().agent_id == "agent_1"
        
        with agent_context(ctx2):
            assert get_current_context().agent_id == "agent_2"
        
        # Back to ctx1
        assert get_current_context().agent_id == "agent_1"
    
    # No context after
    assert get_current_context() is None
    
    print("✓ Context scoping tests passed")


def test_contextual_agents():
    """Test contextual agent implementations."""
    print("Testing contextual agents...")
    
    # Test chat agent
    chat_agent = ChatAgent("TestBot")
    ctx = create_context("chat_test", message="Hello bot!")
    
    response = chat_agent.process(ctx)
    assert "Hello bot!" in response
    assert len(chat_agent.memory.messages) == 2  # User + assistant
    
    # Test callable interface
    response2 = chat_agent(ctx.with_metadata(message="Second message"))
    assert "Second message" in response2
    
    # Test task agent
    task_agent = TaskAgent()
    task_ctx = create_context(
        "task_test",
        task_type="data_processing",
        task_data={"records": 100}
    )
    
    result = task_agent.process(task_ctx)
    assert result["task_type"] == "data_processing"
    assert result["status"] == "completed"
    assert task_agent.tasks_completed == 1
    
    print("✓ Contextual agent tests passed")


def test_mixin_pattern():
    """Test contextual mixin pattern."""
    print("Testing mixin pattern...")
    
    collector = AnalyticsCollector()
    ctx = create_context("analytics_test", user_id="user_456")
    
    with collector.with_context(ctx):
        collector.track_event("page_view", {"page": "home"})
        collector.track_event("click", {"button": "submit"})
    
    assert len(collector.events) == 2
    assert collector.events[0]["session_id"] == ctx.session_id
    assert collector.events[1]["type"] == "click"
    
    print("✓ Mixin pattern tests passed")


def test_memory_management():
    """Test context memory functionality."""
    print("Testing memory management...")
    
    memory = ContextMemory()
    
    # Test immutable operations
    memory1 = memory.add_message("user", "Hello")
    memory2 = memory1.add_message("assistant", "Hi there!")
    memory3 = memory2.update_state(mood="friendly")
    
    # Original unchanged
    assert len(memory.messages) == 0
    assert len(memory.state) == 0
    
    # New instances have changes
    assert len(memory2.messages) == 2
    assert len(memory3.messages) == 2
    assert memory3.state["mood"] == "friendly"
    
    # Test recent messages
    recent = memory3.get_recent_messages(1)
    assert len(recent) == 1
    assert recent[0]["role"] == "assistant"
    
    print("✓ Memory management tests passed")


def test_validation():
    """Test validation system."""
    print("Testing validation...")
    
    # Test basic validator
    validator = ContextValidator()
    validator.require_field('agent_id')
    validator.validate_type('priority', int)
    
    # Valid context
    valid_ctx = create_context("test", priority=1)
    validator.validate_context(valid_ctx)  # Should not raise
    
    # Invalid context - missing required field
    try:
        # Create context with None agent_id (should fail validation)
        from datetime import datetime
        invalid_ctx = AgentContext(None, "session", None, datetime.utcnow(), {})
        validator.validate_context(invalid_ctx)
        assert False, "Should have raised validation error"
    except ContextValidationError:
        pass  # Expected
    
    # Test decorator
    @validate_context(create_chat_validator())
    def chat_function(self, context: AgentContext):
        return f"Processed: {context.get('message')}"
    
    class DummyAgent:
        process = chat_function
    
    agent = DummyAgent()
    chat_ctx = create_context("chat", message="Hello")
    result = agent.process(chat_ctx)
    assert "Hello" in result
    
    print("✓ Validation tests passed")


def test_schema_validation():
    """Test schema-based validation."""
    print("Testing schema validation...")
    
    # Build schema
    schema = (SchemaBuilder()
              .require('task_type', 'priority')
              .optional('description')
              .type_field('priority', int)
              .type_field('task_type', str)
              .build())
    
    # Valid context
    valid_ctx = create_context(
        "schema_test",
        task_type="process",
        priority=1,
        description="Test task"
    )
    schema.validate(valid_ctx)  # Should not raise
    
    # Invalid context - wrong type
    try:
        invalid_ctx = create_context(
            "schema_test",
            task_type="process",
            priority="high"  # Should be int
        )
        schema.validate(invalid_ctx)
        assert False, "Should have raised validation error"
    except ContextValidationError as e:
        assert "should be int" in str(e)
    
    print("✓ Schema validation tests passed")


def test_type_safety():
    """Test type safety utilities."""
    print("Testing type safety...")
    
    ctx = create_context("type_test", count=42, name="test")
    
    # Safe metadata access
    count = safe_get_metadata(ctx, "count", int)
    assert count == 42
    
    name = safe_get_metadata(ctx, "name", str)
    assert name == "test"
    
    # Type mismatch
    try:
        safe_get_metadata(ctx, "count", str)  # count is int, not str
        assert False, "Should have raised TypeError"
    except TypeError:
        pass  # Expected
    
    print("✓ Type safety tests passed")


def run_performance_test():
    """Simple performance test."""
    print("Running performance test...")
    
    import time
    
    # Test context creation performance
    start = time.time()
    for i in range(1000):
        ctx = create_context(f"perf_test_{i}", iteration=i)
    creation_time = time.time() - start
    
    # Test context scoping performance
    ctx = create_context("perf_scope")
    start = time.time()
    for i in range(1000):
        with agent_context(ctx):
            current = get_current_context()
            assert current.agent_id == "perf_scope"
    scoping_time = time.time() - start
    
    print(f"✓ Created 1000 contexts in {creation_time:.3f}s")
    print(f"✓ 1000 context scope operations in {scoping_time:.3f}s")


def demonstrate_real_usage():
    """Demonstrate real-world usage patterns."""
    print("\n=== Real-world Usage Demonstration ===")
    
    # Multi-agent conversation
    chat_agent = ChatAgent("Assistant")
    task_agent = TaskAgent()
    analytics = AnalyticsCollector()
    
    # User session
    session_ctx = create_context(
        "multi_agent_demo",
        user_id="demo_user",
        session_type="interactive"
    )
    
    with agent_context(session_ctx):
        # Chat interaction
        chat_ctx = session_ctx.with_metadata(message="Can you help me process some data?")
        chat_response = chat_agent(chat_ctx)
        print(f"Chat: {chat_response}")
        
        # Task processing
        task_ctx = session_ctx.with_metadata(
            task_type="data_processing",
            task_data={"records": 500, "format": "json"}
        )
        task_result = task_agent(task_ctx)
        print(f"Task result: {task_result['status']}")
        
        # Analytics tracking
        analytics.set_context(session_ctx)
        analytics.track_event("chat_interaction", {"response_length": len(chat_response)})
        analytics.track_event("task_completed", {"task_type": task_result["task_type"]})
        
        print(f"Analytics: Tracked {len(analytics.events)} events")
        
        # Show context propagation
        current = get_current_context()
        print(f"Current context: {current.agent_id} / {current.user_id}")


if __name__ == "__main__":
    """Run all tests."""
    print("🧪 Running Context System Tests\n")
    
    try:
        test_basic_context()
        test_context_scoping()
        test_contextual_agents()
        test_mixin_pattern()
        test_memory_management()
        test_validation()
        test_schema_validation()
        test_type_safety()
        run_performance_test()
        
        print("\n✅ All tests passed!")
        
        demonstrate_real_usage()
        
        print("\n🎉 Context system is working perfectly!")
        print("Clean, simple, and follows KISS principles.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)