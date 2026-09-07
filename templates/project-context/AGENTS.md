# Repository AI Instructions

- Start with `PROJECT.md` and follow the narrowest current pointer.
- Read `.hermes/context-kit.json` before changing adopted project context.
- Source and configuration own implementation truth.
- Task files own work status; ADRs own durable decisions; Checkpoints own
  resumable snapshots; indexes own navigation only.
- Never infer current state from timestamps, filename ordering, or conversation
  recency.
- Update affected indexes whenever a path, status, or pointer changes.
- Never commit credentials, local runtime data, or environment overrides.
