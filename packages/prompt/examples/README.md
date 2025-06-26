# Republic Prompt Examples (Gemini CLI System Prompt Variant)

This directory contains examples demonstrating the Republic Prompt system, which is a **variant** of Google's Gemini CLI system prompt architecture. While it maintains all the core functionality and design principles of the original, it has been refactored into a maintainable, modular structure with some enhancements.

## Architecture Overview

This is **not a 1:1 replication** of Google's monolithic system prompt, but rather a modernized variant that:

- **Preserves all core functionality** from the original Google Gemini CLI prompt
- **Maintains equivalent behavior** for tool usage, safety rules, and environment detection
- **Includes all major feature points** such as command safety, background processes, and context awareness
- **Refactored into modular components** for better maintainability and testing
- **Enhanced with configurable environments** (development, production, simple)
- **Improved template system** with conditional rendering and variable substitution

## Key Differences from Original

1. **Modular Architecture**: Split monolithic prompt into reusable components
2. **Configuration-Driven**: Environment-specific settings via `prompts.toml`
3. **Template System**: Jinja2-based templates with conditional logic
4. **Enhanced Testing**: Comprehensive test coverage for all components
5. **Multiple Variants**: Three different prompt configurations for different use cases

## Directory Structure

```
examples/
├── functions/           # Python functions (equivalent to JS functions)
│   ├── environment.py   # Environment detection and OS utilities
│   ├── tools.py        # Tool usage and command safety functions  
│   └── workflows.py    # Workflow and process management
├── snippets/           # Reusable prompt components
│   ├── command_safety.md
│   ├── core_mandates.md
│   ├── environment_detection.md
│   └── tone_guidelines.md
├── templates/          # Base templates for prompt generation
│   ├── gemini_cli_system_prompt.md
│   └── simple_agent.md
├── prompts/           # Generated final prompts
│   ├── full_cli_system.md      # Development environment (115 lines)
│   ├── basic_cli_system.md     # Production environment (93 lines)
│   └── simple_agent.md         # Minimal agent (17 lines)
└── prompts.toml       # Configuration for all environments
```

## Core Functionality Preserved

All major functionality from Google's original system prompt is preserved:

### Tool Usage
- Complete tool enumeration (LSTool, EditTool, GrepTool, etc.)
- File path handling and parallelism guidelines
- Background process management
- Interactive command avoidance

### Security & Safety
- Command explanation requirements for dangerous operations
- Security best practices enforcement
- Sensitive information protection
- User confirmation respect

### Environment Detection
- Operating system detection and adaptation
- Git repository awareness with appropriate warnings
- Sandbox environment detection
- Context-aware behavior modification

### Command Safety
- Dangerous command pattern recognition
- Background process identification
- Automatic safety explanations
- User-friendly command guidance
