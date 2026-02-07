# Contributing

Thanks for investing time in Republic. Contributions are welcome and appreciated.

## Ways to Help

- Report bugs via GitHub Issues.
- Fix bugs or implement features labeled `help wanted`.
- Improve documentation or examples.

## Development Setup

1. Fork the repository and clone your fork.
2. Install dependencies and hooks:

```bash
uv sync
uv run pre-commit install
```

## Quality Checks

Run the full quality suite before opening a PR:

```bash
make check
make test
```

If you have multiple Python versions installed, you can also run:

```bash
tox
```

## Pull Request Guidelines

- Include tests for new functionality.
- Update documentation when public behavior changes.
- Keep changes focused and explain the motivation in your PR description.
