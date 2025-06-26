---
description: Simplified agent template for comparison with Google's complex version
snippets: core_mandates, tone_guidelines
var_domain: general_assistance
---

You are a helpful {{ domain }} agent.

{% include 'core_mandates' %}

{% include 'tone_guidelines' %}

{{ get_security_guidelines() }}

Ready to help! 