---
name: engineering-workflow
description: Execution details for a reliable engineering workflow — explore → plan → TDD → systematic debugging → code review → verify before completion. Used by the Methodology Coach to guide step by step through development tasks.
metadata:
  octop:
    emoji: "🛠️"
    label:
      zh: "Engineering Workflow"
      en: "Engineering Workflow"
    summary:
      zh: "Guide development through explore, plan, TDD, debug, review, and verify."
      en: "Guide development through explore, plan, TDD, debug, review, and verify."
---

# Reliable Engineering Workflow (Execution Details)

When you take on a development task, proceed in the order below. Every phase needs a "verifiable exit"; do not skip steps.

## Phase 1 — Brainstorming
- Answer first: what problem are we solving? What does success look like? What are the boundaries and constraints?
- If unsure, ask the user; do not assume. Produce a clear problem definition.

## Phase 2 — Writing Plans
For multi-step tasks, write the plan down first:
```
Goal: <one sentence>
Steps:
  1. <step> — Acceptance: <how to confirm completion>
  2. ...
Risks: <known pitfalls>
```
Write code only after the plan is confirmed. Small changes may skip the explicit plan, but verification may not be skipped.

## Phase 3 — TDD
1. Write a test that **fails**, defining the boundary of "done".
2. Write the **minimal implementation** to make the test green.
3. Refactor, keeping the test green.
Do not "write a big pile of implementation first and add tests later" — that amounts to having no acceptance.

## Phase 4 — Systematic Debugging
When something fails:
1. Reproduce: find the minimal input that reproduces it reliably.
2. Observe: use logs/breakpoints/prints to establish a signal and locate the failing layer.
3. Hypothesize: propose 1–3 possible root causes.
4. Experiment: verify and eliminate the hypotheses one by one with minimal changes.
5. Fix: change the code only after locating the root cause, never by guessing.
Forbidden: blindly changing code to try your luck, and retrying the same prompt endlessly.

## Phase 5 — Code Review (Requesting / Receiving)
- Request review proactively before merging; self-check list: correctness, boundaries, error handling, maintainability, test coverage.
- When review comments arrive: understand and respond to each one; do not ignore it because it is "small"; if you push back, give your reasons.

## Phase 6 — Verification Before Completion
Before claiming completion you must have evidence:
- Tests pass (paste the output or state it explicitly)
- The command/script actually ran
- Key behavior was confirmed
Without evidence, keep quiet; do not say "it should be fine".

## Finishing (Finishing a Development Branch)
Feature complete → guide the merge / PR / branch cleanup. Use conventional commits, with clear Chinese commit messages stating the intent.
