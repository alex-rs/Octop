---
name: mcporter
description: >-
  Use the mcporter CLI to list, configure, authenticate, and call MCP servers/tools (HTTP or stdio), with support for ad-hoc
  servers, config management, and CLI/type code generation. Use when the user mentions mcporter, wants to call an MCP server
  tool, list available MCP servers, generate an MCP CLI tool, or manage MCP config. Trigger words include: mcporter,
  MCP tool call, MCP server list, MCP CLI, MCP config, call mcp tool.
metadata:
  octop:
    emoji: "🔗"
    label:
      zh: "mcporter"
      en: "mcporter"
    summary:
      zh: "用 CLI 列出、配置并调用 MCP 服务器与工具。"
      en: "List, configure, and call MCP servers and tools from the CLI."
  harness:
    emoji: "🔗"
  lightclaw:
    emoji: "🔗"
    requires:
      bins:
        - mcporter
    install:
      - id: node
        kind: node
        package: mcporter
        bins:
          - mcporter
        label: "Install mcporter via npm"
      - id: brew
        kind: brew
        tap: steipete/tap
        formula: steipete/tap/mcporter
        bins:
          - mcporter
        label: "Install mcporter via Homebrew"
---

# mcporter — MCP Server/Tool CLI 🔌

You are an engineer well versed in the MCP (Model Context Protocol) ecosystem, skilled at using the
`mcporter` CLI to quickly discover, call, and manage MCP servers and tools.

## Prerequisites

Before doing anything, check whether mcporter is available:

```bash
mcporter --version
```

If the command does not exist, install it in one of the following ways (pick one):

```bash
# Option 1: install globally via npm
npm install -g mcporter

# Option 2: install via Homebrew
brew tap steipete/tap && brew install steipete/tap/mcporter

# Option 3: no installation needed, use npx directly
npx mcporter --version
```

> **Tip**: if you do not want a global install, every command can use `npx mcporter` instead of `mcporter`.

## Core Workflow

### 1. List available MCP servers and tools

mcporter automatically discovers local config (`~/.mcporter/mcporter.json`), project config
(`config/mcporter.json`), and configs imported from editors such as Cursor, Claude Desktop, and VS Code.

```bash
# List all configured servers
mcporter list

# View a server's tool list and argument schemas
mcporter list <server> --schema

# View the tools of a remote MCP endpoint (ad-hoc connection, no config needed)
mcporter list https://mcp.example.com/mcp --all-parameters

# List a local stdio server
mcporter list --stdio "bun run ./local-server.ts" --env TOKEN=xyz

# Output machine-readable JSON
mcporter list --json
```

### 2. Call MCP tools

Several syntax styles are supported; pick the one that best fits the situation:

```bash
# Selector style (most common): <server>.<tool> key=value key:number
mcporter call linear.list_issues team=ENG limit:5

# Function-call style
mcporter call 'linear.create_comment(issueId: "ENG-123", body: "Looks good!")'

# Shorthand (omit call)
mcporter linear.list_issues

# Call an MCP tool directly on a remote URL
mcporter call https://api.example.com/mcp.fetch url=https://example.com

# Call a local stdio server tool
mcporter call --stdio "bun run ./server.ts" scrape url=https://example.com

# Pass full JSON arguments
mcporter call <server.tool> --args '{"limit": 5, "query": "bug"}'
```

**Common flags:**
- `--output json` — output machine-readable JSON results
- `--raw` — output the raw result (no formatting)
- `--config <path>` — use a custom config file path
- `--no-coerce` — disable automatic argument type coercion
- `--log-level debug` — show debug logs
- `--tail-log` — tail the logs

### 3. Authentication (OAuth)

Some MCP servers require OAuth authentication:

```bash
# Perform OAuth login for a given server
mcporter auth <server>

# Reset authentication
mcporter auth <server> --reset
```

### 4. Config management

Manage connection config for MCP servers:

```bash
# List all current config
mcporter config list

# View a server's config
mcporter config get <server>

# Add a new global server
mcporter config add <name> <url>

# Import existing config from an editor (e.g. Cursor, Claude Desktop)
mcporter config import cursor --copy

# Remove config
mcporter config remove <server>

# Config login/logout
mcporter config login
mcporter config logout
```

### 5. Daemon

For stateful servers that need a persistent connection (such as Chrome DevTools), use daemon mode:

```bash
mcporter daemon start     # start the daemon
mcporter daemon status    # check status
mcporter daemon stop      # stop the daemon
mcporter daemon restart   # restart
```

### 6. Code generation

#### Generate a standalone CLI tool

Package any MCP server as a standalone command-line tool:

```bash
# Generate a CLI from a remote MCP endpoint
mcporter generate-cli --command https://mcp.context7.com/mcp

# Generate a CLI from a stdio command
mcporter generate-cli "npx -y chrome-devtools-mcp@latest"

# Generate and bundle
mcporter generate-cli --command <url> --bundle

# Generate a standalone Bun binary
mcporter generate-cli --command <url> --compile --runtime bun
```

#### Inspect a generated CLI

```bash
mcporter inspect-cli <path> [--json]
```

#### Generate TypeScript type definitions

```bash
# Generate a .d.ts type declaration file
mcporter emit-ts <server> --out types/<server>-tools.d.ts

# Generate a ready-to-use client wrapper
mcporter emit-ts <server> --mode client --out clients/<server>.ts

# Include optional arguments
mcporter emit-ts <server> --include-optional
```

## Operating Guide

- User says "list MCP servers" or "what MCP tools are there" → run `mcporter list`
- User says "call the xxx tool" or "call xxx" → call it with `mcporter call`
- User says "connect to an MCP server" → first confirm availability with `mcporter list <url>`, then add the config with `mcporter config add`
- User says "log in/authenticate" → run `mcporter auth <server>`
- User says "generate a CLI" or "package a tool" → use `mcporter generate-cli`
- User wants to call MCP from code → recommend mcporter's TypeScript API (`callOnce` or `createRuntime`)
- When machine-readable output is needed → always add `--output json` or `--json`

## Config File

Default config paths:
- **Global config**: `~/.mcporter/mcporter.json` (or `.jsonc`)
- **Project config**: `./config/mcporter.json`

mcporter automatically merges global config, project config, and editor-imported config. The default paths can be overridden with `--config <path>`.

## Important Notes

1. Every command can use `npx mcporter` instead of a globally installed `mcporter`
2. When calling tools, mcporter automatically coerces argument types (e.g. string to number); add `--no-coerce` if you do not want that
3. mcporter supports environment variable placeholders such as `${TAVILY_API_KEY}`
4. Results are printed in human-readable form by default; add `--output json` when a program needs to process them
5. OAuth credentials are cached locally; use `--reset` to authenticate again
