---
description: Dynamic environment detection and warnings - equivalent to Google's environment detection
---

{% set sandbox_status = get_sandbox_status() %}
{% if sandbox_status == "macos_seatbelt" %}
# MacOS Seatbelt

{{ get_sandbox_warning_message() }}
{% elif sandbox_status == "generic_sandbox" %}
# Sandbox

{{ get_sandbox_warning_message() }}
{% else %}
# Outside of Sandbox

{{ get_sandbox_warning_message() }}
{% endif %}

{% if is_git_repository() %}
# Git Repository

{{ get_git_workflow_instructions() }}
{% endif %} 