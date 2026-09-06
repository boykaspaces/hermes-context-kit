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
  --lock components/lock.yaml
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

The system-task mode additionally verifies:

- the Markdown Task is typed `System` or `Deployment`;
- manifest identity matches the integration project's `Project ID:`;
- component identities and delivery states are unique and valid;
- each declared Component Task exists in the supplied component checkout,
  declares `Type: Component`, and points back to the same parent System Task;
- `handoff-ready` and later have full commit SHAs;
- a missing Component Task has the explicit pre-protocol reason;
- `locked` and later match the supplied component lock;
- verified/deployed integration states have evidence pointers;
- deployed state has a rollback pointer.

The supported lock input is JSON or the `components` list shape used by the
neutral lock template. YAML syntax should also be checked by the repository's
native validator before semantic comparison.

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
