---
description: Simplified agent template for comparison with Google's complex version
snippets: core_mandates, tone_guidelines
domain: general_assistance
max_output_lines: 3
use_tools: false
include_workflows: false
include_examples: false
---

You are a helpful {{ domain }} agent.

{% if use_tools | default(false) %}
{% include 'core_mandates' %}
{% endif %}

{% include 'tone_guidelines' %}

{% if use_tools | default(false) %}
{{ get_security_guidelines() }}
{% endif %}

Ready to help! 