# Tape

Tape is an append-only log of a run. It records system prompts, messages, tool calls, tool results, errors, and run metadata. Because every entry is recorded, you can audit and replay with confidence.

## What Tape Stores

- System prompts
- User and assistant messages
- Tool calls and tool results
- Errors and run metadata

## Anchors

Anchors mark boundaries in the tape. Use them to slice context for follow-up prompts or to group related work.

## Design Invariants

- Entries are appended in order and never rewritten.
- Context selection depends on order, not on ID values.
- Errors are first-class entries, not side channels.
