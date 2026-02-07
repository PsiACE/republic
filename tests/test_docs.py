from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest


def _python_blocks(text: str) -> list[str]:
    pattern = re.compile(r"```python\n(.*?)```", re.DOTALL)
    return [match.strip() for match in pattern.findall(text)]


def _should_skip(block: str) -> bool:
    for line in block.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        return stripped.startswith("# test:skip")
    return False


def _exec_block(block: str) -> None:
    env = dict(os.environ)
    env.setdefault("PYTHONPATH", str(Path.cwd()))
    subprocess.run([sys.executable, "-c", block], check=True, env=env)  # noqa: S603


@pytest.mark.parametrize("path", [Path("README.md"), *Path("docs").rglob("*.md")])
def test_docs_examples_run(path: Path, openrouter_api_key: str) -> None:
    if not path.exists():
        pytest.skip(f"Missing doc path: {path}")
    text = path.read_text(encoding="utf-8")
    blocks = _python_blocks(text)
    for block in blocks:
        if _should_skip(block):
            continue
        _exec_block(block)
