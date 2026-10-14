---
summary: "Cluster doctor heartbeat tasks — periodic cluster patrol and alerting"
read_when:
  - heartbeat polling
---

# Heartbeat Task List

## 1. Quick cluster patrol (core task)

**Trigger:** once every 30 minutes

**Precondition:** a `cluster_config` section exists in MEMORY.md

**If there is no cluster configuration:** skip silently with no prompt at all

**Steps:**

### Step 0: Credential check

Run the credential check through the `tencentcloud-infra` skill (paths are relative to that skill's directory):

```bash
python3 scripts/tccli-oauth-helper.py --status
```

- Returns `valid` → continue
- Returns `expired` or `missing` → push the following prompt and stop this patrol:

```
⚠️ OAuth credentials have expired; the cluster patrol is paused.

Please refresh the credentials (complete the OAuth authorization through the tencentcloud-infra skill).
After refreshing, the cluster patrol resumes automatically on the next heartbeat (about 30 minutes later).
```

### Step 1-4: Run the 3-layer snapshot + scoring

Call the `cvm-ai-doctor` skill and read in order:
1. `references/cluster-quick-check.md` — run the 3-layer snapshot (Layer1+2A+2B, about 25-30s)
2. `references/cluster-health-score.md` — compute node scores + cluster score + quick correlation checks

### Step 5: Alert decision

| Condition | Action |
|------|------|
| Cluster score < 80 or any node score < 60 | Push an alert (see format) |
| All normal (cluster ≥80, all nodes ≥60) | Record silently, **do not push** |

**Alert push format:**

```
[Cluster Doctor Patrol Report YYYY-MM-DD HH:MM]Cluster: <cluster_name>

📊 Cluster score: <N>/100 <grade icon>
   Weakest link: <node name> (<N> points)

🔴 Abnormal nodes (immediate action required):
- <node name> <ins-id>: <problem summary>
  (example: disk 92%[-25] + sshd inactive[-40])

🟡 Nodes needing attention:
- <node name> <ins-id>: <problem summary>
  (example: memory 88%[-20] + cloud-side CPU average 76%[-5])

⏹️ Stopped nodes:
- <node name> <ins-id> (is the downtime planned?)

---
Type "deep analysis <node name>" for root cause analysis
Type "fix <node name>" to start the repair flow
```

### Step 6: Write the diagnosis history

After each patrol, whether or not a push happened, do the following two steps:

**6a. Append a JSONL record (structured history, used by the Dashboard)**

Pipe the JSON output of `cluster_score.sh` to the recording script:

```bash
# Run in the cvm-ai-doctor skill directory
# <score_json> is the complete JSON string output by cluster_score.sh
echo '<score_json>' | python3 scripts/cluster_patrol_record.py \
    --cluster-name "<cluster_name>" \
    --rotate
```

- `--rotate`: after each write, automatically clean up records older than 7 days (compressed and archived to `cluster-doctor.old.jsonl.gz`)
- All internal script errors are handled silently (written to stderr, `exit 0`), so the heartbeat task is **never interrupted**
- Record write path: `~/.octop/stats/cluster-doctor.jsonl`

**6b. Write MEMORY.md (readable summary, for conversation retrieval)**

```markdown
### YYYY-MM-DD HH:MM — cluster patrol
- **Cluster score**: N/100
- **Abnormal nodes**: [ins-xxx(order-api-3, 45 points), ...] (write "none" if there are none)
- **Main problem**: one-sentence description (e.g. "order-api-3 disk 92% and sshd stopped")
- **Action**: check only, no action taken
```

---

## Alert deduplication logic (to prevent alert fatigue)

**Frequency reduction for persistent problems:**
- Same node, same problem, alert triggered in 3 consecutive patrols → reduce to at most 1 push every 4 hours
- After 3 consecutive times, append to the alert: `"persistent anomaly X times, deep analysis recommended"`

**Reset when a problem recovers:**
- If the problem has recovered (node score ≥ 80 and the previously abnormal metrics are back in the normal range) → reset that node's consecutive counter
- The next time a problem appears on that node, push at the normal frequency again

**Rate limit for credential-expiry alerts:**
- Push the credential-expiry prompt at most once per hour, to avoid flooding every 30 minutes

---

## 2. Weekly report summary

**Trigger:** every Sunday at 21:00

**Precondition:** MEMORY.md contains `cluster_config` and there are ≥ 3 patrol records this week

**If the conditions are not met:** skip silently

**Steps:**

1. Review all cluster patrol records for this week in MEMORY.md
2. Compute statistics:
   - This week's average cluster score and the moment of the lowest score
   - Number of alerts and nodes with frequent problems
3. For each RUNNING node, pull the disk trend of the past 7 days through the `tencentcloud-infra` skill:
   ```bash
   tccli monitor GetMonitorData \
     --Namespace QCE/CVM --MetricName DiskUsage \
     --Period 3600 \
     --StartTime "<ISO8601 7 days ago>" --EndTime "<current ISO8601>" \
     --Instances '[{"Dimensions":[{"Name":"InstanceId","Value":"ins-xxx"}]}]'
   ```
4. Identify abnormal disk growth (growth > 5GB this week or current usage > 70%)
5. Push the weekly report:

```
[Cluster Doctor Weekly Report YYYY-MM-DD]Cluster: <cluster_name>

📊 Cluster health summary for this week
- Average cluster score: <N>/100
- Lowest score: <N> points (<date HH:MM>, reason: <one sentence>)
- Patrols: <N> | Alerts: <N>

💾 Disk growth trend (nodes needing attention)
- <node name>: +<NGB> this week (now <M>%) → estimated to exceed 95% in <X> days
  (if there are no nodes needing attention, omit this section)

🔴 Nodes with frequent problems:
- <node name>: <N> alerts this week, main problem: <description>
  (if there are none, omit this section)

💡 Suggestions for this week (by priority):
1. <suggestion 1>
2. <suggestion 2>
```

---

## 3. Memory maintenance

**Trigger:** every Sunday (triggered together with the weekly report)

**Steps:**

1. Review this week's diagnosis history and extract frequent problem types (e.g. "multiple nodes with high disk usage", "frequent TAT timeouts")
2. If a problem occurred ≥ 3 times this week: write (or update) the corresponding Playbook in MEMORY.md:

```markdown
## Common Issues Playbook

### Multiple nodes with high disk usage (last updated: YYYY-MM-DD)
- Typical symptom: disk_root_pct > 75% on ≥2 nodes
- Quick fix: run logrotate -f /etc/logrotate.conf via TAT (see cluster-remediation.md operation B)
- Root cause: usually /var/log/nginx or /var/log/app has no logrotate configuration
- Prevention: check whether every node has the corresponding configuration under /etc/logrotate.d/

### Frequent TAT timeouts (last updated: YYYY-MM-DD)
- Typical symptom: Layer 2B TAT Timeout, node IO too high
- Quick fix: first assess the risk with Layer 2A cloud-side metrics, then diagnose IO with an in-depth TAT command (iostat)
- Root cause: usually disk IO saturation makes shell commands respond slowly
```

3. Clean up patrol records older than 30 days (keep only the monthly summary, not the raw data)

---

## Alert thresholds (customizable through conversation)

| Metric | Default warning threshold | Default critical threshold |
|------|------------|------------|
| Node score | < 60 points | < 40 points |
| Cluster score | < 80 points | < 60 points |
| Disk usage | > 80% | > 90% |
| Memory usage (TAT) | > 80% | > 90% |
| Cloud-side CPU average | > 75% | > 90% |
| Load ratio (load/ncpu) | > 1.5 | > 2.0 |
| SSH status | — | inactive (immediately critical) |
| Instance status | STOPPED | SHUTDOWN/TERMINATING |

**Changing thresholds through conversation:**
> "Change the cluster score alert threshold to 70"
> "Only warn me when disk exceeds 85%"
> "Pause the patrol, I am doing maintenance"

---

## Behavior without a baseline

If MEMORY.md has no cluster configuration (`cluster_config` does not exist):
- All heartbeat tasks are skipped silently
- Only when the user triggers it proactively (typing "check cluster") guide the configuration (read `cluster-discovery.md`).
