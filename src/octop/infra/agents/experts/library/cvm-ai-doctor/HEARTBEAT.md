---
summary: "Heartbeat tasks — periodic health checks and proactive alerts"
read_when:
  - heartbeat polling
---

# Heartbeat Task List

## 1. Periodic health check

**Trigger:** once per hour (frequency configurable by the user)

**Steps:**

1. Run a quick system scan (3 seconds)
2. Check key metrics:
   - System load and CPU usage
   - Memory usage and swap usage
   - Disk space and inode usage
   - Network connectivity (DNS/external network)
   - Status of key services (SSH/systemd/docker)
   - Recent system error logs

3. If an anomaly is found, assess the severity:
   - 🔴 High risk (disk full, SSH down, system load > 2x CPU cores) → push immediately
   - 🟡 Warning (resource usage > threshold, service anomaly, ERROR in logs) → summarize and push
   - 🟢 Normal → do not push, only log it

4. Output format (push only when there is an anomaly):

```
[System Doctor Health Check YYYY-MM-DD HH:MM]

🔴 Critical issues (immediate action required)
- Root partition disk usage 96% (2.1GB remaining)
- SSH service is not running, port 22 unreachable

🟡 Early warnings
- System load 9.5 (4 CPU cores)
- Memory usage 88% (14GB / 16GB)

---
🔍 Run "system detailed diagnosis" for the complete report
```

---

## 2. Service availability monitoring

**Trigger:** once every 15 minutes (high-frequency scenario)

**Steps:**

1. Check the running status of key services:
   - SSH service status and port listening
   - systemd service manager status
   - Docker daemon (if installed)
   - cron scheduled task service

2. If any of the following is found, push immediately:
   - SSH service is not running or the port is unreachable
   - systemd service is in failed state
   - Docker daemon is abnormal

3. Push format:

```
⚠️ Service availability anomaly

Symptom: SSH service is not running, port 22 unreachable
Possible causes: service crash / misconfiguration / firewall blocking

🛠️ Quick troubleshooting:
1. Check service status: sudo systemctl status sshd
2. View service logs: sudo journalctl -u sshd -n 50
3. Check port listening: ss -tlnp | grep :22

Reply "diagnose SSH service" for in-depth diagnosis
```

---

## 3. Disk space monitoring

**Trigger:** once per week (Sunday evening)

**Steps:**

1. Analyze disk usage over the past week:
   - Space usage and growth trend of each partition
   - inode usage
   - Large file and directory scan (> 1GB)
   - Cumulative size of log files

2. Identify optimization opportunities:
   - Whether old logs can be cleaned up
   - Whether temporary files need cleaning
   - Whether the package cache needs cleaning
   - Whether any abnormally large files take up space

3. Provide optimization suggestions:

```
[System Doctor Weekly Report YYYY-MM-DD]

💾 Disk space optimization suggestions

Root partition (/):
- Current usage: 78% (198GB / 256GB)
- Growth this week: +12GB
- Suggestion: clean the package cache to free about 3.5GB

Log files:
- Cumulative size of /var/log: 2.8GB
- Suggestion: clean logs older than 30 days and enable logrotate

Large file scan:
- /tmp/backup.tar.gz: 5.2GB (created 15 days ago)
- Suggestion: confirm whether it is still needed; consider archiving or deleting it

---
📊 Disk usage statistics this week
- Total capacity: 256GB
- Used: 198GB (78%)
- Added this week: +12GB
- Estimated reclaimable: 8.7GB
```

---

## 4. Memory maintenance

**Trigger:** once per week (during the weekend heartbeat)

**Steps:**

1. Review recent diagnosis history in `memory/YYYY-MM-DD.md`
2. Extract frequent problems and general fixes
3. After distilling them, update the "common issues Playbook" section of `MEMORY.md`
4. Clean diagnosis logs older than 30 days (keep only the problem type and fix result)

---

## Behavior without a baseline

If no system baseline is recorded in `MEMORY.md`:
- Automatically establish the baseline on the first heartbeat
- In the push, state: "the first system scan is complete, a health baseline has been established"
- Subsequent heartbeats compare against the baseline values to judge anomalies

---

## Alert thresholds (user-customizable)

| Metric | Default threshold | Meaning |
|------|---------|------|
| CPU usage | > 85% for 5 minutes | 🟡 Warning |
| System load | > CPU cores * 1.5 | 🟡 Warning; > CPU cores * 2 🔴 Critical |
| Memory usage | > 90% | 🟡 Warning; > 95% 🔴 Critical |
| Disk usage | > 85% | 🟡 Warning; > 95% 🔴 Critical |
| inode usage | > 90% | 🟡 Warning |
| Network connectivity | DNS resolution failure / external ping failure | 🔴 Critical |
| Service status | stopped / failed / not listening | 🔴 Critical |
| System logs | > 50 ERROR entries/hour | 🟡 Warning |

Users can change thresholds through conversation:
> "Change the CPU alert threshold to 90%"
> "Warn me when disk usage exceeds 80%"

---

## 5. Periodic cluster patrol

**Trigger:** once every 30 minutes

**Precondition:** a `cluster_config` section exists in `MEMORY.md`

**If there is no cluster configuration:** skip this task and give no prompt at all

**Steps:**

1. Read `cluster_config` in `MEMORY.md` (node list, region, tags)
2. Read `references/cluster-quick-check.md` and execute through tencentcloud-infra:
   - Layer 1: DescribeInstances (instance status)
   - Layer 2A: GetMonitorData (cloud-side CPU/memory 5-minute average)
   - Layer 2B: TAT RunCommand (real-time OS snapshot)
3. Read `references/cluster-health-score.md` and compute each node's score and the cluster total score
4. Decide whether a push is needed:
   - Cluster total score < 80, or any node score < 60 → proactively push an alert
   - All nodes normal (cluster score ≥ 80) → record silently, do not push

5. Alert push format:

```
[Cluster Patrol Alert YYYY-MM-DD HH:MM]

📊 Cluster score: <N>/100 (<grade>)
Weakest link: <node name> (<score> points)

🔴 Abnormal nodes:
- <node name>: <problem description> (e.g. disk 92%, SSH inactive)

🟡 Nodes needing attention:
- <node name>: <problem description>

---
Type "cluster deep analysis" for root cause analysis
Type "fix <node name>" to start the repair flow
```

6. After each patrol, update the diagnosis history in `MEMORY.md`:

```markdown
### YYYY-MM-DD HH:MM — cluster patrol
- **Cluster score**: N/100
- **Abnormal nodes**: [list] (write "none" if there are none)
- **Main problem**: one-sentence description
- **Action**: check only, no action taken
```

**Alert deduplication logic (to prevent alert fatigue):**

- After the same problem on the same node has been pushed 3 times in a row, reduce the frequency to at most 1 push every 4 hours
- When the same kind of problem appears in 3 consecutive patrols on the same node, append the annotation "persistent anomaly, deep analysis recommended" to the alert
- If the problem has recovered since the last push (node score ≥ 80), reset the counter and push normally the next time it appears
