# File Map

Status: Current index

| Path | Owns | Read when |
|---|---|---|
| `README.md` | Repository entry and quick start | Entering the repository |
| `VERSION` | Candidate/released Context Kit implementation version | Packaging or upgrading the Kit |
| `PROJECT.md` | Stable repository identity and boundaries | Maintaining the project |
| `AGENTS.md` | AI editing and validation instructions | Before changing files |
| `.github/workflows/validate.yml` | GitHub-hosted canonical repository validation | Configuring or auditing required status checks |
| `.context-kit/index.md` | This repository's current-first maintenance router | Resuming repository maintenance |
| `tasks/` | Public repository-maintenance Task state | Reviewing or continuing protocol work |
| `docs/decisions/` | Durable Context Kit architecture decisions | Work depends on protocol architecture |
| `spec/` | Versioned portable protocol contracts | Changing observable artifact or state semantics |
| `schemas/` | Machine-readable adoption, lock, and System Task structures | Implementing or integrating validators |
| `profiles/` | Required logical artifacts and features for each adoption level | Bootstrapping or upgrading a project |
| `adapters/` | Runtime and workflow bindings, templates, and integration guidance | Integrating a specific agent or forge |
| `adapters/runtime/hermes/runtime-contract.json` | Fixed Hermes solution paths, capabilities, installation mechanisms, and optional SOUL policy | Discovering or validating Hermes runtime inputs |
| `adapters/runtime/hermes/scripts/runtime_setup.py` | Hermes configuration, immutable Skill installation plan, host setup, verification, and optional SOUL method | Adopting Context Kit in Hermes |
| `skills/README.md` | Skill routing index | Selecting a Skill |
| `skills/project-context-management/SKILL.md` | Project-context trigger, guards, and operation router | Performing or changing persistent context operations |
| `skills/project-context-management/references/` | Project lifecycle, indexes, Tasks, ADRs, Checkpoints, memory, consolidation, recovery, and protocol maintenance | Changing one routed project-context domain |
| `skills/multi-repo-system-management/SKILL.md` | Cross-repository trigger, guards, and operation router | Coordinating System and Component Tasks |
| `skills/multi-repo-system-management/references/` | Repository roles, delivery lifecycle, Handoffs, and validation | Changing one cross-repository domain |
| `skills/multi-repo-system-management/templates/` | Neutral System Task, Component Task, component lock, Handoff, and Checkpoint templates | Creating cross-repository artifacts |
| `skills/multi-repo-system-management/scripts/validate_multi_repo_context.py` | Offline repository/Handoff/System Task validator | Checking protocol consistency |
| `skills/multi-repo-system-management/tests/` | Validator happy/failure path tests | Changing validation behavior |
| `skills/skill-authoring/SKILL.md` | Skill-authoring trigger and operation router | Creating or changing reusable Skills |
| `skills/skill-authoring/references/` | Skill architecture, validation, and maintenance | Changing one routed authoring domain |
| `templates/project-context/` | Neutral v2 project skeleton | Bootstrapping a project |
| `docs/ADOPTION.md` | Installation and runtime verification | Adopting the kit |
| `docs/ARCHITECTURE.md` | Ownership and retrieval model | Understanding the design |
| `docs/SECURITY.md` | Trust and publication boundaries | Reviewing risk |
| `scripts/validate.sh` | Static repository checks | Validating changes |
| `scripts/context_kit.py` | Deterministic init, validate, doctor, and migration audit CLI | Starting or adopting a project |
| `tests/` | Clean-room bootstrap, profile, safety, and migration tests | Changing lifecycle tooling |
