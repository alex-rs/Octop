---
name: standalone-checks
description: System diagnostics with intelligent Quick/Deep mode. Diagnose performance issues (slow, lag, high CPU, memory problems, disk issues) on local systems. Works on servers, PCs, VMs, containers - Linux/macOS/Windows.
metadata: {"openclaw": {"requires": {"bins": ["bash", "ps"]}, "os": ["linux", "darwin", "windows"]}}
---

# Standalone Checks Skill

**Purpose**: Diagnose system performance issues with intelligent Quick (10s triage) → Deep (20-60s analysis) workflow.

**Supported Systems**: Local servers, personal computers (Mac/Windows/Linux), VMs, containers.

---

## 🎯 When to Use This Skill

### ✅ Use When User Mentions

**Performance issues**:
- "slow" / "laggy" / "slow" / "lag" / "sluggish" / "slow response"
- "high CPU" / "cpu 100%" / "high CPU"
- "out of memory" / "memory" / "OOM" / "swap"
- "disk full" / "disk full" / "slow disk" / "I/O slow"
- "check the system" / "health check" / "health check"

**Device types** (all supported):
- 🖥️ Servers: local server, bare metal
- 💻 Personal computers: laptop, desktop, Mac, PC
- 🐳 Containers: Docker, Kubernetes pod
- 📦 Virtual machines: VM, VPS

**OS support**: Linux (Ubuntu/CentOS/Debian), macOS, Windows (partial)

### ❌ Do NOT Use When

- User mentions **remote servers** or **IP addresses** → Use `remote-executor` skill instead
- Pure **software installation** queries → Package manager skills
- **Application-specific** issues → Use application-specific skills first

---

## 🚀 Quick/Deep Workflow

This skill uses a **2-stage diagnostic approach**:

```
Step 1: Quick Mode (10s)
  → Fast scan across all components
  → Returns: OK / WARNING / CRITICAL per component
  
Step 2: Deep Mode (20-60s, conditional)
  → Only analyze components flagged in Quick
  → Root cause analysis + recommendations
```

### How It Works

```yaml
Example: User says "the server is slow"

Stage 1 - Quick Triage:
  Read: references/resource-saturation-quick.md
  Execute: Quick checks (10s)
  Result: CPU=CRITICAL, Memory=OK, Disk=OK, Network=OK
  
Stage 2 - Targeted Deep Analysis:
  Read: references/resource-saturation-deep-cpu.md (only!)
  Execute: Deep CPU analysis (30s)
  Output: Root cause + fix recommendations
  
Efficiency: Only loaded 2 files instead of 5
```

---

## 🔍 Scene Matching (Two-Tier Strategy)

### Tier 1: Core Scenarios (80% coverage)

Match these first - handle most common issues:

```yaml
Slow/laggy system (System Slow):
  keywords: [slow, laggy, slow, lag, slow response]
  workflow: Quick scan → Deep on flagged components
  
High CPU usage (High CPU):
  keywords: [CPU, high cpu, cpu 100%, CPU maxed]
  workflow: Skip Quick → Direct to resource-saturation-deep-cpu.md
  
Insufficient memory (Low Memory):
  keywords: [memory, memory, OOM, swap, low memory]
  workflow: Skip Quick → Direct to resource-saturation-deep-memory.md
  
Disk problems (Disk Issues):
  keywords: [disk, disk, I/O, slow io, disk full]
  workflow: Skip Quick → Direct to resource-saturation-deep-disk.md
  
Network problems (Network Issues):
  keywords: [network, network, NIC, packet loss]
  workflow: Skip Quick → Direct to resource-saturation-deep-network.md
  
Health inspection (Health Check):
  keywords: [check, health, health, check, diagnosis]
  workflow: Quick scan only (stop if all OK)
  
System crash/errors (System Crash):
  keywords: [crash, crash, error, error, reboot, reboot]
  workflow: Quick log scan → Deep on error categories
  
Disk health status (Disk Health):
  keywords: [disk health, SMART, bad sectors, hard disk failure]
  workflow: disk-smart-quick.md → disk-smart-deep.md if FAILED
  
Hardware problems (Hardware Issues):
  keywords: [hardware, hardware, temperature, RAID, ECC, fan]
  workflow: hardware-health-quick.md → hardware-health-deep.md
  
Time problems (Time Issues):
  keywords: [time, NTP, clock, clock is wrong, Kerberos]
  workflow: time-sync.md Quick → Deep if not synced
```

### Tier 2: Extended Scenarios (for non-match)

**If no Tier 1 match**, use fallback strategy:

```yaml
Step 1: Read Extended Scenario Index
  action: read_file("references/00-scenario-index.md")
  purpose: Search 60+ specialized scenarios
  
Step 2: Match keywords in index
  examples:
    - "slow Docker container" → Category: Container Issues
    - "Python environment broken" → Category: Environment Issues  
    - "Bluetooth not working" → Category: Hardware Peripherals
    
Step 3: Execute matched workflow
  if found:
    Follow commands/reference from 00-scenario-index.md
  else:
    Default: Run basic health check (Quick mode)
```

**Example Fallback Execution**:
```text
User: "RAID array shows degraded"

Step 1: Check Tier 1 scenarios
  → Match "hardware problems" (keyword: RAID) ✅
  → Workflow: hardware-health-quick.md → hardware-health-deep.md
  
Step 2: Execute
  → Quick scan detects RAID=CRITICAL
  → Load hardware-health-deep.md
  → Section: RAID diagnostics
```

### Decision Rules

**Rule 1: Determine mode from user intent**
- General issue ("slow", "laggy") → Quick first
- Specific component ("high CPU", "low memory") → Skip to Deep
- Health check → Quick only
- **No match** → Fallback to 00-scenario-index.md

**Rule 2: Conditional Deep loading**
```python
quick_results = execute_quick_mode()

if quick_results["cpu"] in ["WARNING", "CRITICAL"]:
    load("resource-saturation-deep-cpu.md")
    
if quick_results["memory"] in ["WARNING", "CRITICAL"]:
    load("resource-saturation-deep-memory.md")
    
# Only load what's needed
```

---

## 📚 Reference Files

All diagnostic references are in `references/` directory:

### Quick Modules (Fast Triage)
```yaml
resource-saturation-quick.md:
  - 10s scan: CPU/Memory/Disk/Network
  - Returns: Status per component
  
system-logs-quick.md:
  - 10s scan: kernel/OOM/FS/auth/service errors
  - Returns: Error counts per category
  
disk-smart-quick.md:
  - 10s scan: Disk health (PASSED/FAILED)
  
hardware-health-quick.md:
  - 10s scan: CPU temp/Memory/RAID/Battery
  
time-sync.md:
  - 5s check: NTP status and sync
```

### Deep Modules (Root Cause Analysis)
```yaml
Resource Saturation Deep:
  - resource-saturation-deep-cpu.md
  - resource-saturation-deep-memory.md
  - resource-saturation-deep-disk.md
  - resource-saturation-deep-network.md
  
System Logs Deep:
  - system-logs-deep-kernel.md
  - system-logs-deep-oom.md
  - system-logs-deep-fs.md
  - system-logs-deep-auth.md
  - system-logs-deep-service.md
  
Hardware Deep:
  - disk-smart-deep.md
  - hardware-health-deep.md
```

### When to Use Each

| User Problem | Quick File | Conditional Deep Files |
|-------------|-----------|----------------------|
| Server is slow | resource-saturation-quick.md | Based on Quick results |
| High CPU | (skip) | resource-saturation-deep-cpu.md |
| Low memory | (skip) | resource-saturation-deep-memory.md |
| Health check | resource-saturation-quick.md + system-logs-quick.md | None (if all OK) |
| System crash | system-logs-quick.md | Based on error categories |
| Disk failure | (skip) | disk-smart-deep.md |

---

## 🔧 Usage Workflow

### Step 1: Parse User Request

Extract keywords and intent:
```python
user_query = "the server is very slow, not sure why"
keywords = ["slow"]
intent = "troubleshoot"
component = None  # General issue
```

### Step 2: Match Scenario (Two-Tier)

```python
# Try Tier 1 first (10 core scenarios)
tier1_match = match_keywords(user_query, tier1_scenarios)

if tier1_match:
    # 80% of cases end here
    mode = tier1_match.workflow
    references = tier1_match.files
else:
    # Fallback to Tier 2 (60+ extended scenarios)
    read_file("references/00-scenario-index.md")
    tier2_match = search_keywords(user_query, scenario_index)
    
    if tier2_match:
        mode = tier2_match.workflow
        references = tier2_match.files
    else:
        # Default: basic health check
        mode = "quick_only"
        references = ["resource-saturation-quick.md", "system-logs-quick.md"]
```

### Step 3: Execute Quick (if needed)

```bash
# Read Quick reference
read_file("references/resource-saturation-quick.md")

# Execute Quick checks (commands from reference)
# Parse results: cpu_status, memory_status, disk_status, network_status
```

### Step 4: Conditional Deep Analysis

```python
if cpu_status in ["WARNING", "CRITICAL"]:
    read_file("references/resource-saturation-deep-cpu.md")
    execute_deep_cpu_analysis()
    
# Only load files for flagged components
```

### Step 5: Present Results

Format as structured report with:
- Summary of findings
- Root cause (if Deep executed)
- Recommended actions
- Commands to fix

---

## 🚨 Error Handling

### Common Issues

**1. Reference file not found**
```yaml
Action:
  - List available files: list_dir("references/")
  - Fall back to basic checks (ps, top, free)
  - Inform user: "Advanced diagnostics unavailable"
```

**2. Command execution failed**
```yaml
Cause: Tool not available (iostat, sensors, etc.)
Action:
  - Try alternative command (vmstat instead of iostat)
  - Skip that check and continue
  - Note in report: "Tool X unavailable, skipped check Y"
```

**3. Cross-platform compatibility**
```yaml
Strategy:
  - Check OS first: uname -s
  - Use platform-specific commands
  - Adapt thresholds per OS (e.g., macOS has different metrics)
```

---

## 💡 Best Practices

### For AI Agents

1. **Start with Quick mode** unless user specifies component
2. **Read only what you need** - Don't load all Deep modules
3. **Provide actionable output** - Commands user can run
4. **Handle missing tools gracefully** - Suggest alternatives
5. **Adapt to OS** - Commands differ on Linux/macOS/Windows

### Output Format

```yaml
Diagnosis Result Report

Problem: the system responds slowly

Quick check (10s):
  - CPU: 🔴 CRITICAL (95% usage)
  - Memory: ✅ OK (40% usage)
  - Disk: ✅ OK (I/O normal)
  - Network: ✅ OK (bandwidth normal)

Deep analysis - CPU:
  Root cause: process java (PID 1234) is using 90% CPU
  Duration: more than 2 hours
  Recommendations:
    1. Check the application logs: journalctl -u app-service
    2. Analyze the threads: jstack 1234
    3. If everything is normal, consider scaling up
```

---

## 🔗 Extended Documentation

### When to Use Fallback Resources

**Primary**: Use Tier 1 Core Scenarios (covers 80% cases)  
**Fallback**: Use these when Tier 1 doesn't match:

```yaml
00-scenario-index.md:
  when: No Tier 1 scenario matches user keywords
  contains: 60+ specialized scenarios in 20 categories
  action: Search for user's keywords in index, execute matched workflow
  
commands/ directory:
  when: Need specific command reference (referenced by scenario)
  contains: 126 commands across 10+ categories
  
_cross_platform_adapters.sh:
  when: Running on macOS or Windows
  provides: Unified command interface for cross-platform compatibility
```

**Fallback Example**:
```text
User: "MySQL primary-replica replication lag"

Tier 1 Match: None (specialized database issue)
  ↓
Read: references/00-scenario-index.md
  ↓
Search: "MySQL", "primary-replica", "replication"
  ↓
Found: Category "Database Issues" → MySQL replication diagnostics
  ↓
Execute: Commands from matched scenario
```

---

## 📊 Success Metrics

**Accuracy**: > 90% correct root cause identification  
**Efficiency**: Single skill invocation solves the problem  
**User Satisfaction**: User doesn't need to run multiple diagnostics

---

**Last Updated**: 2026-03-24  
**Version**: 2.2 (Modular Quick/Deep architecture)  
**Compatibility**: Linux (full), macOS (full), Windows (basic)
