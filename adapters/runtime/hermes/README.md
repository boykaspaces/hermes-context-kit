# Hermes Runtime Adapter

Use this adapter when Hermes manages Context Kit projects. It is self-contained:
no private operations repository is required to discover the configuration,
paths, supported installation mechanism, or validation steps.

## Contract

[`runtime-contract.json`](./runtime-contract.json) is the machine-readable
adapter contract. The Hermes solution fixes these locations:

| Artifact | Path |
|---|---|
| Hermes home | `/home/hermes/.hermes` |
| Global Skills | `/home/hermes/.hermes/skills/<skill-name>/` |
| Install manifest | `/home/hermes/.hermes/context-kit-install.json` |
| Install transactions | `/home/hermes/.hermes/context-kit-transactions/` |
| Global SOUL | `/home/hermes/.hermes/SOUL.md` |
| Persistent workspace | `/workspace` |
| Installation source checkout | `/workspace/.context-kit/sources/hermes-context-kit` |
| Managed projects | `/workspace/projects/<project_id>` |
| Workspace identity | `/workspace/.hermes/WORKSPACE_ID` |
| Workspace registry | `/workspace/.hermes/WORKSPACES.md` |

The operator or deployment supplies only a stable `workspace_id`, an immutable
Context Kit revision, and optional capabilities. The accepted configuration
shape is defined by [`runtime-config.schema.json`](./runtime-config.schema.json).

## Checkout placement

An immutable checkout used only to install Skills is distribution source, not a
managed project. Put it at the contract's installation source path; it does not
receive a Workspace Registry row.

A checkout intentionally placed at
`/workspace/projects/hermes-context-kit` is instead a managed Context Kit
project. Its repository remains usable if registry approval is pending, but
project navigation is Incomplete until the user approves its entry in
`/workspace/.hermes/WORKSPACES.md`.

## Installation support

| Route | Support | Reason |
|---|---|---|
| Host operator runs `runtime_setup.py` | Required and supported | Reads the reviewed checkout directly, stages all selected Skills, verifies hashes, and records one package transaction |
| Agent uses `skill_manage` with model-supplied files | Unsupported for a complete release install | Cannot import an immutable checkout tree; supporting paths are allowlisted; multiple Skills exceed one package-wide atomic call |
| `skill_view` | Supplemental verification | Confirms discovery and rendered metadata after the operator package is ready |

`skill_manage` remains the correct tool for ordinary Hermes Skill authoring. It
is not a reliable transport for installing this multi-file release. If Hermes
later exposes a trusted immutable-tree import operation, a future adapter may
add a supported Agent route after conformance testing.

## Skill-first setup

Start from a clean Git checkout at a reviewed commit. An installation-only
checkout belongs at the fixed source-cache path, not below `projects/`:

```sh
mkdir -p /workspace/.context-kit/sources
git clone https://github.com/boykaspaces/hermes-context-kit.git \
  /workspace/.context-kit/sources/hermes-context-kit
git -C /workspace/.context-kit/sources/hermes-context-kit \
  checkout <reviewed-commit>
cd /workspace/.context-kit/sources/hermes-context-kit
./scripts/validate.sh
```

If that destination already exists, inspect it and update it through a reviewed
Git workflow; do not overwrite it or substitute mutable `main` for the selected
commit. Generate a configuration without guessing the current revision:

```sh
python3 adapters/runtime/hermes/scripts/runtime_setup.py configure \
  --output /tmp/context-kit-hermes.json \
  --workspace-id my-hermes \
  --capability delivery-governance \
  --capability skill-authoring
```

`project-context` is always selected. Add `--capability multi-repo` only when
this Hermes instance coordinates System Tasks, component locks, Handoffs, or
cross-repository acceptance. Add `skill-authoring` only when it creates or
maintains reusable Skills. Add `delivery-governance` only when at least one
managed project explicitly adopts the advisory extension; installing the Skill
does not enroll a project automatically.

Preview the complete write set:

```sh
python3 adapters/runtime/hermes/scripts/runtime_setup.py plan \
  --config /tmp/context-kit-hermes.json
python3 adapters/runtime/hermes/scripts/runtime_setup.py install \
  --config /tmp/context-kit-hermes.json
```

The second command is also a dry-run. It classifies every target as `fresh`,
`identical`, or `different`. A different target requires an explicit reviewed
`--replace`.

Run the mutation on the Hermes host as the `hermes` service user, or through an
operator that preserves that ownership:

```sh
python3 adapters/runtime/hermes/scripts/runtime_setup.py install \
  --config /tmp/context-kit-hermes.json \
  --apply
python3 adapters/runtime/hermes/scripts/runtime_setup.py verify \
  --config /tmp/context-kit-hermes.json
```

Only `verify` returning `"ready": true` proves installation. It checks the
ready manifest, exact Context Kit revision and capabilities, complete rendered
runtime inventories, transaction journal, workspace identity, and registry.

## Inventories and runtime metadata

Every plan publishes two disjoint inventories:

- `runtime_inventory`: `SKILL.md` plus files below `references/`, `templates/`,
  `scripts/`, and `assets/`; only these files are installed.
- `source_validation_inventory`: source-only tests or other release validation
  artifacts; these remain in the reviewed checkout and are never copied into
  the Hermes Skill root.

Before installation, run the Context Kit repository validator so both
inventories are backed by accepted source validation.

The operator renders generic top-level `version`, `author`, `platforms`,
`tags`, and `related_skills` fields into the installed `SKILL.md`, derived from
the portable `metadata.context-kit` values. The portable source metadata is
retained. Runtime hashes describe this deterministic rendered artifact, so
Hermes discovery metadata is verified without adding `metadata.hermes` to the
common Skill sources.

## Transaction and recovery states

| State | Meaning | Action |
|---|---|---|
| Fresh | Target Skill does not exist | Install without `--replace` |
| Identical | Runtime inventory already matches | No-op; manifest may be reconciled transactionally |
| Different | Target differs or is from another release | Review, then use `install --replace --apply` |
| Staging | A package transaction did not finish | Do not use as ready; inspect and run rollback |
| Ready | Manifest, all selected Skills, and workspace verify | Runtime may use the package |
| Failed | No verified package is active after rollback/failure | Repair and retry from an immutable checkout |

The installer stages every changed Skill before touching the active Skill root.
It journals all targets and restores every prior Skill if an ordinary failure
occurs. The canonical manifest remains `staging` after abrupt interruption, so
verification fails closed. Preview and apply its explicit recovery route:

```sh
python3 adapters/runtime/hermes/scripts/runtime_setup.py rollback \
  --config /tmp/context-kit-hermes.json
python3 adapters/runtime/hermes/scripts/runtime_setup.py rollback \
  --config /tmp/context-kit-hermes.json \
  --apply
```

Rollback restores the previous manifest when one existed. A first installation
that is rolled back records `failed` and is not ready.

## When the agent cannot write the host runtime

Hermes commonly runs file and terminal tools inside a sandbox. A sandbox path
that resembles `~/.hermes` is not evidence that the host runtime changed. The
agent must not fall back to inline `skill_manage` release installation.

Report the unresolved owner action explicitly:

```text
Runtime setup: Pending user
Waiting On: User
Required action: run the printed runtime_setup.py install --apply command on
the Hermes host, then run verify.
Resume evidence: verify returns "ready": true for the selected source revision.
```

The missing host write does not make project initialization fail; only runtime
Skill installation remains pending.

## Skill selection

| Capability | Installed Skill | Required when |
|---|---|---|
| `project-context` | `project-context-management` | Always |
| `delivery-governance` | `ai-delivery-governance` | A managed project's manifest and current Task explicitly opt into advisory delivery governance |
| `skill-authoring` | `skill-authoring` | Hermes creates or materially changes reusable Skills |
| `multi-repo` | `multi-repo-system-management` | Hermes coordinates more than one repository or an integration/deployment boundary |

Use [`SKILL_AUTHORING.md`](./SKILL_AUTHORING.md) for Hermes-specific authoring
and destination rules.

## Optional SOUL reinforcement

SOUL is not required for Context Kit readiness. The Skills contain the complete
behavior; the optional fragment only reinforces when Hermes should load them.

After Skill verification, show the user the proposed block:

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
