# CVM Doctor — AI-powered system diagnosis and repair Skill

> A structured Markdown knowledge system that gives AI Agents professional-grade system diagnosis and repair capabilities.
> Supports Linux / macOS / Windows, covers 60+ scenarios, and includes 126 concrete operation commands.

## What It Is

CVM Doctor is an **AI Agent Skill** (skill package), not a traditional script or program. It uses Markdown files as its carrier and, through a layered, modular organization of knowledge, guides an AI Agent to complete:

1. **Fast triage** (Quick, ~3 seconds) — scan the status of each component and return OK / WARNING / CRITICAL
2. **Deep diagnosis** (Deep, 20-60 seconds) — perform root cause analysis on abnormal components
3. **Safe repair** — recommend a repair plan that **must be executed only after user confirmation**

## Core Design

### Two-Stage Quick/Deep Architecture

```
User: "The server is very slow"
  │
  ▼
Quick Mode (3s) ──→ CPU OK / Memory WARNING / Disk OK / Network OK
  │
  ▼ (anomaly found)
Deep Mode (20s) ──→ Root cause: Java process memory leak, holding 8GB
  │
  ▼
Repair plan ──→ restart the Java service + tune JVM parameters (user confirmation required)
```

### Three-Tier Scenario Matching

```
Tier 1: 10 core scenarios built into SKILL.md     → covers 80% of common problems
  ↓ no match
Tier 2: references/00-scenario-index.md → 60+ extended scenarios, 20 major categories
  ↓ repair needed
Tier 3: commands/*.md                   → 126 concrete operation commands
```

### Cross-Platform Support

All diagnosis flows and commands are provided as a **Linux / macOS / Windows** three-platform comparison table, so the same diagnosis logic can be executed on different operating systems. The AI Agent automatically selects the corresponding command for the current system.

## Project Structure

```
cvm-ai-doctor/
├── SKILL.md                          # Entry file — always loaded by the AI Agent
├── API.md                            # Public API — cross-Skill reference contract
│
├── scripts/                          # Quick diagnosis scripts — 3-second scan
│   ├── quick_scan.sh                 #   Linux/macOS quick check
│   ├── quick_scan.ps1                #   Windows quick check
│   └── README.md                     #   Script usage instructions
│
├── references/                       # Diagnosis modules — loaded by the AI on demand
│   ├── 00-scenario-index.md          #   Scenario routing table (60+ scenarios)
│   ├── skill-collaboration.md        #   Skill collaboration guide
│   ├── resource-saturation-*.md      #   Resource diagnosis (Quick 1 + Deep 5)
│   ├── system-logs-*.md              #   Log diagnosis (Quick 1 + Deep 5)
│   ├── disk-smart-*.md               #   Disk SMART (Quick 1 + Deep 1)
│   ├── hardware-health-*.md          #   Hardware health (Quick 1 + Deep 1)
│   └── time-sync.md                  #   Time sync (Quick+Deep combined)
│
├── commands/                         # Operation command library — loaded on demand during repair
│   ├── debugging/                    #   Crash diagnosis, slow-system troubleshooting
│   ├── system-health/                #   System health check, starting services, upgrades
│   ├── network/                      #   LAN diagnosis, SSH
│   ├── security/                     #   Firewall, audit, permissions
│   ├── hardware/                     #   CPU/GPU/RAM/motherboard profiling
│   ├── storage/                      #   Disk health, RAID, NFS/SMB
│   ├── installation/                 #   CLI/GUI tool installation
│   ├── dev-tools/                    #   Docker/Python/Node/SDK
│   └── ... (29 categories, 126 command files)
│
└── docs/                             # Developer docs — for human maintainers
    ├── architecture.md               #   Architecture design
    ├── scenario-decision-guide.md    #   Scenario decision guide
    └── scenario-index-maintenance.md #   Scenario index maintenance
```

## Covered Scenarios

| Category | Example scenarios | Priority |
|------|---------|--------|
| **Performance problems** | Slow/laggy system, high CPU, insufficient memory, slow disk I/O, slow network | High frequency |
| **Health checks** | Comprehensive health check, periodic maintenance | High frequency |
| **Error troubleshooting** | Crash/reboot, service failure, error logs | High frequency |
| **Hardware diagnosis** | Disk failure, overheating, GPU problems, RAID | High frequency |
| **Time synchronization** | NTP offset, inaccurate clock | High frequency |
| **Network** | LAN connection, firewall, SSH | Medium frequency |
| **Security** | Security audit, permission problems, anti-virus | Medium frequency |
| **Development environment** | Docker, Python/conda, Node.js, SDK | Medium frequency |
| **Configuration** | Git, SSH, PATH, Bash | Medium frequency |
| **Display/desktop** | Multiple monitors, KDE Plasma, audio, Bluetooth | Low frequency |
| **Advanced storage** | NFS/SMB mounts, BTRFS snapshots | Low frequency |
| **Local AI** | Ollama, ComfyUI, MCP, speech recognition | Low frequency |

## How to Use

### Prerequisites

- **Linux/macOS**: `bash` and `ps`
- **Windows**: PowerShell 5.1+ 
- Supported systems: Linux (complete), macOS (complete), Windows (complete)

### Using It as an AI Agent Skill

CVM Doctor is designed to be used directly by AI Agents (such as WorkBuddy, Claude Code, etc.):

1. **Install the Skill**: configure the `cvm-ai-doctor/` directory as the Agent's Skill directory
2. **Trigger a diagnosis**: describe the problem in natural language, for example:
   - "The server is very slow, take a look for me"
   - "CPU is at 100%, why"
   - "Run a system health check for me"
   - "The disk reported an error, how do I read SMART"
3. **The AI executes automatically**: the Agent loads SKILL.md → matches a scenario → Quick triage → Deep root cause analysis → recommends a repair
4. **Safety gating**: all repair operations are executed only after the user confirms them

### Extending Scenarios

You only need to add one `.md` file to extend with a new scenario:

1. Add a Quick/Deep diagnosis module under `references/`
2. Add a repair command file under `commands/`
3. Register the new scenario in `references/00-scenario-index.md`

## Remote Diagnosis

The Skill's knowledge system is inherently transferable. Combined with tools such as SSH and SCP, the diagnosis capability can be extended to remote servers:

```bash
# Transfer the Skill to the remote host
scp -r cvm-ai-doctor/ user@remote:/tmp/

# After SSH-ing into the remote host, the AI Agent diagnoses using the local Skill
ssh user@remote
# Agent: "check system health" → use /tmp/cvm-ai-doctor/SKILL.md to diagnose the remote machine
```

You can also mount the Skill ConfigMap through a Pod in a K8s environment to achieve container-level batch diagnosis.

## Documentation

- [Architecture design](docs/architecture.md) — modular design, Quick/Deep architecture, cross-platform approach
- [Scenario decision guide](docs/scenario-decision-guide.md) — complete workflows for the 60+ scenarios
- [Scenario index maintenance](docs/scenario-index-maintenance.md) — how to maintain and extend the scenario library

## Version Information

- **Current version**: v1.1
- **Coverage**: 20 major categories, 60+ granular scenarios, 126 operation commands
- **Runtime dependencies**: bash / PowerShell
- **Platform support**: Linux (complete) / macOS (complete) / Windows (complete)

**Recent updates** (2026-03-27):
- ✅ Added a Windows PowerShell quick diagnosis script (`scripts/quick_scan.ps1`)
- ✅ Added a Skill collaboration guide (`references/skill-collaboration.md`)
- ✅ Quick Mode performance optimization: 10s → 3s (using scripts instead of standalone commands)
- ✅ Public API specification (`API.md`), supporting cross-Skill references
