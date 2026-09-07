# Tasks and Delivery

## Ownership

`project-context-management` owns Task identity, the five valid Task statuses,
Task indexes, current pointers, progress fields, completion, and Checkpoints.
This reference owns only cross-repository relationships and delivery state.

## Task Types

Use an explicit field near the Task header:

```text
Type: Component
Type: System
Type: Deployment
```

- **Component** — accepted inside one component repository.
- **System** — coordinates two or more repositories or an assembled version.
- **Deployment** — performs an environment mutation and records acceptance or
  rollback. It is stored in the integration repository.

Existing Tasks may omit `Type`. Add it when enrolling an active Task into this
protocol; do not rewrite unrelated history.

## Parent Relationship

Every Component Task created for System work declares exactly one canonical
parent:

```text
Parent System Task: integration-project:TASK-014
```

The System Task lists each child by the same canonical identity. Do not infer
the relationship from matching titles, branch names, directories, or dates.

## System Task Manifest

Store the machine-readable component graph beside the integration Task:

```text
tasks/system/TASK-014.json
```

The Markdown Task remains the source of truth for goal, Task status, progress,
blockers, and next step. The JSON manifest owns:

- `system_task`, `system_id`, and `integration_project`;
- component repository and optional Component Task relationships;
- exact candidate revisions and delivery states;
- integration state and concise evidence pointers.

The manifest must not duplicate the Task's status or narrative progress.

## Delivery States

Delivery state is independent from Task status:

| State | Meaning |
|---|---|
| `pending` | No reviewable immutable component revision recorded |
| `handoff-ready` | Component validation passed and a full candidate SHA exists |
| `merged` | Candidate is present on the component's accepted integration branch |
| `locked` | Integration repository pins the exact accepted SHA |
| `verified` | Cross-component acceptance passed for that SHA |
| `deployed` | That SHA is evidenced in the target environment |

Advance one or more steps only when evidence supports the target state. A
state may move backward when review, validation, or deployment disproves it;
record the blocker and do not erase the failed evidence needed for recovery.

Integration state constrains every component included in the manifest:

- `integration.state: verified` requires every component to be `locked`,
  `verified`, or `deployed` and requires cross-component validation evidence;
- `integration.state: deployed` requires every component to be `deployed`,
  requires deployment evidence, and requires an explicit rollback pointer.

Do not leave an included component at `pending`, `handoff-ready`, or `merged`
while claiming verified or deployed integration. A component that is unchanged
still records its accepted immutable revision through the documented
`no-component-change` path; it is not excluded by leaving it pending.

## Revision Rules

- `handoff-ready` and later require a lowercase 40-character Git commit SHA.
- A branch may be recorded as a review route but never replaces the SHA.
- Whenever a component lock is supplied for validation, every manifest
  component requires a full immutable revision equal to its lock entry,
  regardless of delivery state.
- `verified` requires a cross-component validation evidence pointer.
- `deployed` requires deployment evidence and an explicit rollback pointer.

A component entry may omit `task` only in these cases:

| `task_absence_reason` | Additional requirement |
|---|---|
| `work-predates-protocol` | The implementation existed before protocol adoption |
| `no-component-change` | `source_system_task` identifies the earlier System Task that delivered the unchanged revision |

The immutable revision and all current acceptance gates remain required. A
ref-only merge, lock promotion, or deployment must not create a fake Component
Task when no component-owned file changes.

For `no-component-change`, `source_system_task` must identify a different,
explicitly completed prior state in the same integration project and system,
resolve to exactly one System or Deployment Task, and its canonical
`tasks/system/<TASK-ID>.json` manifest must be structurally valid and record the
same component, full revision, and an accepted delivery state of `locked` or
later. Every source component must declare either a canonical `task` or an
allowed `task_absence_reason`; this structural check does not recursively
validate inaccessible component repositories or provenance chains. "Prior"
is an explicit provenance relationship, not an ordering inferred from Task
IDs, timestamps, or file modification times.

Integration validation evidence, deployment evidence, and rollback are
pointers, not prose status claims. Record each as an HTTP(S) URL or a
repository-relative file pointer; do not use booleans, objects, null values, or
uncited narrative strings. Repository-relative pointers resolve from the
integration repository root and must name regular in-repository files without
crossing symlinks; HTTP(S) pointers must have a valid authority and no userinfo.

## System Task Procedure

1. Resolve the integration project and check its Task Index for duplicate
   scope.
2. Create or enroll the System Task using the standard Task lifecycle.
3. Create `tasks/system/<TASK-ID>.json` from the template and link it from the
   Task file.
4. Create Component Tasks only in repositories that require new work.
5. Record candidate SHAs after component validation, initially as
   `handoff-ready`.
6. After review/merge, update the accepted SHA and state to `merged`.
7. Advance the component lock in the integration repository, validate exact
   equality, then set `locked`.
8. Run system acceptance and record evidence before `verified`.
9. Record real deployment evidence and rollback before `deployed`.
10. Complete the System Task only when its own Goal is satisfied; synchronize
    all local pointers and indexes through `project-context-management`.

## Component Task Procedure

1. Resolve the component project and create a normal Task.
2. Set `Type: Component` and `Parent System Task:` to the canonical parent.
3. Implement, document, and validate only the component-owned scope.
4. Complete the Component Task when its local Goal is satisfied.
5. If direct integration access exists, update the System Task manifest there.
   Otherwise generate a Handoff through `handoffs.md`.

Component completion never advances the parent Task automatically.
