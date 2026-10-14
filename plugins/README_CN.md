# Octop Plugin Examples

[English](./README.md)

This directory provides plugin demos covering the `kind` values supported by Octop / octop-harness, plus a **frontend + backend** UI rendering example.
The layout is inspired by [octop-toolkit](https://github.com/veenyi/octop-plugins/tree/main/octop-toolkit).

Product plugins shipped with the Octop installation package live in `src/octop/infra/agents/plugins/bundled/`.
When `octop init` and `octop run` start up, they copy missing plugins into `~/.octop/plugins/` and write them as **globally off** in `config.json`; an administrator turns them on in the Dashboard plugins page before agents can use them. Uninstalled ids are not installed back automatically.

## Demo Overview

| Directory | `kind` | Purpose |
|------|--------|------|
| [`demo-toolkit`](./demo-toolkit/) | `tool` | Register callable tools (time, text stats, configurable prefix echo) |
| [`demo-greeting-skill`](./demo-greeting-skill/) | `skill` | Sync a sample Skill into the agent workspace |
| [`demo-turn-logger`](./demo-turn-logger/) | `hook` | Register `AgentMiddleware` that logs before/after model calls |
| [`demo-ui-card`](./demo-ui-card/) | `tool` + `ui/` | The backend returns `octop_ui` JSON; the frontend renders an interactive card in chat |

## Directory conventions

Each plugin is a folder containing at least:

```text
my-plugin/
├── plugin.yaml    # id, version, name, kind, entry; optional icon / ui
├── main.py        # must define setup(ctx)
├── skills/        # skill plugins only: <name>/SKILL.md
└── ui/            # optional: prebuilt frontend (no npm run at install time)
    └── dist/
        ├── index.js       # ESM, exports setup(host)
        └── manifest.json  # declares renderer ↔ tool
```

In `setup(ctx)`, call the API that matches `kind`:

| `kind` | API |
|--------|-----|
| `tool` | `ctx.tool(name, fn, description=..., config_fields=...)` |
| `skill` | `ctx.skills("skills")` — relative to the plugin root |
| `hook` | `ctx.middleware(instance, priority=...)` |

### Tool plugins with a UI

Optional `plugin.yaml` fields:

```yaml
icon: "🧩"   # or an https://… image URL, shown on Dashboard cards
ui:
  entry: ui/dist/index.js
  manifest: ui/dist/manifest.json
```

Tools return a JSON string (recommended):

```json
{
  "octop_ui": { "renderer": "demo_card", "version": 1 },
  "data": { "title": "…", "count": 1 },
  "text": "plain text fallback"
}
```

The Dashboard loads `index.js` through `GET /api/plugins/{id}/ui/…` and calls `setup(host)` to register renderers.
`host.patchResult(callId, data)` can refresh the bubble without re-running the LLM (L2); streaming still replaces the whole `output` over SSE (L1).

The plugin ESM is a self-contained file; React is injected by the Dashboard as `window.__OCTOP_REACT__` / `__OCTOP_JSX__`.

## Install locally

```bash
# Install from a directory (common during development)
octop plugin install ./plugins/demo-toolkit --force
octop plugin install ./plugins/demo-greeting-skill --force
octop plugin install ./plugins/demo-turn-logger --force
octop plugin install ./plugins/demo-ui-card --force
octop plugin list
```

Or pack it first and then install:

```bash
cd plugins
zip -r demo-ui-card.zip demo-ui-card/
octop plugin install ./demo-ui-card.zip --force
```

**Dashboard:** Admin → Plugins → Install. Paste the ZIP's **direct download URL**
(for GitHub use `raw.githubusercontent.com` or a Download / raw link, not the `/blob/` page).

- **tool**: after installing, go to "Tool management" and enable the tools for the specific agent  
- **skill**: synced into the workspace `skills/` when the agent starts  
- **hook**: globally enabled plugins get the corresponding middleware attached  
- **ui**: installed together with the plugin; the renderer loads automatically once you open the chat page  

## Packaging notes

The ZIP should contain **exactly one** plugin root directory with a `plugin.yaml`; if it includes a UI, pack the prebuilt `ui/dist/` as well (**do not** rely on the server running `npm install`).

```bash
# Correct: a single plugin directory
zip -r demo-toolkit.zip demo-toolkit/

# Wrong: several plugins crammed into one ZIP, or loose files with no plugin root directory
```

## Quick validity check

Run this from the repository root (no service startup needed):

```bash
uv run python - <<'PY'
from pathlib import Path
from octop_harness.plugins import PluginRegistry, load_plugin_dir

for name in ("demo-toolkit", "demo-greeting-skill", "demo-turn-logger", "demo-ui-card"):
    PluginRegistry.reset()
    p = load_plugin_dir(Path("plugins") / name, install_deps=False)
    print(
        p.manifest.id,
        p.manifest.kind,
        f"tools={len(p.tools)}",
        f"mw={len(p.middleware)}",
        f"skills={p.skills_dir}",
    )
PY
```

Expected result:

- `demo-toolkit` → `tool`, 3 tools  
- `demo-greeting-skill` → `skill`, `skills/` exists  
- `demo-turn-logger` → `hook`, 1 middleware  
- `demo-ui-card` → `tool`, 1 tool  
