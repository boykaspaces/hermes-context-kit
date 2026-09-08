# Hermes Runtime Adapter

Use this adapter when Hermes manages Context Kit projects. It is self-contained:
no private operations repository is required to discover the configuration,
paths, Skills, or validation steps.

## Contract

[`runtime-contract.json`](./runtime-contract.json) is the machine-readable
adapter contract. The Hermes solution fixes these locations:

| Artifact | Path |
|---|---|
| Hermes home | `/home/hermes/.hermes` |
| Global Skills | `/home/hermes/.hermes/skills/<skill-name>/` |
| Global SOUL | `/home/hermes/.hermes/SOUL.md` |
| Persistent workspace | `/workspace` |
| Workspace identity | `/workspace/.hermes/WORKSPACE_ID` |
| Workspace registry | `/workspace/.hermes/WORKSPACES.md` |

The operator or deployment supplies only a stable `workspace_id`, an immutable
Context Kit revision, and optional capabilities. The accepted configuration
shape is defined by [`runtime-config.schema.json`](./runtime-config.schema.json).

## Sixty-second Skill-first setup

Start from a clean Git checkout at a reviewed commit. Generate a configuration
without guessing the current revision:

```sh
python3 adapters/runtime/hermes/scripts/runtime_setup.py configure \
  --output /tmp/context-kit-hermes.json \
  --workspace-id my-hermes \
  --capability skill-authoring
```

`project-context` is always selected. Add `--capability multi-repo` only when
this Hermes instance coordinates System Tasks, component locks, Handoffs, or
cross-repository acceptance. Add `skill-authoring` only when it creates or
maintains reusable Skills.

Preview the complete write set:

```sh
python3 adapters/runtime/hermes/scripts/runtime_setup.py plan \
  --config /tmp/context-kit-hermes.json
python3 adapters/runtime/hermes/scripts/runtime_setup.py install \
  --config /tmp/context-kit-hermes.json
```

The second command is also a dry-run. If its paths and Skill inventory are
correct, run the host-side installation as the `hermes` service user (or
through an operator that preserves that ownership), then verify it:

```sh
python3 adapters/runtime/hermes/scripts/runtime_setup.py install \
  --config /tmp/context-kit-hermes.json \
  --apply
python3 adapters/runtime/hermes/scripts/runtime_setup.py verify \
  --config /tmp/context-kit-hermes.json
```

Installation refuses a dirty source checkout or one whose HEAD differs from
the configured commit. It also refuses to replace a different installed Skill
unless the operator reviews the difference and explicitly supplies `--replace`.
Replaced copies are retained under the Hermes home for rollback.

## When the agent cannot write the host runtime

Hermes commonly runs file and terminal tools inside a sandbox. A sandbox path
that resembles `~/.hermes` is not evidence that the host runtime changed.

If the agent has the host-side `skill_manage` tool, it may install the plan's
selected Skill tree through `create` plus `write_file`, preserving every
inventory entry, then verify discovery with `skill_view`. If it lacks either
host-side mechanism, it must not write a sandbox substitute. Report:

```text
Runtime setup: Pending user
Required action: run the printed runtime_setup.py install --apply command on
the Hermes host, then run verify.
Resume evidence: verify returns "ready": true.
```

The missing host write does not make the project initialization itself fail;
it leaves only runtime Skill installation pending.

## Skill selection

| Capability | Installed Skill | Required when |
|---|---|---|
| `project-context` | `project-context-management` | Always |
| `skill-authoring` | `skill-authoring` | Hermes creates or materially changes reusable Skills |
| `multi-repo` | `multi-repo-system-management` | Hermes coordinates more than one repository or an integration/deployment boundary |

The common Skills use portable `name` and `description` frontmatter. Hermes may
ignore the `metadata.context-kit` namespace while retaining it for release and
related-Skill validation. Use [`SKILL_AUTHORING.md`](./SKILL_AUTHORING.md) for
Hermes-specific authoring and destination rules.

## Optional SOUL reinforcement

SOUL is not required for Context Kit readiness. The Skills contain the complete
behavior; the optional fragment only reinforces when Hermes should load them.

Successful verification returns `"ready": true` independently of SOUL and
includes an optional next action. At that point, show the user the proposed
block:

```sh
python3 adapters/runtime/hermes/scripts/runtime_setup.py soul \
  --config /tmp/context-kit-hermes.json
```

Then ask whether they want it. Do not apply it merely because setup succeeded.
If the user explicitly chooses to add it, an operator with host access may run:

```sh
python3 adapters/runtime/hermes/scripts/runtime_setup.py soul \
  --config /tmp/context-kit-hermes.json \
  --apply
```

The command creates or replaces only the marked Context Kit block in the
operator-owned SOUL. Existing user content outside that block is preserved. A
user may instead merge
[`templates/SOUL.project-context.example.md`](./templates/SOUL.project-context.example.md)
manually, or decline it with no loss of Context Kit functionality.
