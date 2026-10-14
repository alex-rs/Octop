# Scenario Decision Guide

**Purpose**: Extended scenario library with 60+ diagnostic scenarios.  
**Usage**: Fallback reference when SKILL.md's built-in scenarios don't match.

---

## How to Use This Guide

1. **Try SKILL.md first** - It covers 80% of common cases
2. **If no match**, search this file for relevant keywords
3. **Follow the workflow** specified for that scenario

---

## Performance Issues

### Server Slow/Lagging (System Slow)
```yaml
Keywords: [slow, lag, sluggish, slow response, latency]
Workflow:
  step1: Read resource-saturation-quick.md
  step2: Execute Quick checks (10s)
  step3: Based on results, conditionally read Deep modules:
    - If CPU = WARNING/CRITICAL → resource-saturation-deep-cpu.md
    - If Memory = WARNING/CRITICAL → resource-saturation-deep-memory.md
    - If Disk = WARNING/CRITICAL → resource-saturation-deep-disk.md
    - If Network = WARNING/CRITICAL → resource-saturation-deep-network.md
Reason: Quick triage identifies bottleneck, then Deep analysis on specific component
```

### High CPU
```yaml
Keywords: [CPU, high cpu, CPU 100%, process hung]
Workflow:
  step1: Skip Quick, go directly to:
    - resource-saturation-deep-cpu.md
Reason: User already identified CPU as bottleneck
```

### Memory Issues
```yaml
Keywords: [memory, OOM, swap, memory full, out of memory]
Workflow:
  step1: Skip Quick if issue is clear
  step2: Read resource-saturation-deep-memory.md
Reason: Focus on memory component only
```

### Disk Issues
```yaml
Keywords: [disk, disk full, disk slow, I/O slow]
Workflow:
  step1: Determine if "full" or "slow"
  step2a: If "full" → Direct commands (du, df)
  step2b: If "slow" → resource-saturation-quick.md, then resource-saturation-deep-disk.md
Reason: Disk full needs space check, disk slow needs I/O analysis
```

### Network Slow (Network Issues)
```yaml
Keywords: [network, network slow, packet loss]
Workflow:
  step1: Read resource-saturation-quick.md
  step2: If network issue confirmed → resource-saturation-deep-network.md
Reason: Network diagnostics need baseline first
```

---

## System Errors

### Health Check
```yaml
Keywords: [check, health, health check]
Workflow:
  step1: Read resource-saturation-quick.md
  step2: Read system-logs-quick.md
  step3: If all OK → Stop (no Deep needed)
Reason: Health check only needs Quick scan
```

### Crash/Errors
```yaml
Keywords: [crash, error, exception, killed, panic]
Workflow:
  step1: Read system-logs-quick.md
  step2: Based on results, conditionally read:
    - If kernel errors → system-logs-deep-kernel.md
    - If OOM events → system-logs-deep-oom.md
    - If FS errors → system-logs-deep-fs.md
    - If auth failures → system-logs-deep-auth.md
    - If service failures → system-logs-deep-service.md
Reason: Quick error count identifies problem categories, then Deep analysis
```

### OOM Issues (OOM Killer)
```yaml
Keywords: [OOM, Out of Memory, killed process, oom killer]
Workflow:
  step1: Skip system-logs-quick.md
  step2: Read system-logs-deep-oom.md directly
Reason: OOM explicitly mentioned, direct to Deep analysis
```

### Kernel Panic/Crash
```yaml
Keywords: [kernel panic, kernel crash, kernel oops]
Workflow:
  step1: Skip Quick
  step2: Read system-logs-deep-kernel.md
Reason: Critical issue, immediate Deep analysis needed
```

### Auth Failures
```yaml
Keywords: [authentication, SSH, login failed, brute force]
Workflow:
  step1: Skip system-logs-quick.md
  step2: Read system-logs-deep-auth.md directly
Reason: Auth issues need immediate analysis
```

### Filesystem Errors
```yaml
Keywords: [filesystem, fs error, read-only, I/O error]
Workflow:
  step1: Skip Quick
  step2: Read system-logs-deep-fs.md
Reason: FS errors are critical, direct Deep analysis
```

### Service Failures
```yaml
Keywords: [service, systemd, service failed]
Workflow:
  step1: system-logs-quick.md (check if systemic)
  step2: If service-specific → system-logs-deep-service.md
Reason: Differentiate between systemic vs. single service issue
```

---

## Hardware Issues

### Disk Health
```yaml
Keywords: [disk health, SMART, bad sector]
Workflow:
  step1: Read disk-smart-quick.md (10s check)
  step2: If any disk = FAILED or UNKNOWN → disk-smart-deep.md
Reason: Quick health check sufficient if all PASSED
```

### Disk Failure
```yaml
Keywords: [disk failure, FAILED, disk failed]
Workflow:
  step1: Skip disk-smart-quick.md
  step2: Read disk-smart-deep.md directly
Reason: Explicit failure mentioned, detailed SMART analysis needed
```

### Hardware Issues
```yaml
Keywords: [hardware, temperature, hot, overheating]
Workflow:
  step1: Read hardware-health-quick.md
  step2: If issues found → hardware-health-deep.md
Reason: Quick hardware health scan across all components
```

### CPU Overheating
```yaml
Keywords: [CPU temperature, CPU overheating, CPU hot, throttling]
Workflow:
  step1: Skip Quick
  step2: Read hardware-health-deep.md (focus: CPU temperature)
Reason: Temperature issues need immediate deep analysis
```

### Memory Hardware Failure (Memory Hardware)
```yaml
Keywords: [memory error, ECC, memory hardware, bad memory]
Workflow:
  step1: Skip Quick
  step2: Read hardware-health-deep.md (focus: ECC errors)
Reason: Hardware memory errors need detailed analysis
```

### RAID Issues
```yaml
Keywords: [RAID, raid degraded, array, disk array]
Workflow:
  step1: Read hardware-health-quick.md
  step2: If RAID degraded → hardware-health-deep.md
Reason: RAID issues need component-level analysis
```

---

## Time & Clock

### Time Issues
```yaml
Keywords: [time, NTP, ntp, clock, wrong time]
Workflow:
  step1: Read time-sync.md (Quick section)
  step2: If not synced → time-sync.md (Deep section)
Reason: Quick NTP sync check, then Deep if issues
```

### Time Drift
```yaml
Keywords: [time drift, clock offset, Kerberos failure]
Workflow:
  step1: Skip Quick
  step2: Read time-sync.md (Deep section)
Reason: Time drift explicitly mentioned, immediate Deep analysis
```

### Kerberos Auth Failure (Kerberos Auth)
```yaml
Keywords: [Kerberos, kerberos failure, clock skew]
Workflow:
  step1: Read time-sync.md (check time first)
  step2: If time OK → system-logs-deep-auth.md
Reason: Kerberos failures often caused by time drift (>5s threshold)
```

---

## Low-Frequency Scenarios

### Slow Boot
```yaml
Keywords: [slow boot, boot time, systemd-analyze]
Workflow:
  - Run: systemd-analyze blame
  - Identify slow services
  - Check: system-logs-deep-service.md for service issues
```

### Zombie Processes
```yaml
Keywords: [zombie process, zombie, defunct, Z state]
Workflow:
  - Run: ps aux | grep defunct
  - Identify parent process
  - Check if parent is hung (resource-saturation-deep-cpu.md)
```

### High Load but Low CPU (High Load, Low CPU)
```yaml
Keywords: [load average high, cpu not high, high load low cpu]
Workflow:
  - Read: resource-saturation-quick.md
  - Focus on: Disk I/O wait, Network wait
  - Deep: resource-saturation-deep-disk.md or deep-network.md
Reason: High load with low CPU indicates I/O or network bottleneck
```

### Excessive Context Switches (High Context Switches)
```yaml
Keywords: [context switch, cs rate]
Workflow:
  - Read: resource-saturation-deep-cpu.md
  - Focus on: vmstat cs column, process scheduling
```

### File Descriptor Exhaustion
```yaml
Keywords: [too many open files, file descriptor, ulimit, fd limit]
Workflow:
  - Check: lsof -p <pid> | wc -l
  - Check: ulimit -n
  - Deep: system-logs-deep-service.md (if service-related)
```

---

## Usage Tips

### For AI Agents

1. **Start with SKILL.md** - Don't read this file unless needed
2. **Match keywords precisely** - Use exact keyword matching
3. **Follow workflow strictly** - Don't skip steps unless specified
4. **Combine scenarios** - Some issues need multiple checks

### When to Use This File

- ✅ Built-in scenarios in SKILL.md don't match
- ✅ User mentions specific technical terms (Kerberos, RAID, ECC)
- ✅ Low-frequency issues (zombie processes, fd exhaustion)
- ❌ Common issues (slow, high CPU, out of memory) - Use SKILL.md instead

---

**Last Updated**: 2026-03-24  
**Maintainer**: AI diagnostics team  
**Related**: See SKILL.md for core scenarios, commands/ for action commands
