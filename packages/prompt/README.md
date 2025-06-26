# Republic Prompt

> A modern prompt engineering workspace library that makes complex AI system prompt management simple, maintainable, and extensible.

Republic Prompt streamlines prompt engineering through a **file-first architecture** and **clear separation of responsibilities**. Using a combination of TOML configuration, Jinja2 templating, and modular functions, it enables teams to build, maintain, and scale complex AI prompts efficiently.

## Design Philosophy

Republic Prompt is built on four core principles:

1. **File-First Architecture** - Use filesystem conventions instead of complex configuration
2. **Clear Separation** - Each component has a single, well-defined responsibility
3. **Environment-Aware** - Dynamic behavior based on deployment context
4. **Composable** - Build complex prompts from simple, reusable components

## Real-World Example

We provide a complete example refactoring Google's Gemini CLI system prompt into a maintainable modular architecture, check [examples/README.md](examples/README.md) for more details.

## Installation

```bash
pip install republic-prompt
```

## Quick Start

### Basic Usage

```python
from republic_prompt import load_workspace, render

# Load a prompt workspace
workspace = load_workspace("./my-prompts")

# Use pre-built prompts (ready to use)
debug_assistant = workspace.prompts["debugging_assistant"]
print(debug_assistant.content)

# Render dynamic templates with variables
template = workspace.templates["code_review"]
prompt = render(template, {
    "language": "python",
    "review_type": "security",
    "user_query": "Check this authentication function"
}, workspace)

print(prompt.content)
```

### Creating Your First Workspace

```bash
mkdir my-prompts && cd my-prompts
```

**1. Configure your workspace**

```toml
# prompts.toml
[prompts]
name = "my-ai-workspace"
function_loaders = ["python"]

[prompts.defaults]
tone = "professional"
max_output_lines = 3

[prompts.environments.development]
debug_mode = true
verbose = true

[prompts.environments.production]
debug_mode = false
verbose = false
```

**2. Create reusable snippets**

```markdown
<!-- snippets/greeting.md -->
---
description: Standard AI assistant greeting
var_name: Assistant
---
Hello! I'm {{ name }}, your AI assistant specialized in {{ domain }}.
```

**3. Build dynamic templates**

```markdown
<!-- templates/code_reviewer.md -->
---
description: Code review assistant template
snippets: greeting
var_language: python
var_review_type: general
---
{% include 'greeting' %}

I'll review your {{ language }} code focusing on {{ review_type }} aspects.

{% if debug_mode %}
**Debug mode enabled** - I'll provide detailed explanations.
{% endif %}

{% set topic = extract_topic(user_query) %}
{% if topic == "security" %}
## Security Review Checklist
{{ get_security_checklist(language) }}
{% endif %}

Please share your code for review.
```

**4. Add business logic functions**

```python
# functions/__init__.py
def extract_topic(query: str) -> str:
    """Extract the main topic from user query"""
    if "security" in query.lower() or "vulnerability" in query.lower():
        return "security"
    elif "performance" in query.lower():
        return "performance"
    return "general"

def get_security_checklist(language: str) -> str:
    """Get security checklist for specific language"""
    checklists = {
        "python": "- Check for SQL injection\n- Validate input sanitization",
        "javascript": "- Check for XSS vulnerabilities\n- Validate CSRF protection"
    }
    return checklists.get(language, "- Follow general security practices")

# Export functions for template use
WORKSPACE_FUNCTIONS = {
    'extract_topic': extract_topic,
    'get_security_checklist': get_security_checklist,
}
```

**5. Use your workspace**

```python
from republic_prompt import load_workspace, render

workspace = load_workspace(".")
template = workspace.templates["code_reviewer"]

# Render with environment configuration
env_config = workspace.get_environment_config("development")
variables = {
    **env_config,
    "name": "CodeReviewer",
    "domain": "software engineering",
    "language": "python",
    "review_type": "security",
    "user_query": "Please check for security vulnerabilities"
}

prompt = render(template, variables, workspace)
print(prompt.content)
```

## Core Architecture

### File-First Organization

Republic Prompt organizes prompts using a clear directory structure:

```
my-prompts/
├── prompts.toml           # Workspace configuration
├── snippets/              # Reusable prompt components
│   ├── greeting.md
│   └── instructions.md
├── templates/             # Dynamic templates (require rendering)
│   ├── code_reviewer.md
│   └── system_agent.md
├── prompts/               # Pre-built prompts (ready to use)
│   ├── python_reviewer.md
│   └── debug_assistant.md
└── functions/             # Business logic functions
    ├── __init__.py
    ├── environment.py
    └── tools.py
```

### Component Responsibilities

| Component | Purpose | Usage |
|-----------|---------|-------|
| **snippets/** | Reusable prompt fragments | Building blocks for complex prompts |
| **templates/** | Dynamic templates with variables | Parameterized, environment-aware prompts |
| **prompts/** | Ready-to-use complete prompts | Quick deployment, standard scenarios |
| **functions/** | Business logic and dynamic content | Environment detection, data fetching |

## Advanced Features

### Environment-Driven Configuration

```toml
[prompts.environments.development]
debug_mode = true
verbose_explanations = true
show_reasoning = true
max_output_lines = 5

[prompts.environments.production]
debug_mode = false
verbose_explanations = false
show_reasoning = false
max_output_lines = 2
```

```python
# Different behavior based on environment
dev_prompt = render(template, workspace.get_environment_config("development"), workspace)
prod_prompt = render(template, workspace.get_environment_config("production"), workspace)
```

### Template Composition

```jinja2
<!-- Compose from multiple snippets -->
{% include 'core_mandates' %}
{% include 'tone_guidelines' %}

<!-- Dynamic function calls -->
{% set topic = extract_topic(user_query) %}
{{ get_examples_for_topic(topic, count=3) }}

<!-- Environment-aware rendering -->
{% if debug_mode %}
**Debug Information:**
- Environment: {{ environment }}
- Variables: {{ template_variables }}
{% endif %}
```

### Message Format Support

```markdown
<!-- templates/conversation.md -->
---
output_format: messages
---
[SYSTEM]
You are a helpful AI assistant.

[USER]
{{ user_query }}

[ASSISTANT]
I'll help you with that.
```

```python
# Render to OpenAI-compatible message format
prompt = render(template, variables, workspace)
messages = prompt.to_openai_format()
# [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
```

### Function Loaders

Republic Prompt supports multiple programming languages for business logic:

```python
from republic_prompt import register_function_loader, FunctionLoader

@register_function_loader("javascript")
class JavaScriptFunctionLoader(FunctionLoader):
    language = "javascript"
    supported_extensions = [".js", ".mjs"]
    
    def load_functions(self, workspace_path: Path) -> Dict[str, Function]:
        # Custom JavaScript function loading logic
        pass
```

## Usage Patterns

### 1. Quick Use - Pre-built Prompts
```python
# Out of the box, no rendering needed
workspace = load_workspace("./examples")
prompt = workspace.prompts["debugging_assistant"]
print(prompt.content)  # Ready to use immediately
```

### 2. Customization - Dynamic Templates
```python
# Parameterized rendering for different scenarios
template = workspace.templates["system_agent"]
custom_prompt = render(template, {
    "domain": "data_science",
    "user_query": "Analyze this dataset",
    "debug_mode": True
}, workspace)
```

### 3. Development - Compose from Components
```python
# Build prompts from snippets and functions
from republic_prompt import quick_render

content = """
{% include 'greeting' %}
Current task: {{ get_current_task() }}
{% include 'instructions' %}
"""

prompt = quick_render(content, {"name": "DataAnalyst"}, workspace)
```

---

**Republic Prompt** - Making complex AI prompt management simple and elegant.