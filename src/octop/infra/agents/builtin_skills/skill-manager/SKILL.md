---
name: skill-manager
description: Must use for managing the current expert instance's Skills through conversation, including finding, inspecting, installing, importing, updating, editing, listing, restoring, or deleting. Supports skillhub.cn/skills/... page URLs, the SkillHub CLI, local and uploaded files, SKILL.md, ZIP/TAR, Git/GitHub, and plain download URLs; also used to organize arbitrary material such as PDFs, Markdown, documents, code, and images into a new Skill. Must use for conversational Skill management from files, URLs, Git repositories, archives, or SkillHub.
metadata:
  octop:
    emoji: "🧩"
    label:
      zh: "Skill Manager"
      en: "Skill Manager"
    summary:
      zh: "Find, install, import, update, or delete skills on this instance."
      en: "Find, install, import, update, or delete skills on this instance."
---

# Skill Manager

Only manage the current instance's `{{OCTOP_SKILLS}}/`. The current instance workspace is fixed at `{{OCTOP_WORKSPACE}}`; uploaded files usually live in its `inbound/`. System files (skills, built-in skills, sessions, etc.) live in the directory containing `{{OCTOP_SKILLS}}`. Do not use `pwd`, `$HOME`, `~/.octop-harness/workspace`, memory files, or search results to re-guess the workspace. Do not modify other instances, global Skill directories, or `{{OCTOP_BUILTIN_SKILLS}}/`.

## Operation Entry Point

Use the built-in script to inspect, download, safely unpack, install, list, and delete:

```bash
python "{{OCTOP_BUILTIN_SKILLS}}/skill-manager/scripts/manage_skills.py" <command>
```

```bash
# List installed skills
... list

# Inspect the source without writing to the installed skills directory
... inspect "<file-directory-url-or-skillhub:slug>"

# Install; multiple Skills inside a repository or archive can be installed in one go
... install "<source>" [--subpath "path/in/repo"] [--name "slug"]

# Overwrite only after the user has explicitly agreed to replace
... install "<source>" --force

# SkillHub search; the results can be inspected or installed with skillhub:<slug>
... skillhub-search "<query>" --limit 10

# Run only after the user has explicitly agreed to delete; actually moves the skill to skills/.trash/
... remove "<slug>" --yes

# Restore from the trash
... restore "<trash-name>"
```

## Handling Sources

1. **A ready-made Skill, directory, or ZIP/TAR**: run `inspect` first; once the check passes and the user has asked for installation, run `install`.
2. **Git/GitHub URL**: repositories, GitHub `tree` subdirectories, and `blob` URLs pointing at `SKILL.md` can all be handled directly. For complex repositories use `git+<url>` and `--subpath`.
3. **SkillHub page URL**: `https://skillhub.cn/skills/<namespace>/<slug>` can be passed straight to `inspect` or `install`; the script parses the namespace and the slug. Do not install or upgrade the CLI yourself, and do not run `skillhub install` directly.
4. **Plain HTTP(S) URL**: the script handles direct files and archives. If the URL is some other introductory web page, first read it with the available web tools to find the public repository, the download URL, or the `SKILL.md`, then hand that to the script. Do not bypass logins, paywalls, or access controls.
5. **SkillHub search**: when the user only describes a capability, search first and present 1–3 candidates with their slug, name, purpose, and source so the user can choose; when the user has already named a specific Skill, inspect and install it directly.
6. **Any non-Skill file**: ordinary material does not become a Skill just by being copied. Read and understand the material first, then use the built-in `skill-creator` workflow to organize the reusable knowledge, steps, and required resources into a valid Skill, write it to `{{OCTOP_SKILLS}}/<slug>/`, and then run `inspect` to validate it.

## Change Rules

- A new install request itself counts as consent to add; if the target already exists, stop and explain the conflict, and use `--force` only with explicit consent.
- Before editing an existing Skill, read its `SKILL.md` and related resources, and only change that Skill's directory; run `inspect` again after editing.
- Name the target and get explicit confirmation before deleting. Use `remove --yes` rather than `rm -rf` directly. Use `restore` when you need to recover something.
- After installing, report the slug and the final path. Newly installed, updated, or deleted Skills usually take full effect from the next new session.

## Security Boundaries

- The script limits the download and unpack size and the file count, rejects path traversal and symlinks, and installs through a staging directory.
- Do not execute, import, or source code from downloaded packages. Installing means deploying the Skill content; it does not mean third-party code has passed a security audit.
- Do not echo URL credentials in output; for private sources use only the Git or SkillHub credentials already present in the environment.
- If the current instance has no Shell execution capability, you can still handle simple text Skills with file tools, but you must state that URL downloads, safe unpacking, and the SkillHub CLI cannot be done that way — do not pretend they succeeded.
