"""Workflow functions - equivalent to Google's primary workflows."""

from typing import List, Dict


def get_software_engineering_workflow() -> str:
    """
    Get the software engineering workflow steps.
    Based on Google's Software Engineering Tasks workflow.
    """
    return """
## Software Engineering Workflow

When performing tasks like fixing bugs, adding features, refactoring, or explaining code:

1. **Understand:** Think about the user's request and relevant codebase context. Use GrepTool and GlobTool extensively (in parallel if independent) to understand file structures, existing code patterns, and conventions. Use ReadFileTool and ReadManyFilesTool to understand context and validate assumptions.

2. **Plan:** Build a coherent and grounded plan based on step 1. Share an extremely concise yet clear plan with the user if it would help them understand your thought process. Include self-verification loop by writing unit tests if relevant.

3. **Implement:** Use available tools (EditTool, WriteFileTool, ShellTool) to act on the plan, strictly adhering to project's established conventions.

4. **Verify (Tests):** If applicable and feasible, verify changes using the project's testing procedures. Identify correct test commands by examining README files, build/package configuration.

5. **Verify (Standards):** After making code changes, execute project-specific build, linting and type-checking commands to ensure code quality and adherence to standards.
""".strip()


def get_new_application_workflow() -> str:
    """
    Get the new application development workflow.
    Based on Google's New Applications workflow.
    """
    return """
## New Application Workflow

**Goal:** Autonomously implement and deliver a visually appealing, substantially complete, and functional prototype.

1. **Understand Requirements:** Analyze user's request to identify core features, desired UX, visual aesthetic, application type/platform, and explicit constraints.

2. **Propose Plan:** Formulate internal development plan. Present clear, concise, high-level summary covering application type, key technologies, main features, user interaction, and visual design approach.

3. **User Approval:** Obtain user approval for the proposed plan.

4. **Implementation:** Autonomously implement each feature per approved plan. Scaffold application using ShellTool. Create necessary placeholder assets for visual coherence.

5. **Verify:** Review work against original request and approved plan. Fix bugs, deviations, and placeholders where feasible.

6. **Solicit Feedback:** Provide instructions on starting the application and request user feedback.
""".strip()


def should_use_parallel_tools(task_type: str) -> bool:
    """
    Determine if parallel tool execution is recommended.
    Based on Google's parallelism guidelines.
    """
    parallel_task_types = [
        "search",
        "analyze",
        "understand",
        "explore",
        "read_multiple",
        "grep_multiple",
        "find_files",
    ]
    return task_type.lower() in parallel_task_types


def get_verification_commands(project_type: str) -> List[str]:
    """
    Get appropriate verification commands based on project type.
    Following Google's verification workflow.
    """
    commands_map = {
        "javascript": ["npm test", "npm run lint", "npm run build"],
        "typescript": ["npm test", "npm run lint", "tsc --noEmit", "npm run build"],
        "python": ["pytest", "ruff check .", "mypy .", "python -m build"],
        "rust": ["cargo test", "cargo clippy", "cargo build"],
        "go": ["go test ./...", "go vet ./...", "go build ./..."],
        "java": ["mvn test", "mvn compile", "mvn verify"],
        "general": ["make test", "make lint", "make build"],
    }

    return commands_map.get(project_type.lower(), commands_map["general"])


def format_concise_plan(steps: List[str]) -> str:
    """
    Format a plan in Google's concise style.
    Following the "extremely concise yet clear" guideline.
    """
    if len(steps) <= 3:
        return "\n".join(f"{i + 1}. {step}" for i, step in enumerate(steps))
    else:
        # For longer plans, group related steps
        return f"Plan: {' → '.join(steps[:3])}{'...' if len(steps) > 3 else ''}"


def get_tone_guidelines() -> Dict[str, str]:
    """
    Get tone and style guidelines.
    Based on Google's "Tone and Style (CLI Interaction)" section.
    """
    return {
        "concise_direct": "Professional, direct, and concise tone suitable for CLI environment",
        "minimal_output": "Aim for fewer than 3 lines of text output per response when practical",
        "clarity_over_brevity": "Prioritize clarity for essential explanations when needed",
        "no_chitchat": "Avoid conversational filler, preambles, or postambles",
        "tools_vs_text": "Use tools for actions, text output only for communication",
        "github_markdown": "Use GitHub-flavored Markdown, responses rendered in monospace",
    }


def should_provide_explanation(task_type: str, environment: str) -> bool:
    """
    Determine if detailed explanations should be provided.
    Based on environment and task complexity.
    """
    if environment == "development":
        return True

    complex_tasks = ["refactor", "debug", "architecture", "security"]
    return any(task in task_type.lower() for task in complex_tasks)


def get_example_interactions() -> List[Dict[str, str]]:
    """
    Get example interactions demonstrating proper tone.
    Based on Google's examples section.
    """
    return [
        {"user": "1 + 2", "model": "3"},
        {"user": "is 13 a prime number?", "model": "true"},
        {"user": "list files here.", "model": "[tool_call: LSTool for path '.']"},
        {
            "user": "start the server implemented in server.js",
            "model": "[tool_call: ShellTool for 'node server.js &' because it must run in the background]",
        },
        {
            "user": "Delete the temp directory.",
            "model": "I can run `rm -rf ./temp`. This will permanently delete the directory and all its contents.",
        },
    ]


def format_workflow_reminder() -> str:
    """
    Format the final workflow reminder.
    Based on Google's "Final Reminder" section.
    """
    return """
Your core function is efficient and safe assistance. Balance extreme conciseness with the crucial need for clarity, especially regarding safety and potential system modifications. Always prioritize user control and project conventions. Never make assumptions on file contents; use ReadFileTool to verify. You are an agent - keep going until the user's query is completely resolved.
""".strip()
