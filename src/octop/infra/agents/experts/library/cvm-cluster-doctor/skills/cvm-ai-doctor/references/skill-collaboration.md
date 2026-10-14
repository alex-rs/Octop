# Skill Collaboration Guide

**Last Updated**: 2026-03-27

---

## Overview

This document defines how `cvm-doctor` collaborates with other skills, primarily `health-check`.

---

## 🩺 CVM Doctor ↔ Health Check

### Scope Division

| Aspect | **CVM Doctor** | **Health Check** |
|--------|----------------|------------------|
| **Target** | User's **CVM/VM/host** system | **LightClaw platform** itself |
| **Focus** | Performance bottlenecks | Security + configuration health |
| **Checks** | CPU/Memory/Disk/Network saturation | Process vitals, logs, auth, config, dependencies |
| **Trigger** | "slow/laggy/high CPU/disk full/performance problem" | "self-check/health check/security check/LightClaw status" |
| **Output** | Performance analysis + optimization | Security score + health report |

---

## 🔀 Cross-reference Scenarios

### Scenario 1: User says "check the system" (ambiguous)

**Decision tree**:

```yaml
if user_mentions("LightClaw" or "self-check" or "health check" or "security"):
  → Use health-check skill
  
elif user_mentions("slow" or "laggy" or "CPU" or "performance"):
  → Use cvm-doctor skill
  
else:
  # Generic "check system" - prioritize performance
  → Execute cvm-doctor (Quick Mode)
  
  if all_components_ok:
    → Report: "✅ System performance is healthy."
    → Suggest: "Need LightClaw platform security audit? (say 'self-check' or 'health check')"
  
  else:
    → Proceed to Deep Mode for flagged components
```

---

### Scenario 2: CVM Doctor detects LightClaw process anomaly

**Trigger condition**:
- Top CPU/Memory process name contains: `lightclaw` / `uvicorn` / `python.*lightclaw`

**Action in CVM Doctor report**:

```markdown
## 🔬 Deep CPU Analysis

**Top CPU Process**: lightclaw-server (PID 12345, 87.3% CPU)

⚠️  **Platform Component Detected**: The abnormal process is a LightClaw platform service.

💡 **Recommended Next Step**:
   Run platform health check for detailed diagnostics:
   
   User: "self-check" or "LightClaw health check"
   
   This will analyze:
   - Process vitals and thread count
   - Recent error logs
   - Configuration issues
   - Dependency conflicts
```

---

### Scenario 3: Health Check detects host environment issues

**Trigger condition**:
- Disk free space < 10%
- System uptime > 365 days
- Python version < 3.8

**Action in Health Check report**:

```markdown
## 💾 Storage and Data Security — 3/10 ⚠️

**Issues**:
- Only 8% disk space remaining (24GB / 300GB)
- LightClaw log directory consuming 15GB

💡 **Recommend using CVM Doctor for detailed disk analysis**:
   
   User: "check disk" or "disk slow"
   
   CVM Doctor will provide:
   - Disk saturation analysis
   - Large file scan
   - I/O performance diagnosis
   - Cleanup recommendations
```

---

### Scenario 4: Both skills needed (multi-layered issue)

**Example**: User says "the system has been slow lately and keeps reporting errors"

**Workflow**:

1. **First**: CVM Doctor (Quick Mode)
   ```
   Checks: CPU/Memory/Disk/Network saturation
   Result: Memory WARNING (Swap in use)
   ```

2. **Second**: If LightClaw process is involved
   ```
   Check top memory process → lightclaw-server (1.2GB)
   ```

3. **Third**: Cross-reference to Health Check
   ```
   Suggest: "LightClaw process memory usage is abnormal; recommend running a 'health check' to look into:
   - Log errors (possible memory leak)
   - Configuration issues (heartbeat too frequent)
   - Dependency conflicts"
   ```

---

## 🎯 Implementation Checklist

### For CVM Doctor

- [x] Update SKILL.md trigger words to avoid "self-check/health check/security check"
- [x] Add cross-reference logic in Quick Mode output format
- [x] Add collaboration section in SKILL.md
- [x] Create this skill-collaboration.md reference

### For Health Check (if editing)

- [ ] Add note: "For system performance issues (slow/laggy/high CPU), use `cvm-doctor` skill"
- [ ] In host environment section, suggest CVM Doctor for disk/resource deep dive

---

## 📝 Cross-reference Templates

### CVM Doctor → Health Check

```markdown
💡 **LightClaw Platform Component Detected**

The issue involves a LightClaw service. For platform-specific diagnostics:

**Next Step**: Run health check
- User says: "self-check" or "LightClaw health check"
- Checks: Process vitals, logs, config, security
```

### Health Check → CVM Doctor

```markdown
💡 **Host Machine Resource Issue**

Abnormal host machine {disk/memory/CPU} resource usage detected. Recommend using CVM Doctor for a detailed analysis:

**Next Step**: say "check {disk/memory/CPU}" or "system performance diagnosis"
- Checks: resource saturation, I/O performance, process analysis
```

---

## 🌩️ CVM Doctor ↔ Tencent Cloud Infra

### Applicable Scenarios

When the user says "check the cluster"/"all CVMs"/"batch diagnostics"/"restart a cloud server",
cvm-doctor and tencentcloud-infra must work together to complete the task.

### Division of Responsibilities

| Responsibility | **CVM Doctor** | **tencentcloud-infra** |
|------|--------------|----------------------|
| Node discovery (API) | ❌ | ✅ DescribeInstances |
| Cloud monitoring metrics | ❌ | ✅ GetMonitorData |
| Remote OS command execution | ❌ | ✅ TAT RunCommand |
| OS data diagnostic analysis | ✅ | ❌ |
| Cross-node correlation analysis | ✅ | ❌ |
| Instance lifecycle operations | ❌ | ✅ Reboot/Stop/Start |
| Cluster health scoring | ✅ | ❌ |

### Quick Decision Rules

```yaml
if user_mentions("cluster" or "clusters" or "all CVMs" or "all nodes" or "fleet" or "batch"):
  → Read references/cluster-quick-check.md
  → Perform node discovery and TAT snapshots through tencentcloud-infra
  → Generate a scoring report using references/cluster-health-score.md

elif user_mentions("restart instance" or "restart cloud server" or "ins-" or "start/stop"):
  → Read references/cluster-remediation.md
  → Perform instance lifecycle operations through tencentcloud-infra (risk confirmation required)

else:
  → Continue with the existing single-host diagnostic flow; tencentcloud-infra is not needed
```

### Full Collaboration Protocol

All API call details (TAT execution format, data structures, degradation mode) are documented in:
`references/skill-collaboration-tencentcloud.md`

---

**Last Updated**: 2026-05-08
