#!/usr/bin/env python3
"""
Generate prompts from examples configuration.

This script reads the examples workspace configuration and generates
pre-built prompts for different environments and use cases.
"""

import sys
import shutil
from pathlib import Path
from typing import Dict, Any
import argparse

from republic_prompt import load_workspace, render


# Add src to path for imports
script_dir = Path(__file__).parent
src_path = script_dir.parent / "src"
sys.path.insert(0, str(src_path))


def clear_prompts_directory(prompts_dir: Path) -> None:
    """Clear existing prompts directory."""
    if prompts_dir.exists():
        print(f"Clearing existing prompts directory: {prompts_dir}")
        shutil.rmtree(prompts_dir)
    prompts_dir.mkdir(parents=True, exist_ok=True)


def generate_core_prompts(workspace, base_config: Dict[str, Any]) -> Dict[str, str]:
    """Generate the 3 core prompt variants."""

    variants = {}

    # 1. Full CLI System with functions (development environment)
    if "gemini_cli_system_prompt" in workspace.templates:
        template = workspace.templates["gemini_cli_system_prompt"]
        full_config = {
            **base_config,
            **workspace.config.environments.get("development", {}),
            "domain": "software_engineering",
            "agent_type": "cli_agent",
            "tone": "professional_comprehensive",
            "max_output_lines": 5,
            "debug_mode": True,
            "verbose_explanations": True,
            "use_tools": True,
            "explain_critical_commands": True,
        }

        try:
            prompt = render(template, full_config, workspace)
            variants["full_cli_system"] = prompt.content
            print(
                "Generated: full_cli_system.md (comprehensive CLI system with functions)"
            )
        except Exception as e:
            print(f"Error generating full CLI system: {e}")

    # 2. Basic CLI System (production environment, minimal)
    if "gemini_cli_system_prompt" in workspace.templates:
        template = workspace.templates["gemini_cli_system_prompt"]
        basic_config = {
            **base_config,
            **workspace.config.environments.get("production", {}),
            "domain": "general_assistance",
            "agent_type": "basic_cli",
            "tone": "concise_direct",
            "max_output_lines": 3,
            "debug_mode": False,
            "verbose_explanations": False,
            "use_tools": True,
            "explain_critical_commands": True,
        }

        try:
            prompt = render(template, basic_config, workspace)
            variants["basic_cli_system"] = prompt.content
            print("Generated: basic_cli_system.md (basic CLI system)")
        except Exception as e:
            print(f"Error generating basic CLI system: {e}")

    # 3. Simple Agent (lightweight)
    if "simple_agent" in workspace.templates:
        template = workspace.templates["simple_agent"]
        simple_config = {
            **base_config,
            "domain": "general_assistance",
            "agent_type": "simple_assistant",
            "tone": "helpful_friendly",
            "max_output_lines": 3,
            "debug_mode": False,
            "verbose_explanations": False,
        }

        try:
            prompt = render(template, simple_config, workspace)
            variants["simple_agent"] = prompt.content
            print("Generated: simple_agent.md (lightweight simple agent)")
        except Exception as e:
            print(f"Error generating simple agent: {e}")

    return variants


def create_prompt_file(
    prompts_dir: Path, name: str, content: str, metadata: Dict[str, Any]
) -> None:
    """Create a prompt file with frontmatter."""
    file_path = prompts_dir / f"{name}.md"

    # Create frontmatter
    frontmatter_lines = ["---"]
    for key, value in metadata.items():
        if isinstance(value, str):
            frontmatter_lines.append(f'{key}: "{value}"')
        elif isinstance(value, dict):
            frontmatter_lines.append(f"{key}:")
            for sub_key, sub_value in value.items():
                frontmatter_lines.append(f"  {sub_key}: {sub_value}")
        else:
            frontmatter_lines.append(f"{key}: {value}")
    frontmatter_lines.append("---")
    frontmatter_lines.append("")

    # Write file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(frontmatter_lines))
        f.write(content)

    print(f"Generated: {file_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate prompts from examples configuration"
    )
    parser.add_argument(
        "--examples-dir", default="examples", help="Examples directory path"
    )
    parser.add_argument(
        "--clear", action="store_true", help="Clear existing prompts directory"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be generated without writing files",
    )

    args = parser.parse_args()

    # Determine paths
    script_dir = Path(__file__).parent
    examples_dir = script_dir.parent / args.examples_dir
    prompts_dir = examples_dir / "prompts"

    if not examples_dir.exists():
        print(f"Error: Examples directory not found: {examples_dir}")
        sys.exit(1)

    print(f"Loading workspace from: {examples_dir}")

    try:
        # Load the examples workspace
        workspace = load_workspace(str(examples_dir))
        print(f"Loaded workspace: {workspace.name}")
        print(f"Available templates: {list(workspace.templates.keys())}")
        print(f"Available snippets: {list(workspace.snippets.keys())}")
        print(f"Available functions: {list(workspace.functions.keys())}")

    except Exception as e:
        print(f"Error loading workspace: {e}")
        sys.exit(1)

    if args.dry_run:
        print("\n--- DRY RUN MODE ---")
    else:
        # Clear existing prompts if requested
        if args.clear:
            clear_prompts_directory(prompts_dir)

    # Get base configuration
    base_config = workspace.config.defaults.copy()

    # Generate the 3 core prompt variants
    print("\nGenerating core prompt variants...")

    if args.dry_run:
        # For dry run, just show what would be generated
        variants = generate_core_prompts(workspace, base_config)
        for variant_name, content in variants.items():
            print(f"Would generate: {variant_name}.md ({len(content)} chars)")
    else:
        variants = generate_core_prompts(workspace, base_config)

        # Create the files with appropriate metadata
        for variant_name, content in variants.items():
            if variant_name in ["full_cli_system", "basic_cli_system"]:
                source_template = "gemini_cli_system_prompt"
            else:
                source_template = "simple_agent"

            metadata = {
                "description": f"Core prompt variant: {variant_name}",
                "source_template": source_template,
                "generated_by": "generate_prompts.py",
                "variant": variant_name,
            }
            create_prompt_file(prompts_dir, variant_name, content, metadata)

    if not args.dry_run:
        print(f"\nPrompt generation complete. Files saved to: {prompts_dir}")
        print(f"Total files generated: {len(list(prompts_dir.glob('*.md')))}")
    else:
        print("\n--- DRY RUN COMPLETE ---")


if __name__ == "__main__":
    main()
