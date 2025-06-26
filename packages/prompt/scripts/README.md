# Prompt Generation Scripts

This directory contains utility scripts for managing and generating prompts from the examples workspace.

## generate_prompts.py

A script that generates pre-built prompts from the examples workspace configuration, templates, and snippets.

### Purpose

This script automates the generation of specialized prompt variants by:

1. Loading the examples workspace configuration
2. Rendering templates with different environment and use-case specific variables
3. Generating pre-built prompts that are ready to use without further rendering
4. Replacing the manually maintained prompts with automatically generated ones

### Usage

```bash
# Basic usage - generate prompts from examples
python scripts/generate_prompts.py

# Clear existing prompts directory and regenerate
python scripts/generate_prompts.py --clear

# Dry run to see what would be generated
python scripts/generate_prompts.py --dry-run

# Use custom examples directory
python scripts/generate_prompts.py --examples-dir path/to/examples
```

### Generated Prompts

The script generates exactly 3 core prompt variants:

#### 1. Full CLI System (`full_cli_system.md`)
- **Purpose**: Comprehensive CLI agent with all functions and features
- **Based on**: `gemini_cli_system_prompt` template with development environment
- **Features**: Debug mode, verbose explanations, full tool access, comprehensive workflows
- **Use case**: Development, complex tasks, full-featured AI assistant

#### 2. Basic CLI System (`basic_cli_system.md`) 
- **Purpose**: Production-ready CLI agent with essential features
- **Based on**: `gemini_cli_system_prompt` template with production environment
- **Features**: Concise output, essential tools, streamlined workflows
- **Use case**: Production environments, general assistance, minimal footprint

#### 3. Simple Agent (`simple_agent.md`)
- **Purpose**: Lightweight general-purpose assistant
- **Based on**: `simple_agent` template
- **Features**: Basic functionality, friendly tone, minimal complexity
- **Use case**: Simple tasks, quick help, resource-constrained environments

### Configuration

The script reads configuration from:
- `examples/prompts.toml` - Workspace configuration with environments and defaults
- `examples/templates/` - Template files to render
- `examples/snippets/` - Reusable prompt components
- `examples/functions/` - Python functions for dynamic content

### Generated File Structure

Each generated prompt includes:
- Frontmatter with metadata (source template, generation info, variant type)
- Fully rendered content with all variables resolved
- Environment-specific behavior and configuration

### Benefits

- **Consistency**: All prompts follow the same structure and conventions
- **Maintainability**: Update templates/snippets to update all generated prompts
- **Customization**: Easy to add new variants or environments
- **Automation**: No manual maintenance of individual prompt files
- **Traceability**: Clear metadata about how each prompt was generated

### Development Workflow

1. Modify templates, snippets, or configuration in `examples/`
2. Run `python scripts/generate_prompts.py --clear` to regenerate all prompts
3. Test the generated prompts
4. Commit both the source changes and generated prompts

### Error Handling

The script includes error handling for:
- Missing templates or workspace files
- Template rendering errors
- File system issues
- Invalid configurations

Errors are reported with context to help debugging. 