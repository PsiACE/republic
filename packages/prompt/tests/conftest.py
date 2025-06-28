"""Pytest configuration for republic_prompt tests."""

import pytest
import tempfile
from pathlib import Path


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_path = Path(temp_dir)
        
        # Create basic workspace structure
        (workspace_path / "prompts.toml").write_text("""
[prompts]
name = "test-workspace"
version = "1.0.0"
function_loaders = ["python"]

[prompts.defaults]
project = "TestProject"
environment = "test"
""")
        
        # Create directories
        (workspace_path / "templates").mkdir()
        (workspace_path / "snippets").mkdir()
        (workspace_path / "functions").mkdir()
        
        # Create basic template
        (workspace_path / "templates" / "test_template.md").write_text("""
Hello {{ name }}! Welcome to {{ project }}.
""")
        
        # Create basic snippet
        (workspace_path / "snippets" / "test_snippet.md").write_text("""
This is a test snippet.
""")
        
        # Create basic function
        (workspace_path / "functions" / "test_functions.py").write_text("""
def test_function():
    '''A test function.'''
    return "test result"

WORKSPACE_FUNCTIONS = {
    "test_function": test_function,
}
""")
        
        yield workspace_path


@pytest.fixture
def sample_toml_content():
    """Sample TOML frontmatter content."""
    return """+++
title = "Test Template"
description = "A test template"
version = "1.0"

[features]
security = true
debug = false
+++

This is the template content with {{ variable }}.
"""


@pytest.fixture
def sample_yaml_content():
    """Sample YAML frontmatter content."""
    return """---
title: Test Template
description: A test template
version: 1.0
features:
  security: true
  debug: false
---

This is the template content with {{ variable }}.
"""


@pytest.fixture
def sample_functions():
    """Sample functions for testing."""
    def upper_case(text):
        """Convert text to uppercase."""
        return text.upper()
    
    def add_numbers(a, b):
        """Add two numbers."""
        return a + b
    
    return {
        "upper_case": upper_case,
        "add_numbers": add_numbers,
    } 