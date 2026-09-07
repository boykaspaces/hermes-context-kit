# Repository AI Instructions

- Start with `PROJECT.md` and follow the narrowest current pointer.
- Read `.context-kit/manifest.json` before changing adopted project context.
- Source and configuration own implementation truth.
- Task files own work status; ADRs own durable decisions; indexes own
  navigation only.
- Treat the accepted integration ref as canonical. A pull-request branch is a
  candidate next state until merged.
- Never infer current state from timestamps, filename ordering, branch names,
  or conversation recency.
- Update affected indexes whenever a path, status, or pointer changes.
- Never commit credentials, local runtime data, or environment overrides.
