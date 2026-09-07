# Public Protocol Specification

This directory owns the portable contracts implemented by Context Kit.
Specifications describe observable project behavior and machine-readable
artifacts; Skills explain when and how an agent applies those contracts.

## Current contracts

| Contract | Version | Owns |
|---|---:|---|
| [Project adoption](./project/v2.md) | 2 | Neutral namespace, adapters, canonical state, and proposal activation |
| [Multi-repository coordination](./multi-repo/v2.md) | 2 | Component acceptance, verification, deployment applicability, and evidence |

Project adoption [v1](./project/v1.md) remains an explicit legacy migration
input; it is not the default for new projects.

Published specification versions are immutable. Compatible clarification may
improve prose or implementation without changing required behavior. A change
that invalidates a previously conforming artifact requires a new specification
version and a migration path.

JSON Schemas under [`../schemas/`](../schemas/) define machine-readable
artifact structure. Normative cross-field invariants that JSON Schema cannot
express are stated in the matching specification and enforced by validators.

## Design boundaries

- Core contracts contain no deployment paths, account identifiers, provider
  names, or consumer repository assumptions.
- Profiles add coherent capabilities; they do not redefine core ownership.
- Consumers record project-specific data only through documented extension
  points or consumer-owned artifacts.
- An inaccessible repository is `not_checked`, never implicitly passed.
- Task status, component acceptance, integration verification, and deployment
  state are separate facts.
