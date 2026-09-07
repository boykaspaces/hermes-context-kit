# Schema Index

| Schema | Owns |
|---|---|
| [`context-kit-adoption.schema.json`](./context-kit-adoption.schema.json) | Current neutral project adoption manifest v2 |
| [`context-kit-adoption-v1.schema.json`](./context-kit-adoption-v1.schema.json) | Legacy `.hermes/` adoption input |
| [`component-lock.schema.json`](./component-lock.schema.json) | Portable immutable component lock |
| [`system-task-v2.schema.json`](./system-task-v2.schema.json) | Separated source, acceptance, verification, deployment, and evidence structure |

JSON Schema validates artifact shape. Cross-file identity, Task relationships,
repository-relative evidence, and state transitions require the reference
validators.
