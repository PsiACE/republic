# Republic Prompt

A modern, elegant, and extensible Python prompt engineering toolkit.

`republic-prompt` aims to simplify the process of creating, managing, and rendering prompts, allowing you to focus on building great AI functionality rather than dealing with tedious string concatenation.

## Core Principles

- **Simplicity First**: Provide a clean, intuitive API. You can do most of the work with just a few lines of code.
- **Convention over Configuration**: Intelligent defaults and directory structure mean you almost never need to configure anything.
- **Structure over Strings**: Treat prompts, snippets, and functions as first-class citizens rather than simple text.
- **Extensible by Nature**: Easily integrate custom Python functions, even functions from other languages like JavaScript.

## Installation

```bash
# Use uv (recommended)
uv pip install republic-prompt

# or use pip
pip install republic-prompt
```

## Quick Start

### Option 1: Simple Template Formatting (90% of users)

Just need to format template strings? Use the `format()` function - no setup required!

```python
from republic_prompt import format

# Basic variable substitution
result = format("Hello {{ name }}!", name="Alice")
print(result)  # "Hello Alice!"

# With custom functions
def upper(text):
    return text.upper()

result = format(
    "Hello {{ upper(name) }}!", 
    custom_functions={"upper": upper},
    name="Bob"
)
print(result)  # "Hello BOB!"

# With conditional logic
result = format(
    "{% if count > 1 %}{{ count }} items{% else %}1 item{% endif %}",
    count=3
)
print(result)  # "3 items"
```

### Option 2: Full Workspace (for complex projects)

Forget about complex setup. Use `quick_render` to render templates from anywhere in just one line of code.

```python
# 'my_prompts' can be any directory
# 'my_prompts/templates/greeting.md'
# ---
# message: "Hello from Republic Prompt!"
# ---
# {{ message }} - You are asking about {{ topic }}.

from republic_prompt import quick_render

result = quick_render("my_prompts", "greeting", topic="Python")
print(result.content)
# >> Hello from Republic Prompt! - You are asking about Python.
```

## Core Features

### 1. Elegant Workspace Structure

A workspace is just a directory. Follow simple conventions, and `republic-prompt` will automatically discover all content.

```
my_workspace/
├── prompts.toml          # [optional] workspace metadata
├── templates/            # your main prompt templates
│   └── agent_prompt.md
├── snippets/             # reusable text snippets
│   └── rules.md
└── functions/            # Python functions that can be called by templates
    └── text_utils.py
```

### 2. Powerful Templates

Templates use [Jinja2](https://jinja.palletsprojects.com/) syntax and support **TOML** (`+++`) or **YAML** (`---`) frontmatter to define metadata and default variables.

```markdown
<!-- templates/agent_prompt.md -->
---
# YAML Frontmatter
description: "A friendly and helpful AI agent."
agent_name: "Republic Assistant"
---
## System

You are **{{ agent_name }}**.

{% include 'rules' %}

Please format the following items into a list:
{{ format_list(items) }}
```

### 3. Reusable Code Snippets (Snippets)

Use `{% include 'snippet_name' %}` to inject reusable parts into any template.

```markdown
<!-- snippets/rules.md -->
Your core rules are:
1. Be helpful and harmless.
2. Provide accurate information.
```

### 4. Plug-and-Play Functions

Create Python files in the `functions/` directory, and `republic-prompt` will automatically load them, making them available in templates.

```python
# functions/text_utils.py
def format_list(items):
    """Takes a list and formats it as a Markdown list."""
    return "\n".join(f"- {item}" for item in items)
```

### 5. Structured Output

`republic-prompt` can parse templates with `## Role` headings into structured message lists, which is perfect for integration with LLM APIs like OpenAI.

```python
# my_workspace/templates/chat.md:
# ---
# ## System
# You are a helpful assistant.
# 
# ## User
# I need help with {{ topic }}.
# ---
from republic_prompt import load_workspace

workspace = load_workspace("my_workspace")
result = workspace.render("chat", topic="Python lists")

# The `messages` property will be automatically populated
messages = result.to_openai_format()
# [
#   {"role": "system", "content": "You are a helpful assistant."},
#   {"role": "user", "content": "I need help with Python lists."}
# ]
```

### 6. Custom Function Injection

In addition to automatic loading, you can also inject custom functions when loading a workspace.

```python
def summarize(text: str) -> str:
    return text[:10] + "..."

workspace = load_workspace(
    "my_workspace",
    custom_functions={"summarize": summarize}
)
```

### 7. Cross-Workspace Imports

Managing multiple related prompt collections? `republic-prompt` allows you to easily reference content from another workspace in your current workspace, enabling modularity and reuse.

You can achieve this in two ways:

**1. Programmatically (via `add_external_workspace`)**
```python
# ... (existing python code for programmatic attachment) ...
main_ws.add_external_workspace("shared", shared_ws)
result = main_ws.render("main")
```

**2. Declaratively (via `prompts.toml`)**

For a more permanent setup, define external workspaces directly in your `prompts.toml`:

```toml
# workspaces/main_project/prompts.toml
name = "main_project"

[external_workspaces]
shared = "../shared_assets" # Path is relative to this TOML file
```

When `main_project` is loaded, it will automatically discover and attach the `shared` workspace.

```python
# Now, loading the workspace is enough
from republic_prompt import load_workspace

main_ws = load_workspace("workspaces/main_project")

# It can find 'shared::common_header' automatically
# result = main_ws.render("main")
```
