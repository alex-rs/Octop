# AI Quick Scenario Matching Guide

> **Purpose**: let the AI quickly identify the user's problem and choose the correct diagnosis path
> **Decision time**: < 3 seconds

---

## 🎯 One-Line Matching Rule

**See a user keyword → match the scenario immediately → run Quick Mode → decide on Deep from the results**

---

## 🔥 Top 10 High-Frequency Scenarios (covering 80% of problems)

### 1. Slow/laggy system ⭐⭐⭐⭐⭐
**Keywords**: slow, laggy, lag, slow, sluggish, slow response
```bash
bash references/resource-saturation.md
# Quick 10s → if anomalies → Deep --focus <component>
```

### 2. High CPU ⭐⭐⭐⭐⭐
**Keywords**: CPU, CPU 100%, fans spinning hard, high CPU
```bash
bash references/resource-saturation.md --mode deep --focus cpu
```

### 3. Insufficient memory ⭐⭐⭐⭐⭐
**Keywords**: memory, memory, OOM, swap, low memory
```bash
bash references/resource-saturation.md --mode deep --focus memory
```

### 4. Disk space full ⭐⭐⭐⭐⭐
**Keywords**: disk full, disk full, no space, out of space
```bash
df -h && du -sh /* | sort -rh | head -20
# Then: commands/optimisation/large-files.md
```

### 5. Slow disk/high I/O ⭐⭐⭐⭐⭐
**Keywords**: slow disk, I/O wait, disk slow, slow reads/writes
```bash
bash references/resource-saturation.md --mode deep --focus disk
bash references/disk-smart.md
```

### 6. Slow network ⭐⭐⭐⭐⭐
**Keywords**: slow network, slow internet, high ping, network slow
```bash
bash references/resource-saturation.md --mode quick
# Then: commands/network/diagnose-network-issues.md
```

### 7. Health check ⭐⭐⭐⭐⭐
**Keywords**: check, health, health, check, status
```bash
# Full Quick scan
bash references/resource-saturation.md --mode quick
bash references/system-logs.md --mode quick
bash references/disk-smart.md --mode quick
# If anomalies → the corresponding Deep
```

### 8. Crash/reboot ⭐⭐⭐⭐⭐
**Keywords**: crash, crash, reboot, reboot, panic
```bash
bash references/system-logs.md --mode deep --focus crash
# Then: commands/debugging/diagnose-crash.md
```

### 9. Error logs ⭐⭐⭐⭐⭐
**Keywords**: error, error, error message, exception, exception
```bash
bash references/system-logs.md --mode quick
# If there are many errors → Deep analysis
```

### 10. Hardware problems ⭐⭐⭐⭐⭐
**Keywords**: hardware, temperature, sensors, hardware, hot
```bash
bash references/hardware-other.md
# SMART check: bash references/disk-smart.md
```

---

## 🎯 AI 3-Second Decision Flow

```
Step 1: Extract keywords
  User: "the server is very slow" → keywords: ["slow"]

Step 2: Match a scenario
  "slow" → scenario #1 (slow/laggy system)

Step 3: Run Quick
  bash resource-saturation.md (10 seconds)

Step 4: Decide on Deep
  Quick result: Memory WARNING
  → run: bash resource-saturation.md --mode deep --focus memory (20 seconds)

Step 5: Report
  Root cause: Java memory leak
  Fix: restart Java + add memory
```

---

## 🔄 Quick/Deep Decision Rules

### When to Run Deep?

| Quick result | User intent | Decision |
|-----------|---------|------|
| **CRITICAL** | any | ✅ Automatic Deep |
| **WARNING** | contains "slow/laggy/troubleshoot" | ✅ Automatic Deep |
| **WARNING** | only "check" | ❓ Ask the user |
| **OK** | any | ❌ No Deep needed |

### Choosing focus During Deep

- Single anomaly → `--focus <component>`
- Multiple anomalies → `--focus` one by one, do not use `--focus all`
- User explicitly specifies → go straight to Deep on that component

---

## 📊 Where the Complete Scenario Index Lives

**Detailed index**: `references/00-scenario-index.md`
- 60+ scenario categories
- 126 command mappings
- 5 reference mappings
- Complete decision algorithm

---

## 🚀 Usage Examples

### Example 1: "The server is slow"
```
1. Match → scenario #1
2. Quick: resource-saturation.md (10s)
3. Result: CPU OK, Memory WARNING, Disk OK
4. Deep: --mode deep --focus memory (20s)
5. Report: MySQL is using 8GB; consider optimizing the queries
```

### Example 2: "The disk is broken"
```
1. Match → scenario #10 (hardware) → #5.2 (disk failure)
2. Quick: disk-smart.md --mode quick (5s)
3. Result: SMART CRITICAL
4. Deep: disk-smart.md --mode deep (15s)
5. Report: Reallocated sectors 100+; back up immediately
```

### Example 3: "Check the system"
```
1. Match → scenario #7 (health check)
2. Batch Quick:
   - resource-saturation.md (10s)
   - system-logs.md (5s)
   - disk-smart.md (5s)
3. Result: everything OK
4. Report: the system is healthy, no Deep needed
```

---

## ⚡ Performance Tips

- **Quick first**: always run Quick first
- **Deep on demand**: run Deep only when Quick finds an anomaly
- **Token optimization**: Quick 200 tokens, Deep 500-700 tokens
- **Time control**: Quick 10s, Deep 20-60s
- **Batch Quick**: a health check can run several Quick checks in parallel

---

**Quick reference version**: 1.0
**Full index**: references/00-scenario-index.md
**Last updated**: 2026-03-24
