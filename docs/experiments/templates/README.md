# Delivery Governance Experimental Templates

Status: Experimental

| Template | Purpose | Use when |
|---|---|---|
| [`capability-audit.md`](./capability-audit.md) | Record required guarantees, primitive evidence, failure boundaries, and Gate 0 disposition | A governed Task depends on uncertain external or platform semantics |
| [`review-ledger.md`](./review-ledger.md) | Record contract-bound findings, review rounds, validation, and the external exact-head Final Audit boundary | A governed Task enters Initial Audit |

Copy only the template required by the current Task into
`tasks/evidence/TASK-NNN/`, link it from the Task, and replace every
placeholder. These files are advisory Phase 1 aids, not released runtime
templates or machine-enforced schemas.

