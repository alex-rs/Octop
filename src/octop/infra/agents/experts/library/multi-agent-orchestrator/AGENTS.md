# Multi-Expert Collaboration Protocol (AGENTS Guide)

This file defines the dispatch protocol for the main agent in "multi-expert collaboration orchestration" mode. It grounds the DAG concept of agency-orchestrator onto OCTOP's existing sub-agent delegation mechanism.

## 1. Role catalog and slug

OCTOP sub-agent persona files live at:

```
subagents/library/zh/<division>/<slug>.md
```

- `<division>`: academic / design / engineering / finance / game-development / gis / hr / legal / marketing / paid-media / product / project-management / sales / security / spatial-computing / specialized / supply-chain / support / testing
- `<slug>`: the filename (without .md), such as `engineering-software-architect`, `marketing-content-creator`

When delegating, reference `division/slug` (for example `engineering/engineering-code-reviewer`).

## 2. DAG structure (field conventions)

Describe each collaboration plan with the following structure:

```
goal: <one-sentence goal>
steps:
  - id: <step_id>
    role: <division>/<slug>        # which sub-agent executes this step
    task: "<task description, may reference upstream output with {{var}}>"
    depends_on: [<step_id>, ...]   # empty or omitted = can be dispatched in parallel immediately
    output: <output_var>           # named output of this step, for downstream reference
    llm: <optional, overrides the model used by this step>
```

## 3. Relay and parallelism rules

- **Relay**: in a downstream `task`, consume the upstream result with `{{previous step output}}` to avoid regenerating or losing context.
- **Parallelism**: steps with an empty `depends_on` are dispatched at the same time; dependent steps wait for their dependencies to finish before dispatch.
- **Convergence**: finish with one step (or the main agent itself) that aggregates all outputs into the final deliverable.

## 4. Team reuse (team)

For an ongoing project, record a locked set of `role` entries as a "team roster", for example:

```
team: "Product zero to one"
  - product/product-manager
  - engineering/engineering-software-architect
  - engineering/engineering-frontend-developer
  - engineering/engineering-code-reviewer
  - ops-engineer
```

Later tasks reuse that roster directly, saving the need to recast every time.

## 5. Execution discipline

- Present the DAG plan to the user for confirmation before dispatch (especially for steps involving irreversible operations or external calls).
- If a step fails: back off, re-sequence, or swap roles; do not blindly retry the same prompt.
- Steps with irreversible or external side effects (sending email, changing production, payments) must go through `securityGate` for a second confirmation.
- Every sub-agent invocation counts toward session audit (integrating with ai-safety-guardian's L8 Session Guard).

## 6. Boundary with single-agent mode

- If the goal can be split and each step needs a different professional perspective → use this collaboration protocol (multi-expert).
- If the goal is singular and the expertise is concentrated → let the matching expert/sub-agent do it directly; do not force orchestration.
