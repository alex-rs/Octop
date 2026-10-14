# CVM Doctor Public API

> **Version**: 1.1 | **Updated**: 2026-03-27
>
> This file declares the file paths and formats that external Skills (such as remote-doctor, health-check) can stably reference.
> Files that are not listed are treated as internal implementation and may change at any time.

---

## References

Diagnosis knowledge modules. External consumers reference them by file path and extract diagnosis commands and decision logic from them.

### Quick (fast scan, 10s level)

| Path | Purpose |
|------|------|
| `references/resource-saturation-quick.md` | CPU / memory / disk / network quick scan, returning OK / WARNING / CRITICAL per component |
| `references/system-logs-quick.md` | Kernel / OOM / file system / auth / service log error scan |
| `references/disk-smart-quick.md` | Disk SMART health check |
| `references/hardware-health-quick.md` | CPU temperature / memory / RAID / battery status |
| `references/time-sync.md` | NTP time synchronization status (Quick + Deep combined) |

### Deep (root cause analysis, 20-60s level)

| Path | Purpose | When to trigger |
|------|------|---------|
| `references/resource-saturation-deep-cpu.md` | CPU root cause analysis | Quick reports CPU WARNING+ |
| `references/resource-saturation-deep-memory.md` | Memory root cause analysis | Quick reports Memory WARNING+ |
| `references/resource-saturation-deep-disk.md` | Disk I/O root cause analysis | Quick reports Disk WARNING+ |
| `references/resource-saturation-deep-network.md` | Network root cause analysis | Quick reports Network WARNING+ |
| `references/resource-saturation-deep-combined.md` | Multi-component correlation analysis | Quick reports 2+ abnormal components |
| `references/system-logs-deep-kernel.md` | In-depth kernel log analysis | Quick reports kernel errors |
| `references/system-logs-deep-oom.md` | OOM event analysis | Quick reports OOM |
| `references/system-logs-deep-fs.md` | File system error analysis | Quick reports FS errors |
| `references/system-logs-deep-auth.md` | Authentication failure analysis | Quick reports auth errors |
| `references/system-logs-deep-service.md` | Service failure analysis | Quick reports service errors |
| `references/disk-smart-deep.md` | Detailed SMART analysis | Quick reports SMART FAIL |
| `references/hardware-health-deep.md` | In-depth hardware check | Quick reports hardware anomalies |

### Index

| Path | Purpose |
|------|------|
| `references/00-scenario-index.md` | 60+ scenario routing table (keyword → diagnosis flow → command path) |
| `references/skill-collaboration.md` | Skill collaboration guide (division of labor and cross-references with Skills such as health-check) |

---

## Skill Collaboration

### Integration with other Skills

| Skill | Collaboration | Reference doc |
|-------|---------|---------|
| `health-check` | Division of labor: CVM Doctor handles **performance diagnosis**, Health Check handles **platform self-check** | `references/skill-collaboration.md` |
| `remote-connect` | Remote diagnosis: CVM Doctor provides the commands, remote-connect executes them | `SKILL.md` Remote Diagnostics section |

**Cross-reference points**:
- CVM Doctor detects LightClaw process anomaly → Suggest health-check
- Health Check detects host resource issue → Suggest CVM Doctor
- User says ambiguous "check the system" → CVM Doctor prioritizes, then suggests health-check if all OK

---

## Commands

The `commands/` directory contains 126 command files, referenced by the scenario index through paths.

External consumers do **not** need to maintain a complete list of command paths — dynamic lookup through `00-scenario-index.md` is enough. Only the format is fixed here.

### File Format Contract

Every command `.md` file follows this structure:

```
# Title

## Platform Detection
OS_TYPE=$(uname -s) detection section

## Diagnosis/Operation Steps
Markdown table, with fixed columns:

| Check item | Linux | macOS | Windows |
```

**Contracts you can rely on:**

1. The table cells contain **directly executable shell commands**
2. All diagnosis commands are **read-only** (they do not change system state)
3. Commands that modify the system are marked with `⚠️` in the file and require user confirmation

---

## Diagnosis Flow Contract

```
Quick → Triage → Deep three-stage flow:

1. Quick: read *-quick.md, run the commands in it, and collect the status of each component
2. Triage: decide which Deep module to use based on the Quick results
   - 1 abnormal component → the corresponding *-deep-{component}.md
   - 2+ abnormal components → *-deep-combined.md
   - All normal → end
3. Deep: read the corresponding *-deep-*.md, run the commands in it, and output the root cause analysis
```

An external orchestrator only needs to implement this three-step flow; the specific commands are extracted from the reference files.

---

## Diagnosis Statistics

After each diagnosis is completed, the Agent automatically appends a JSONL record.

### Statistics File

| Path | Format | Purpose |
|------|------|------|
| `~/.lightclaw/stats/cvm-doctor.jsonl` | JSONL (one JSON object per line) | Local diagnosis statistics, usable for aggregate analysis |

### Record Schema

```json
{
  "ts": "ISO8601",
  "mode": "quick | deep | quick+deep",
  "scenario": "Tier 1 scenario name or general",
  "os": "linux | darwin | windows",
  "duration_s": "int (seconds)",
  "components": {
    "cpu": "ok | warning | critical | skipped",
    "memory": "ok | warning | critical | skipped",
    "disk": "ok | warning | critical | skipped",
    "network": "ok | warning | critical | skipped"
  },
  "issues_found": "int (number of WARNING + CRITICAL components)",
  "severity": "ok | warning | critical",
  "trigger": "user | cron"
}
```

### How to Consume It

External tools can read this file for aggregate analysis:

```bash
# Count the total number of diagnoses
wc -l ~/.lightclaw/stats/cvm-doctor.jsonl

# Count the issue discovery rate
jq -s '[.[] | select(.issues_found > 0)] | length as $issues | length as $total | {total: $total, issues: $issues, rate: ($issues/$total*100)}' ~/.lightclaw/stats/cvm-doctor.jsonl

# Count the anomaly distribution across components
jq -s '[.[] | .components | to_entries[] | select(.value != "ok" and .value != "skipped")] | group_by(.key) | map({component: .[0].key, count: length})' ~/.lightclaw/stats/cvm-doctor.jsonl
```

---

## Changelog

| Date | Version | Change |
|------|------|------|
| 2026-04-08 | 1.2 | Added a diagnosis statistics section declaring the `cvm-doctor-stats.jsonl` format and how to consume it |
| 2026-03-27 | 1.1 | Added a Skill collaboration section declaring the division of labor with health-check; added `references/skill-collaboration.md` |
| 2026-03-26 | 1.0 | Initial version |
