"""Simplified tests for republic_prompt loaders."""

import tempfile
import pytest
from pathlib import Path
from typing import Dict

from republic_prompt.loaders import (
    TomlFormatterLoader, YamlFormatterLoader, FormatterLoaderRegistry,
    ContentLoader, ConfigLoader, load_workspace_content,
    FunctionLoader, FunctionLoaderRegistry, PythonFunctionLoader
)
from republic_prompt.models import PromptWorkspaceConfig, FunctionModel
from republic_prompt.exceptions import LoaderError


class TestFormatterLoaders:
    """Test frontmatter format loaders."""

    def test_toml_formatter_loader(self):
        """Test TOML frontmatter parsing."""
        loader = TomlFormatterLoader()
        
        content = """+++
title = "Test"
version = "1.0"
+++

This is the content."""
        
        assert loader.can_handle(content)
        metadata, main_content = loader.parse(content)
        
        assert metadata["title"] == "Test"
        assert metadata["version"] == "1.0"
        assert "This is the content." in main_content

    def test_yaml_formatter_loader(self):
        """Test YAML frontmatter parsing."""
        try:
            import yaml
        except ImportError:
            pytest.skip("PyYAML not installed")
            
        loader = YamlFormatterLoader()
        
        content = """---
title: Test
version: 1.0
---

This is the content."""
        
        assert loader.can_handle(content)
        metadata, main_content = loader.parse(content)
        
        assert metadata["title"] == "Test"
        assert metadata["version"] == 1.0
        assert "This is the content." in main_content

    def test_formatter_registry(self):
        """Test formatter registry auto-detection."""
        registry = FormatterLoaderRegistry()
        registry.register("toml", TomlFormatterLoader())
        
        content = """+++
title = "Test"
+++

Content here."""
        
        metadata, main_content = registry.parse_frontmatter(content)
        assert metadata["title"] == "Test"
        assert "Content here." in main_content

    def test_no_frontmatter(self):
        """Test content without frontmatter."""
        registry = FormatterLoaderRegistry()
        registry.register("toml", TomlFormatterLoader())
        
        content = "Just plain content."
        metadata, main_content = registry.parse_frontmatter(content)
        
        assert metadata == {}
        assert main_content == "Just plain content."


class TestContentLoader:
    """Test content loading functionality."""

    def test_load_snippet(self):
        """Test loading a snippet."""
        with tempfile.TemporaryDirectory() as temp_dir:
            snippet_path = Path(temp_dir) / "test.md"
            snippet_path.write_text("""+++
description = "Test snippet"
+++

This is a test snippet.""")
            
            formatter_registry = FormatterLoaderRegistry()
            formatter_registry.register("toml", TomlFormatterLoader())
            
            loader = ContentLoader(formatter_registry)
            snippet = loader.load_snippet(snippet_path)
            
            assert snippet.name == "test"
            assert "This is a test snippet." in snippet.content
            assert snippet.metadata["description"] == "Test snippet"

    def test_load_template(self):
        """Test loading a template."""
        with tempfile.TemporaryDirectory() as temp_dir:
            template_path = Path(temp_dir) / "greeting.md"
            template_path.write_text("""+++
title = "Greeting Template"
+++

Hello {{ name }}!""")
            
            formatter_registry = FormatterLoaderRegistry()
            formatter_registry.register("toml", TomlFormatterLoader())
            
            loader = ContentLoader(formatter_registry)
            template = loader.load_template(template_path)
            
            assert template.name == "greeting"
            assert "Hello {{ name }}!" in template.content
            assert template.metadata["title"] == "Greeting Template"

    def test_load_missing_file(self):
        """Test loading non-existent file."""
        formatter_registry = FormatterLoaderRegistry()
        loader = ContentLoader(formatter_registry)
        
        with pytest.raises(LoaderError):
            loader.load_snippet(Path("/nonexistent/file.md"))


class TestConfigLoader:
    """Test configuration loading."""

    def test_load_toml_config(self):
        """Test loading TOML configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "prompts.toml"
            config_path.write_text("""
[prompts]
name = "test-workspace"
version = "1.0.0"
description = "Test workspace"
""")
            
            loader = ConfigLoader()
            config = loader.load_config(Path(temp_dir))
            
            assert config.name == "test-workspace"
            assert config.version == "1.0.0" 
            assert config.description == "Test workspace"

    def test_load_missing_config(self):
        """Test loading from directory without config."""
        with tempfile.TemporaryDirectory() as temp_dir:
            loader = ConfigLoader()
            
            # Should create default config
            config = loader.load_config(Path(temp_dir))
            assert config.version == "1.0.0"  # Default version

    def test_invalid_config(self):
        """Test handling invalid config."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "prompts.toml"
            config_path.write_text("invalid toml content [[[")
            
            loader = ConfigLoader()
            
            with pytest.raises(LoaderError):
                loader.load_config(Path(temp_dir))


class TestWorkspaceLoading:
    """Test complete workspace loading."""

    def test_load_workspace_content(self):
        """Test loading complete workspace content."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_path = Path(temp_dir)
            
            # Create config
            config = PromptWorkspaceConfig(
                name="test-workspace",
                version="1.0.0"
            )
            
            # Create directories and files
            templates_dir = workspace_path / "templates"
            templates_dir.mkdir()
            (templates_dir / "hello.md").write_text("Hello {{ name }}!")
            
            snippets_dir = workspace_path / "snippets"
            snippets_dir.mkdir()
            (snippets_dir / "greeting.md").write_text("Nice to meet you!")
            
            functions_dir = workspace_path / "functions"
            functions_dir.mkdir()
            (functions_dir / "utils.py").write_text("""
def format_name(name):
    return name.title()
""")
            
            # Load workspace content
            snippets, templates, functions = load_workspace_content(workspace_path, config)
            
            assert "hello" in templates
            assert "greeting" in snippets
            assert "format_name" in functions
            
            # Test template content
            assert "Hello {{ name }}!" in templates["hello"].content
            
            # Test snippet content
            assert "Nice to meet you!" in snippets["greeting"].content
            
            # Test function
            assert callable(functions["format_name"].callable)
            result = functions["format_name"].callable("alice")
            assert result == "Alice"

    def test_load_empty_workspace(self):
        """Test loading workspace with no content."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_path = Path(temp_dir)
            config = PromptWorkspaceConfig(name="empty-workspace")
            
            snippets, templates, functions = load_workspace_content(workspace_path, config)
            
            assert len(snippets) == 0
            assert len(templates) == 0
            assert len(functions) == 0


class TestCustomFunctionLoader:
    """Test custom function loader functionality."""

    def test_javascript_function_loader(self):
        """Test implementing a JavaScript function loader that actually executes JS code."""
        import subprocess
        import shutil
        
        # Skip test if Node.js is not available
        if not shutil.which("node"):
            pytest.skip("Node.js not found, skipping JavaScript function loader test")
        
        class JavaScriptFunctionLoader(FunctionLoader):
            """Custom loader for JavaScript functions that executes real JS code."""
            
            def can_handle(self, path: Path) -> bool:
                """Check if this loader can handle JavaScript files."""
                return path.suffix == '.js' and path.exists()
            
            def load_functions(self, path: Path) -> Dict[str, FunctionModel]:
                """Load functions from JavaScript file."""
                try:
                    content = path.read_text(encoding='utf-8')
                    functions = {}
                    
                    # Parse function declarations with parameters
                    import re
                    
                    # Match function declarations: function name(params) { ... }
                    pattern = r'function\s+(\w+)\s*\(([^)]*)\)\s*\{[^}]*\}'
                    matches = re.findall(pattern, content)
                    
                    for func_name, params in matches:
                        # Create a Python function that executes the JavaScript
                        def create_js_executor(name, js_path, param_list):
                            def js_executor(*args):
                                try:
                                    # Create a temporary script to call the JS function
                                    call_script = f"""
const fs = require('fs');
eval(fs.readFileSync('{js_path}', 'utf8'));

const args = {list(args)};
const result = {name}(...args);
console.log(JSON.stringify(result));
"""
                                    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as temp_file:
                                        temp_file.write(call_script)
                                        temp_file.flush()
                                        
                                        # Execute JavaScript with Node.js
                                        result = subprocess.run(
                                            ['node', temp_file.name],
                                            capture_output=True,
                                            text=True,
                                            check=True
                                        )
                                        
                                        # Clean up temporary file
                                        Path(temp_file.name).unlink()
                                        
                                        # Parse and return result
                                        import json
                                        return json.loads(result.stdout.strip())
                                        
                                except Exception as e:
                                    raise LoaderError(f"Failed to execute JavaScript function {name}: {e}")
                            
                            return js_executor
                        
                        functions[func_name] = FunctionModel(
                            name=func_name,
                            callable=create_js_executor(func_name, path, params),
                            signature=f"{func_name}({params})",
                            docstring=f"JavaScript function: {func_name}",
                            module=f"js:{path.name}"
                        )
                    
                    return functions
                    
                except Exception as e:
                    raise LoaderError(f"Failed to load JavaScript functions: {e}")
        
        # Test the JavaScript loader with real JS execution
        with tempfile.TemporaryDirectory() as temp_dir:
            js_file = Path(temp_dir) / "utils.js"
            js_file.write_text("""
function formatText(text) {
    return text.toUpperCase();
}

function addNumbers(a, b) {
    return a + b;
}

function createGreeting(name) {
    return `Hello, ${name}!`;
}

function multiplyNumbers(x, y) {
    return x * y;
}

// This is not a function declaration, should be ignored
const arrow = () => {};
""")
            
            loader = JavaScriptFunctionLoader()
            assert loader.can_handle(js_file)
            
            functions = loader.load_functions(js_file)
            
            # Check loaded functions
            assert "formatText" in functions
            assert "addNumbers" in functions
            assert "createGreeting" in functions
            assert "multiplyNumbers" in functions
            assert "arrow" not in functions  # Arrow functions not parsed
            
            # Test actual JavaScript execution
            format_func = functions["formatText"].callable
            result = format_func("hello")
            assert result == "HELLO"  # Real JavaScript toUpperCase()
            
            add_func = functions["addNumbers"].callable
            result = add_func(2, 3)
            assert result == 5  # Real JavaScript addition
            
            greeting_func = functions["createGreeting"].callable
            result = greeting_func("World")
            assert result == "Hello, World!"  # Real JavaScript template literal
            
            multiply_func = functions["multiplyNumbers"].callable
            result = multiply_func(4, 5)
            assert result == 20  # Real JavaScript multiplication
            
            # Check metadata
            assert functions["formatText"].docstring == "JavaScript function: formatText"
            assert functions["formatText"].signature == "formatText(text)"
            assert functions["addNumbers"].signature == "addNumbers(a, b)"

    def test_function_loader_registry_with_js(self):
        """Test function loader registry with JavaScript loader."""
        import subprocess
        import shutil
        
        # Skip test if Node.js is not available
        if not shutil.which("node"):
            pytest.skip("Node.js not found, skipping JavaScript function loader registry test")
        
        class JavaScriptFunctionLoader(FunctionLoader):
            """Real JS loader for registry testing."""
            
            def can_handle(self, path: Path) -> bool:
                if path.is_file():
                    return path.suffix == '.js'
                elif path.is_dir():
                    # Check if directory contains any .js files
                    return any(f.suffix == '.js' for f in path.glob('*.js'))
                return False
            
            def load_functions(self, path: Path) -> Dict[str, FunctionModel]:
                if path.is_file() and path.suffix == '.js':
                    # Parse actual JavaScript functions
                    content = path.read_text(encoding='utf-8')
                    functions = {}
                    
                    import re
                    pattern = r'function\s+(\w+)\s*\(([^)]*)\)\s*\{[^}]*\}'
                    matches = re.findall(pattern, content)
                    
                    for func_name, params in matches:
                        def create_js_executor(name, js_path):
                            def js_executor(*args):
                                try:
                                    call_script = f"""
const fs = require('fs');
eval(fs.readFileSync('{js_path}', 'utf8'));

const args = {list(args)};
const result = {name}(...args);
console.log(JSON.stringify(result));
"""
                                    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as temp_file:
                                        temp_file.write(call_script)
                                        temp_file.flush()
                                        
                                        result = subprocess.run(
                                            ['node', temp_file.name],
                                            capture_output=True,
                                            text=True,
                                            check=True
                                        )
                                        
                                        Path(temp_file.name).unlink()
                                        
                                        import json
                                        return json.loads(result.stdout.strip())
                                        
                                except Exception as e:
                                    raise LoaderError(f"Failed to execute JavaScript function {name}: {e}")
                            
                            return js_executor
                        
                        functions[func_name] = FunctionModel(
                            name=func_name,
                            callable=create_js_executor(func_name, path),
                            signature=f"{func_name}({params})",
                            docstring=f"JavaScript function: {func_name}"
                        )
                    
                    return functions
                    
                elif path.is_dir():
                    # Handle directory by checking for .js files
                    functions = {}
                    for js_file in path.glob('*.js'):
                        functions.update(self.load_functions(js_file))
                    return functions
                return {}
        
        # Test registry with both Python and JavaScript loaders
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            js_file = Path(temp_dir) / "script.js"
            js_file.write_text("""
function processText(text) { 
    return text.toUpperCase() + "!"; 
}

function calculateSum(a, b) {
    return a + b;
}
""")
            
            py_file = Path(temp_dir) / "utils.py"
            py_file.write_text("""
def python_func():
    return "python"
""")
            
            # Create registry and register loaders
            registry = FunctionLoaderRegistry()
            registry.register("python", PythonFunctionLoader())
            registry.register("javascript", JavaScriptFunctionLoader())
            
            # Load from directory
            all_functions = registry.load_all_functions(Path(temp_dir))
            
            # Should have functions from both loaders
            assert "processText" in all_functions  # From JavaScriptFunctionLoader
            assert "calculateSum" in all_functions  # From JavaScriptFunctionLoader
            assert "python_func" in all_functions  # From PythonFunctionLoader
            
            # Test JavaScript function execution
            js_func = all_functions["processText"].callable
            assert js_func("hello") == "HELLO!"  # Real JavaScript execution
            
            calc_func = all_functions["calculateSum"].callable
            assert calc_func(10, 20) == 30  # Real JavaScript execution
            
            # Test Python function execution
            py_func = all_functions["python_func"].callable
            assert py_func() == "python" 