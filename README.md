# Republic

> The minimalistic AI stack for developers who value freedom and efficiency.

## Installation

```bash
pip install republic[all]
```

## Usage

```python
from republic.prompt import load_workspace, render

# Load a workspace from directory
workspace = load_workspace("path/to/workspace")

# Get a template and render it
template = workspace.templates["template_name"]
prompt = render(template, {"name": "John"}, workspace)

print(prompt.content)
```

## Features

| Feature  | Description                                                                                                                                       |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `prompt` | Prompt management with `republic-prompt`, check [republic-prompt](https://github.com/psiace/republic/tree/main/packages/prompt) for more details. |
