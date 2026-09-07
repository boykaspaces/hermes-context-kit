# Validation

## Validator

Use the deterministic helper:

```sh
python3 scripts/validate_multi_repo_context.py repository --root <repo>
python3 scripts/validate_multi_repo_context.py handoff --file <handoff.json>
python3 scripts/validate_multi_repo_context.py system-task \
  --root <integration-repo> \
  --task TASK-014 \
  --manifest tasks/system/TASK-014.json \
  --component-root component-a=../component-a \
  --verify-component-git \
  --lock components/lock.json
```

Paths are resolved from the current working directory. The validator performs
no network or deployment operation.

## Repository Check

The repository mode verifies:

- an explicit `Project ID:` exists;
- Task files have stable IDs and one of the five Task statuses;
- explicit Task types use `Component`, `System`, or `Deployment`;
- Component Tasks with a parent use canonical `<project-id>:TASK-NNN` form;
- `tasks/current.md` points only to an In Progress or Blocked Task;
- every Task file is routed from `tasks/README.md` with matching status;
- `.hermes/state.md`, when present, agrees with the current Task pointer.

Legacy Tasks may omit `Type`. Enrollment is explicit rather than a historical
bulk rewrite.

## System Task Check

The system-task mode detects schema v1 or v2 from the manifest. New System
Tasks use v2 and `components/lock.json`. Historical v1 Tasks retain
`components/lock.yaml` compatibility.

The mode additionally verifies:

- the Markdown Task is typed `System` or `Deployment`;
- the manifest is stored at `tasks/system/<TASK-ID>.json` and the Markdown
  Task's `System Manifest` field points to that canonical path; manifest
  storage must remain inside the repository and must not use symlinks;
- manifest identity matches the integration project's `Project ID:`;
- component identities and delivery states are unique and valid;
- each declared Component Task exists in the supplied component checkout,
  declares `Type: Component`, and points back to the same parent System Task;
- supplied component checkouts and Component Task paths must not use symlinks;
- when `--verify-component-git` is selected for v2 acceptance, every supplied
  checkout is clean and its Git HEAD exactly matches the manifest and lock;
- `handoff-ready` and later have full commit SHAs;
- a missing Component Task has an allowed reason; unchanged-component
  promotion resolves a different, explicitly completed prior
  System/Deployment Task in the same integration project and system whose
  structurally valid canonical manifest owns the same accepted component
  revision; prior state is explicit provenance and is not inferred from Task
  IDs, timestamps, or file modification times;
- v2 locked/verified acceptance has a full immutable revision equal to its
  canonical `components/lock.json` entry;
- a supplied lock is accepted only at the schema's canonical regular,
  non-symlinked integration-repository path;
- the lock contains exactly the manifest's component set, its repository URLs
  agree with the manifest, and it rejects malformed, incomplete, or duplicate
  core entries while allowing consumer-owned metadata;
- v2 verified integration has evidence and every component is at least locked;
- v2 deployed integration requires every deployment-required component to be
  deployed, plus deployment evidence and rollback; not-applicable components
  do not create false deployment claims.

Evidence and rollback values must be non-empty HTTP(S) URLs or
repository-relative file pointers. Non-string values and uncited prose do not
count as evidence. Repository-relative pointers must resolve to regular files
inside the integration repository without crossing a symlink. HTTP(S) pointers
and repository URLs are structurally validated and must not contain userinfo.

Completed schema v1 Tasks may retain their original non-empty narrative
evidence so a protocol upgrade does not rewrite history. This compatibility
rule also preserves their previously accepted combined delivery/integration
state relationship. It is validation-only: active v1 Tasks and all v2 Tasks
require stable pointers and current state invariants, and historical records
cannot advance a new state.

The low-level lock parser retains the historical `components` list YAML shape
shown in [`../templates/component-lock.yaml`](../templates/component-lock.yaml)
for schema v1 Tasks. A completed v1 Task may validate against its matching
`components/locks/TASK-NNN.yaml` snapshot after the rolling lock migrates to
v2. New schema v2 Tasks use the canonical
`components/lock.json` template, whose portable core is component name,
repository URL, and immutable revision. Consumers may add project-owned
metadata beside the core fields; their native validator owns those extensions.

## Acceptance Layers

Run checks in this order and stop at the first failed owner:

1. component repository validation;
2. Component Task and optional Handoff validation;
3. exact revision and component-lock verification;
4. cross-component integration validation;
5. deployment acceptance and negative tests, when deployment is in scope.

Passing an earlier layer is not evidence for a later layer.

## Repair

| Failure | Repair owner |
|---|---|
| Missing/invalid Component Task state | Component repository |
| Invalid Handoff facts | Handoff producer |
| Unknown component or parent mismatch | Integration repository System Task manifest |
| Revision differs from lock | Integration repository component lock |
| Integration validation fails | System Task; component fix gets a new Component Task when scope is new |
| Deployment acceptance fails | Deployment Task and rollback procedure |

After repair, rerun the failed layer and all later layers. Do not advance
delivery state merely by editing the manifest to silence a validator.
