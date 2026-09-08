# ADR-003: Make Hermes Adoption Skill-First and SOUL Optional

Status: Active
Decision Area: Hermes Runtime Adoption
Supersedes: —
Superseded-By: —

## Context

The first Hermes adapter treated an operator-owned `SOUL.md` fragment as the
place that supplied workspace and Skill-installation bindings. A first-time
agent could understand Context Kit and initialize a project, but it could not
derive a complete Hermes installation plan without deployment-private
documentation. The deployed Hermes agent can manage global Skills through its
host-side Skill tool, but its sandbox does not expose the authoritative global
SOUL for direct mutation.

SOUL is also user-owned identity and behavior. Requiring Context Kit to change
it would unnecessarily couple functional adoption to persistent persona
mutation.

## Decision

Hermes adoption is Skill-first:

1. The public Hermes adapter owns a self-describing runtime contract, fixed
   solution paths, capability-to-Skill mapping, installation planning, and
   verification behavior.
2. The selected Skills contain all behavior required for correct operation.
   No correctness or safety rule may exist only in SOUL.
3. SOUL integration is optional behavioral reinforcement. The adapter offers a
   rendered snippet and an explicit user-controlled application method after
   Skill installation; absence of that snippet does not make adoption
   Incomplete.
4. Existing SOUL content is never overwritten or modified by default.
5. Consumer repositories own accepted Context Kit revisions, chosen
   capabilities, deployment evidence, and workspace identity values; they are
   not required to explain the public adapter contract.

For the Hermes solution profile, the adapter fixes these paths:

```text
Hermes home:       /home/hermes/.hermes
Global SOUL:       /home/hermes/.hermes/SOUL.md
Global Skill root: /home/hermes/.hermes/skills
Workspace root:    /workspace
Identity marker:   /workspace/.hermes/WORKSPACE_ID
Registry:          /workspace/.hermes/WORKSPACES.md
```

## Rationale

Skills are discoverable runtime capabilities and can be installed and verified
without changing user identity. A small optional SOUL hint can reduce missed
Skill activation, but making it mandatory would create a privileged
self-modification requirement and make a private deployment repository an
implicit dependency.

## Alternatives Considered

- Require a Context Kit SOUL block: rejected because it couples functional
  adoption to user-owned persistent identity and a host-side mutation path.
- Mount the Hermes home writable into the agent sandbox: rejected because it
  broadens access to runtime configuration and persistent agent state.
- Keep all runtime values private: rejected because a new public consumer
  could not know which configuration is required.

## Consequences

- Hermes users can complete functional adoption without modifying SOUL.
- The adapter must keep Skill discovery descriptions and runtime validation
  sufficient without global prompt reinforcement.
- SOUL status is reported separately as optional, recommended, applied, or
  declined; it does not determine runtime readiness unless a consumer adopts a
  stricter local policy.
- Other runtime adapters may choose different fixed paths and optional
  instruction mechanisms without changing the portable core.
