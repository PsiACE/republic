# Context

Context determines which tape entries are included when building prompts. The default context uses the most recent anchor and includes only message entries.

## Anchor Selection

- `LAST_ANCHOR` selects entries after the latest anchor.
- `None` selects the full tape.
- A named anchor selects entries after that anchor.

## Custom Selection

Provide a custom `select` function when you need to filter or reshape entries. This is useful when you want to exclude tool results or inject metadata into the prompt.

## Design Invariants

- Context selection should be deterministic.
- Changes in selection should be explicit, not accidental.
