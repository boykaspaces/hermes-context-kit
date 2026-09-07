# Conformance

Context Kit conformance tests observable contracts rather than exact prose.

## Release gates

- All JSON schemas and profile definitions parse.
- A fresh minimal, repository, and multi-repository project initializes and
  validates without network access or an agent-specific instruction file.
- Hermes and Codex adapter fixtures validate independently; selecting one does
  not change core Task or State semantics.
- Initialization dry-run performs no writes and normal initialization never
  overwrites different existing content.
- Previous-version fixtures produce deterministic migration reports.
- GitHub workflow guidance makes the final System proposal the activation
  boundary and does not require routine post-merge reconciliation.
- Project identity, active Task ownership, component revisions, evidence, and
  deployment applicability reject false claims.
- Repository-internal symlink escapes are rejected while platform-owned parent
  aliases do not invalidate a checkout.
- Linux, macOS, and Windows path behavior is covered by CI or focused platform
  tests before a release claims support.

## Consumer acceptance

Context Kit CI proves only the portable contract. Each consumer owns:

- its optional extensions;
- native build and test validation;
- deployment bindings and production evidence;
- the decision to advance its accepted Context Kit release.

Public consumers should run their acceptance against an immutable Kit release
or commit. A private consumer may provide anonymized structural fixtures back
to Context Kit without publishing private state.
