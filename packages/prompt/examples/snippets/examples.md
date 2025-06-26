---
description: Example interactions demonstrating proper tone and workflow
---

# Examples (Illustrating Tone and Workflow)

{% for example in get_example_interactions() %}
**Example {{ loop.index }}:**
user: {{ example.user }}
model: {{ example.model }}

{% endfor %} 