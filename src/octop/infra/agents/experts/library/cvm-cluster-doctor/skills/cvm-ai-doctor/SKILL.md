---
name: cvm-ai-doctor
description: CVM instance health diagnosis, using an intelligent quick/deep inspection mode. Covers professional inspection, diagnosis, and repair of performance and usage problems. Supports server, PC, virtual machine, and container scenarios, and supports Linux/macOS/Windows.
metadata:
  openclaw:
    requires:
      bins: ["bash", "ps"]
    os: ["linux", "darwin", "windows"]
  octop:
    emoji: "🩺"
    label:
      zh: "CVM AI Diagnosis"
      en: "CVM AI Doctor"
    summary:
      zh: "Triage quickly, then deep-check CPU, memory, disk, and network problems."
      en: "Triage then deeply diagnose CPU, memory, disk, and network issues."
---

# CVM AI Doctor Skill

**Purpose**: intelligently diagnose all kinds of performance and usage problems on a system, using a quick check (10-second triage) → deep analysis (20-60 seconds) workflow.

**Supported systems**: local servers, personal computers (Mac/Windows/Linux), virtual machines, containers.

---

## 🎯 When to Use This Skill

**Core capabilities**:
- System performance diagnosis (CPU, memory, disk, network)
- Health checks (quick scan, comprehensive analysis)
- System troubleshooting (crash, error, slow, laggy)
- Performance optimization suggestions
- **Cluster management**: multi-node health inspection, scoring, correlation analysis, risk-gated remediation (requires the `tencentcloud-infra` skill)

**Trigger keywords**: see the complete keyword list in "Tier 1 Core Scenarios"

**Note**: if the user mentions "LightClaw self-check" or "platform health check" or "security check", please use the `health-check` skill.

**Note**: if the user mentions "cluster", "all nodes", "all CVMs", use the cluster management scenario, which requires loading the `tencentcloud-infra` skill as well.

### 🌐 Remote Servers

- The user mentions an **IP address** or a **remote host** → use together with the `remote-connect` skill (see the "Remote Diagnosis" section)

---

## 🚀 Quick/Deep Diagnosis Workflow

Two-stage diagnosis approach:

```yaml
Quick mode (3-10 seconds):
  - Quickly scan all components
  - Execution strategy:
      Preferred: run the quick scan script (if present) → ~3 seconds
        - Windows: pwsh scripts/quick_scan.ps1
        - Linux/macOS: bash scripts/quick_scan.sh
      Fallback: read resource-saturation-quick.md → run individual commands → ~10 seconds
  - Returns: OK / WARNING / CRITICAL status for each component
  
Deep mode (20-60 seconds, triggered on demand):
  - Single component: analyze only the flagged components
  - Multiple components: use combined correlation analysis
  - Root cause analysis + recommendations

Decision rules:
  - General problem ("slow", "laggy") → quick scan first, then deep analysis of the flagged components
  - Specific component ("high CPU") → skip quick, go straight to deep analysis
  - Multiple anomalies (2+ flagged) → use deep combined analysis
  - Health check → quick scan only; stop if everything is OK
```

---

## 🔍 Scenario Matching

### Tier 1: Core Scenarios (80% coverage)

Prioritize matching the following scenarios:

```yaml
Slow/laggy system (System Slow):
  keywords: [slow, laggy, slow, lag, slow response, sluggish, performance problem, performance issue, performance fault, performance problem]
  workflow: quick scan → deep analysis of the flagged components
  fixes: [commands/debugging/diagnose-slowdown.md, commands/system-health/review-startup-services.md]

High CPU usage (High CPU):
  keywords: [CPU, high cpu, cpu 100%, CPU maxed]
  workflow: use resource-saturation-deep-cpu.md directly
  fixes: [commands/hardware/hardware-profilers/by-component/profile-cpu.md]

Insufficient memory (Low Memory):
  keywords: [memory, memory, OOM, swap, low memory]
  workflow: use resource-saturation-deep-memory.md directly
  fixes: [commands/hardware/hardware-profilers/by-component/profile-ram.md]

Disk problems (Disk Issues):
  keywords: [disk, disk, I/O, slow io, disk full, disk space, drive full, C drive, D drive, disk full, space, storage]
  workflow: use resource-saturation-deep-disk.md directly
  fixes: [commands/optimisation/large-files.md, commands/storage/health-checks/check-drive-health.md]

Network problems (Network Issues):
  keywords: [network, network, NIC, packet loss]
  workflow: use resource-saturation-deep-network.md directly
  fixes: [commands/network/lan/diagnose-lan-connectivity.md]

Health inspection (Health Check):
  keywords: [check, health, health, check, diagnosis, health check, health score, inspection, professional check, expert check, quick check, in-depth check, deep check, comprehensive check]
  workflow: |
    General health check → run the quick scan script (3 seconds):
      Stop if everything is OK.
    Comprehensive health check (user says "comprehensive check" / "full health check" / "full system check" / "in-depth check" / "deep check" / "professional check" / "expert check"):
      Run 3 quick modules in order:
        1. resource-saturation-quick.md (CPU/memory/disk/network)
        2. system-logs-quick.md (kernel/OOM/file system/auth/service errors)
        3. disk-smart-quick.md (disk SMART health)
      Perform deep analysis on any WARNING/CRITICAL components found.
  fixes: [commands/system-health/system-health-checkup.md]

System crash/errors (System Crash):
  keywords: [crash, crash, error, error, reboot, reboot, system rescue, system emergency, emergency, rescue, emergency repair, fault repair]
  workflow: system-logs-quick.md → deep analysis of the error category
  fixes: [commands/debugging/diagnose-crash.md]

Performance tuning (Performance Optimization):
  keywords: [performance optimization, performance improvement, improve performance, performance optimization, performance tuning, optimize, tuning, tuning, optimization suggestions]
  workflow: quick scan → identify bottlenecks → deep analysis → optimization suggestions
  fixes: [commands/hardware/hardware-profilers/hardware-profile.md, commands/optimisation/large-files.md]

Disk health status (Disk Health):
  keywords: [disk health, SMART, bad sectors, hard disk failure]
  workflow: disk-smart-quick.md → disk-smart-deep.md if FAILED
  fixes: [commands/storage/health-checks/check-drive-health.md]

Hardware problems (Hardware Issues):
  keywords: [hardware, hardware, temperature, RAID, ECC, fan]
  workflow: hardware-health-quick.md → hardware-health-deep.md
  fixes: [commands/hardware/hardware-profilers/hardware-profile.md]

Time problems (Time Issues):
  keywords: [time, NTP, clock, clock is wrong, Kerberos]
  workflow: time-sync.md quick → deep analysis if not synchronized
  fixes: []  # time-sync.md itself contains the repair steps

SSH login problems (SSH Login Issues):
  keywords: [SSH, ssh login, cannot log in, login failed, can't login, login failed, connection refused, cannot connect]
  workflow: |
    Use cvm-self-diagnosis-repair.md → diagnose the SSH service, firewall, disk, memory
    Repair after user confirmation: restart services, fix configuration, open the firewall
  fixes: [references/cvm-self-diagnosis-repair.md]

Diagnosis statistics (Diagnosis Stats):
  keywords: [stats, diagnosis stats, stats, statistics, diagnosis report, past diagnoses, diagnosis history, diagnosis trend, diagnosis report, problem rate, diagnosis count]
  workflow: |
    Run: bash scripts/analyze_stats.sh
    Supported parameters:
      --today     today's data only
      --last Nd   the last N days (e.g. --last 7d)
      --json      output JSON (for programmatic consumption)
    If the user asks about a specific time range → add the corresponding parameter
    If the user asks for an overview/summary → add no parameter (full data)
  fixes: []

Cluster management (Cluster Management):
  keywords: [cluster, cluster, all CVMs, all nodes, fleet, batch check, multiple servers, inspection, node, health inspection, cluster health, cvm cluster, node status]
  workflow: |
    Precondition: all tccli commands in this scenario are executed through the tencentcloud-infra skill;
          you must confirm that this skill is already loaded in the current session and that the OAuth credential is valid.

    Routing decisions:

    1. No cluster config (MEMORY.md has no cluster_config section) → first-time configuration guidance
       Read references/cluster-discovery.md and show the user the following guidance text:
       ─────────────────────────────────────────────────────────
       I need to know which CVM instances to manage. Please choose a configuration method:

       1. Tag filter (recommended): batch-select by service tag, e.g. Service=order-api
       2. Specify instance IDs: enter ins-xxx,ins-yyy,ins-zzz directly
       3. Full scan: all instances in the current region (⚠️ be careful with large accounts)

       Please tell me:
       - Which method do you choose?
       - Which region are the instances in (e.g. ap-guangzhou)?
       - The corresponding tag key/value, or the instance ID list?
       ─────────────────────────────────────────────────────────
       After receiving the reply, run DescribeInstances through tencentcloud-infra and show the results for the user to confirm;
       once confirmed, write the cluster_config section into MEMORY.md.

    2. Config exists and the user wants a health check:
       → read references/cluster-quick-check.md (3-layer snapshot, about 30 seconds)
       → read references/cluster-health-score.md (generate a scoring report)

    3. An anomaly is found and the user wants deep analysis:
       → read references/cluster-deep-analysis.md (choose the TAT command by anomaly type)

    4. The user wants a repair:
       → read references/cluster-remediation.md (risk-gated, serial execution)

    See references/skill-collaboration-tencentcloud.md for the collaboration protocol
  fixes: [references/cluster-remediation.md]
  risk_level: 🟡~🔴 (depends on the specific operation; read the risk level in cluster-remediation.md)

```

### Tier 2: Extended Scenarios

**If Tier 1 did not match**:
1. Read `references/00-scenario-index.md` (60+ professional scenarios)
2. Search the user's keywords (exact match → substring match → related-term match)
3. If matched → execute the workflow | if not matched → run the quick scan script (generic health check)

---

## 🔧 Usage Workflow

1. **Parse the user request** → extract keywords and intent
2. **Match a scenario** → try Tier 1 first, fall back to Tier 2 if unmatched
3. **Run the quick check** (for general problems) → get the status of each component
4. **Run deep analysis** (on demand):
   - **1 component flagged** → use single-component deep analysis (cpu/memory/disk/network)
   - **2+ components flagged** → use combined deep analysis (correlation analysis)
   - **All OK but slow** → review the combined decision tree
5. **Present the results** → summary + root cause + recommendations
6. **Offer a repair plan** → if the user wants to repair:
   - Consult the `fixes` of the matched scenario (Tier 1) or `Commands` (Tier 2)
   - Read the relevant `commands/*.md` files
   - **Check the risk level** (see the "Risk Management" section below)
   - Present an action plan with risk indicators
   - **🟢 Low risk** (read-only): execute directly
   - **🟡 Medium risk** (service restart, cleanup): ask the user to confirm
   - **🔴 High risk** (config change, package install): requires explicit confirmation and displaying an impact warning

---

## 🔒 Risk Management

**Risk levels**:

```yaml
🟢 Low risk (automatic execution):
  - Read-only diagnosis: top, ps, df, free, netstat, journalctl
  - Does not change system state
  
🟡 Medium risk (execute after asking):
  - Service restart: systemctl restart, launchctl restart
  - Log rotation, cache cleanup
  - Temporary file deletion (from /tmp, /var/tmp)
  
🔴 High risk (explicit confirmation + display impact):
  - Configuration file changes: /etc/sysctl.conf, sshd_config, firewall rules
  - Package install/uninstall: apt install, yum remove
  - Disk operations: file system repair, partition changes
  - Process termination: kill -9
```

**Confirmation template** (medium/high risk):
```
⚠️ Risk level: [🟡 Medium risk / 🔴 High risk]
Operation: [specific operation]
Impact: [services/features that may be affected]
Reversible: [yes/no]

Continue? (yes/no)
```

---

## 🚨 Error Handling

**Reference file not found**:
- List the available files: `list_dir("references/")`
- Fall back to basic checks (ps, top, free)
- Notify the user: "advanced diagnosis unavailable"

**Command execution failed** (tool unavailable):
- Try an alternative command (for example, use vmstat instead of iostat)
- Skip that check and continue
- Note in the report: "tool X is unavailable; check Y was skipped"

**Cross-platform compatibility**: see the OS detection and command table in the "Cross-Platform Command Selection" section

---

## 📋 Quick Reference

**Decision logic**: see the "Quick/Deep Diagnosis Workflow" section above

**Quick modules** (commands/): `*-quick.md` files for 10-second triage  
**Deep modules** (commands/): `*-deep.md` files for 20-60 second analysis  
**Repair plans** (system-health/): repair playbooks

---

## 🌐 Cross-Platform Command Selection

**Always detect the operating system before running a command**

**Complete command table**: see `references/00-scenario-index.md`

**Quick reference** (most commonly used):
- Memory: Linux `free -h` | macOS `vm_stat` | Windows `wmic OS get TotalVisibleMemorySize`
- CPU: Linux `top -b -n 1` | macOS `top -l 1` | Windows `Get-Process | Sort CPU -Desc`
- Disk: Linux/macOS `df -h` | Windows `wmic logicaldisk get caption,size,freespace`

---

## 🔗 Extended Resources

**When Tier 1 does not match**:

```yaml
00-scenario-index.md:
  60+ professional scenarios across 20 categories
  Search the user's keywords and execute the matching workflow
  
commands/ directory:
  126 commands referenced by the scenarios
  Each command file contains Linux/macOS/Windows platform-specific command tables
```

---

## 📚 Reference Files

All diagnosis reference files live in the `references/` directory:

### Quick Modules (fast triage)

```yaml
Quick scan script: all-in-one health check (3 seconds, Windows/Linux/macOS)
  - scripts/quick_scan.ps1: Windows PowerShell version
  - scripts/quick_scan.sh: Linux/macOS bash version
resource-saturation-quick.md: CPU/memory/disk/network reference (fallback, 10 seconds)
system-logs-quick.md: kernel/OOM/file system/auth/service errors (10 seconds)
disk-smart-quick.md: disk health check (10 seconds)
hardware-health-quick.md: CPU temperature/memory/RAID/battery (10 seconds)
time-sync.md: NTP status check (5 seconds)
```

### Cluster Diagnosis Scripts (TAT remote execution)

The following scripts **run on the remote CVM**; the Agent base64-encodes them locally and passes them in through TAT `RunCommand --Content`.
For the encoding steps, see `references/skill-collaboration-tencentcloud.md` (⚡ script-first path).

```yaml
scripts/cluster_os_snapshot.sh:
  Purpose: Layer 2B OS snapshot, outputs a single line of KEY=VALUE for cluster_score.sh to score
  Timeout: 30s

scripts/cluster_deep_cpu.sh:
  Purpose: CPU deep analysis (top consumers, load details, cgroup throttling, IO wait)
  Timeout: 60s

scripts/cluster_deep_memory.sh:
  Purpose: memory deep analysis (top consumers, meminfo, OOM history, swap usage)
  Timeout: 60s

scripts/cluster_deep_disk.sh:
  Purpose: disk deep analysis (usage, inode, large files ≥500MB, IO stats, logrotate status)
  Timeout: 90s

scripts/cluster_deep_ssh.sh:
  Purpose: SSH deep analysis (sshd service status, listening ports, recent logs, key config lines, failure records)
  Timeout: 30s

scripts/cluster_deep_network.sh:
  Purpose: network deep analysis (connection summary, state counts, interface stats, errors, DNS resolution test)
  Timeout: 30s
```

### Deep Modules (root cause analysis)

```yaml
Resource saturation:
  - resource-saturation-deep-cpu.md
  - resource-saturation-deep-memory.md
  - resource-saturation-deep-disk.md
  - resource-saturation-deep-network.md
  - resource-saturation-deep-combined.md (multi-component correlation analysis)
  
System logs:
  - system-logs-deep-kernel.md
  - system-logs-deep-oom.md
  - system-logs-deep-fs.md
  - system-logs-deep-auth.md
  - system-logs-deep-service.md
  
Hardware:
  - disk-smart-deep.md
  - hardware-health-deep.md
```

---

## 🤝 Skill Collaboration

### Collaboration with the `tencentcloud-infra` Skill (cluster management)

This skill is deeply integrated with the **tencentcloud-infra** skill to support Tencent Cloud CVM cluster-level diagnosis and management.

**Trigger words:** cluster, cluster, all CVMs, all nodes, fleet, batch check, multiple servers

**Cluster management workflow (about 35 seconds):**

```yaml
1. Check whether MEMORY.md has cluster_config
   → No: read references/cluster-discovery.md and guide the user through cluster configuration
   → Yes (< 1 hour): use the cached node list directly

2. Read references/cluster-quick-check.md and execute the 3-layer snapshot:
   - Layer 1: call DescribeInstances through tencentcloud-infra
   - Layer 2A: call GetMonitorData through tencentcloud-infra (cloud-side metrics)
   - Layer 2B (⚡ script-first): encode scripts/cluster_os_snapshot.sh locally → call TAT RunCommand through tencentcloud-infra
     When the script does not exist, fall back to the inline commands in cluster-quick-check.md

3. Read references/cluster-health-score.md, compute the score and generate the report

4. If there are abnormal nodes, ask whether to perform deep analysis
   → Yes: read references/cluster-deep-analysis.md

5. If a repair is needed (restart a node/service), read references/cluster-remediation.md
```

**All cloud API operations are executed by the tencentcloud-infra skill; see:**
`references/skill-collaboration-tencentcloud.md`

---

### Coordination with the `health-check` Skill

**Scope division**:
- **CVM Doctor** → system **performance** diagnosis (CPU/memory/disk/network saturation), plus cluster node diagnosis
- **Health Check** → LightClaw **platform** health (security audit, configuration, logs, dependencies)

**When to cross-reference**:

1. **CVM Doctor detects a LightClaw process anomaly**:
   ```
   If the abnormal process name contains "lightclaw" or "uvicorn":
     → suggest that the user run health-check for platform-specific diagnosis
   ```

2. **The user says the generic "check the system"**:
   ```
   Priority: CVM Doctor (quick mode)
   If everything is OK → optional suggestion: "Performance is healthy. Do you want to check the LightClaw platform?"
   ```

3. **A host environment problem is found**:
   ```
   If disk space < 10% or system uptime > 365 days:
     → CVM Doctor provides detailed disk/resource analysis
     → Health Check reports it as a host environment risk factor
   ```

**Cross-reference template**:
```markdown
💡 A problem involving a LightClaw platform component was detected.
   Suggest running a platform health check:
   
   User: "self-check" or "health check" (triggers the health-check skill)
```

---

**Last updated**: 2026-04-22
**Version**: 3.3 (added Patrol periodic inspection + Dashboard)
**Compatibility**: Linux (complete), macOS (complete), Windows (basic)
