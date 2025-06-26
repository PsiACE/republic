# Gemini CLI System Prompt with Republic Prompt

This example demonstrates how Google's complex system prompt (from their CLI agent) can be refactored and managed using Republic Prompt's multi-file architecture.

## The Challenge

Gemini CLI's original system prompt is a monolithic JavaScript function with:
- Environment detection mixed with prompt content
- Hard-coded tool names and workflows
- Difficult to maintain and customize

## Our Solution

We've decomposed Google's complex prompt into a maintainable, scalable architecture:

### File Organization

### Before (Monolithic)

- Single JavaScript function with embedded logic
- Hardcoded environment detection (sandbox, git repository, etc.)
- Complex conditional workflow generation
- Difficult to test, modify, and customize
- Mixed concerns: environment detection, tool definitions, workflows, examples

### After (Republic Prompt)

```
examples/
├── prompts.toml                    # Environment configuration
├── functions/                      # Modular business logic (Python)
│   ├── __init__.py                # Function exports
│   ├── environment.py             # Environment & sandbox detection
│   ├── tools.py                   # Tool usage & safety guidelines  
│   └── workflows.py               # Software engineering workflows
├── snippets/                      # Reusable prompt components
│   ├── core_mandates.md          # Core behavior rules
│   ├── tone_guidelines.md        # CLI communication style
│   ├── environment_detection.md  # Dynamic environment warnings
│   └── examples.md               # Interaction examples
├── templates/                     # Dynamic templates
│   ├── gemini_cli_system_prompt.md  # Main system prompt template
│   └── simple_agent.md             # Simplified agent template
└── prompts/                       # Pre-built specialized prompts
    ├── full_cli_system.md         # Comprehensive CLI system with all functions
    ├── basic_cli_system.md        # Production-ready CLI system (minimal)
    └── simple_agent.md            # Lightweight general-purpose assistant
```

### Key Refactoring Achievements

**Original Complexity Broken Down:**

- **Environment Detection** (100+ lines JS) → `environment.py` (266 lines with comprehensive detection)
  - macOS Seatbelt/App Sandbox detection
  - Linux container/Docker detection  
  - Git repository status and workflow integration
  - Dynamic warning message generation

- **Tool Safety Logic** (50+ lines JS) → `tools.py` (175 lines with enhanced safety)
  - Command danger assessment and explanation generation
  - Background process detection
  - Interactive command conversion
  - Parallel execution recommendations

- **Workflow Management** (150+ lines JS) → `workflows.py` (142 lines structured workflows)
  - Software engineering task workflows
  - New application development processes
  - Verification and testing procedures
  - Tone and interaction guidelines

- **Template Composition** (200+ lines JS) → Modular snippets + dynamic templates
  - `core_mandates.md` - Core behavior rules
  - `tone_guidelines.md` - CLI interaction style
  - `environment_detection.md` - Dynamic environment warnings
  - `examples.md` - Interaction examples
