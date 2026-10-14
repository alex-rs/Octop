---
name: cheatsheet
description: A quick reference for AI coding tools plus a 60+ technique checklist — covering the capability matrix, core commands, and high-frequency technique categories of Claude Code / Cursor / Codex / Copilot / Aider and others. For coding coaches to cite when choosing tools and troubleshooting.
metadata:
  octop:
    emoji: "📋"
    label:
      zh: "AI Coding Cheatsheet"
      en: "AI Coding Cheatsheet"
    summary:
      zh: "Compare mainstream AI coding tools' capability matrix, commands, and high-frequency techniques."
      en: "Compare AI coding tools, commands, and high-frequency techniques."
---

# AI Coding Tool Quick Reference and Technique Checklist

## 1. Capability matrix of mainstream tools (selection reference)

| Tool | Form | Strengths | Fits |
| --- | --- | --- | --- |
| Claude Code | Terminal agent | Autonomous execution, subagents, hooks, engineered workflows | Multi-step engineering tasks, automated pipelines |
| Cursor | In-editor AI | Codebase understanding, Tab completion, multi-file editing | Everyday coding, refactoring |
| Codex / Copilot CLI | Cloud agent | One-off patches, command-line fixes | Patches, script generation |
| Aider | Terminal pair | Structured edits to an existing codebase | Modernizing legacy projects |
| Gemini CLI | Terminal agent | Long context, multimodal | Large files / document processing |
| Kiro / Trae / Windsurf | IDE agent | Different workflow preferences | Match your team's habits |

## 2. Technique categories of the six methodologies (derived from ai-coding-guide)

1. **Prompting (~12)**: clear intent, give examples, separate do/don't, testable acceptance.
2. **CLAUDE.md / project memory (~10)**: write good project conventions so the AI follows them automatically.
3. **Agent and Subagent (~10)**: use subagents to isolate context and parallelize independent tasks.
4. **Hook (~8)**: use hooks for automated checks (formatting, tests, pre-commit validation).
5. **Workflow (~12)**: plan-execute-verify loop, TDD, incremental commits.
6. **Git and PR (~8)**: disciplined commits, small PRs, AI-assisted review.

## 3. Debugging and cost (~16)

- **Debugging (~10)**: reproduce and localize first, then fix; use error messages; avoid mindless retries.
- **Performance and cost (~6)**: control context length, caching, batching, pick the right model tier.

## 4. Universal iron rules (words for the user)

- Context matters more than prompt wording: writing good "project memory" beats a long prompt every time.
- Small steps, fast feedback: every step verifiable and revertible is steadier than one big change.
- Evidence first: have the AI run tests/commands and paste the results; don't trust "it should be fixed now."
- Security: no secrets in prompts; watch out for dangerous commands the AI generates; don't send sensitive data outside.

> When the user is stuck, first judge whether it is "a context problem / a prompt problem / a tool capability limit," then give the matching remedy with concrete commands or templates.
