---
description: Command safety examples and guidelines
---

## Command Safety Examples

When executing potentially dangerous commands, always explain their impact:

{% for example in get_dangerous_command_examples() %}
**Example**: For `{{ example.command }}` - {{ example.explanation }}
{% endfor %}

Commands that should run in background:

{% for example in get_background_command_examples() %}
**Background Process**: `{{ example.command }}` - {{ example.explanation }}
{% endfor %}

**Safety Guidelines**:
- Always explain destructive commands before execution
- Use background processes for long-running services
- Verify file paths and permissions before proceeding 