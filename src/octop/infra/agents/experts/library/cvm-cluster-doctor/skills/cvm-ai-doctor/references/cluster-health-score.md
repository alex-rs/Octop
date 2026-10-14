# Cluster Health Score

> **Turn quick-check data into a quantifiable health score and generate a cluster report.**
> The input comes from the summary data in references/cluster-quick-check.md Step 4.

---

## Node Scoring Algorithm (100-point scale, deduction-based)

### Starting score: 100

### Deduction Rules (computed in order; deductions do not stack beyond the caps)

#### Layer 1: Cloud Instance State

| Condition | Deduction | Notes |
|------|------|------|
| `instance_state` = STOPPED / SHUTDOWN / TERMINATING | Final score = **0** | Instance unavailable, stop the calculation |
| `instance_state` = REBOOTING | Not scored for now | Mark it as "rebooting" |

#### Layer 2B: OS Load (TAT data; skip this section if tat_available=false)

| Condition | Deduction |
|------|------|
| `load_ratio` > 2.0 (LOAD / NCPU > 200%) | **-25** |
| `load_ratio` > 1.5 (150%) | **-10** |
| `load_ratio` > 1.0 (100%) | **-5** |

#### Layer 2B: Memory Usage (TAT data)

| Condition | Deduction |
|------|------|
| `mem_pct` > 90% | **-20** |
| `mem_pct` > 75% | **-10** |
| `mem_pct` > 60% | **-5** |

#### Layer 2B: Disk Usage (TAT data)

| Condition | Deduction |
|------|------|
| `disk_root_pct` > 90 | **-25** |
| `disk_root_pct` > 80 | **-10** |
| `disk_root_pct` > 70 | **-5** |

#### Layer 2B: SSH Daemon Status (TAT data)

| Condition | Deduction |
|------|------|
| `sshd_active` = false (not in the active state) | **-40** |

#### Layer 2A: Cloud CPU Average (GetMonitorData)

| Condition | Deduction |
|------|------|
| `cpu_cloud_avg_pct` > 85% | **-15** |
| `cpu_cloud_avg_pct` > 70% | **-5** |

#### Layer 2A: Cloud Memory Average (GetMonitorData)

| Condition | Deduction |
|------|------|
| `mem_cloud_avg_pct` > 90% | **-15** |
| `mem_cloud_avg_pct` > 80% | **-5** |

#### Degradation Compensation

| Condition | Handling |
|------|------|
| `tat_available` = false | OS-related deductions are skipped; the result is marked "cloud metrics only (lower confidence)" |
| Cloud metrics N/A | Cloud-metric deductions are skipped |

**Minimum score: 0 (it never goes negative)**

---

## Cluster Scoring: The Bucket Principle

```
Cluster score = MIN(score of all nodes)

Rationale: the cluster's actual availability is decided by its weakest node.
           1 node down = some requests fail, no matter how healthy the others are.
```

---

## Health Levels

| Range | Level | Display |
|------|------|------|
| 90-100 | Healthy | ✅ Healthy |
| 75-89 | Minor anomaly | ✅ Normal (minor issues) |
| 60-74 | Needs attention | ⚠️ Needs attention |
| 40-59 | Abnormal | 🚨 Abnormal |
| 0-39 | Critical | 🔴 Critical |

---

## Report Template

```
## Cluster Health Report [<cluster_name>]
Time: <YYYY-MM-DD HH:MM:SS> (<region>)

📊 Cluster score: <score>/100 <level icon>
   Weakest link: <lowest-scoring node name> (<lowest score> points)

Node status overview:
  ✅ Healthy nodes: <N>
  ⚠️ Needs attention: <N>
  🔴 Abnormal nodes: <N>
  ⏹️ Stopped: <N>

| Node         | State   | Score | Load/core | Mem%  | Disk% | SSH   | Cloud CPU% | Anomaly summary |
|--------------|---------|------|---------|-------|-------|-------|--------|---------|
| order-api-1  | RUNNING | 95   | 0.3/4   | 42%   | 55%   | ✅    | 38%    | —       |
| order-api-2  | RUNNING | 78   | 0.8/4   | 78%   | 61%   | ✅    | 65%    | Memory high |
| order-api-3  | RUNNING | 55   | 3.2/4   | 88%   | 79%   | ✅    | 92%    | CPU high / memory high / disk elevated |
| order-api-4  | STOPPED | 0    | —       | —     | —     | N/A   | —      | Instance stopped |

---
<If there are cross-node correlated issues, list them here; otherwise omit>

⚠️ Cluster-level issues detected:
1. [Correlation] order-api-2 and order-api-3 both have memory > 75%, suggesting shared-resource pressure
   → Recommended: check the shared MySQL/Redis instances (call tencentcloud-infra GetMonitorData)

---
💡 Suggested actions (by priority):

🔴 Handle immediately:
→ order-api-3 CPU usage is 92%; its processes need in-depth investigation
   Type "deep analysis order-api-3" to view the top processes

🟡 Handle as soon as possible:
→ order-api-4 is stopped; please confirm whether this was planned
   If it needs to be started: confirm first, then do it via tencentcloud-infra

🟢 Monitor:
→ order-api-2 memory is 78%; recommend rechecking the trend within 24 hours
```

---

## Correlation Detection (quick version)

Before generating the report, quickly scan for the following patterns (for detailed analysis see cluster-deep-analysis.md):

**Pattern A: Memory cascade**
Condition: `≥ 3 nodes with mem_pct > 75%`
Append to the report: "[Correlation] Multiple nodes have elevated memory at the same time, suggesting shared backend pressure"

**Pattern B: Uneven load**
Condition: `MAX(load_ratio) - MIN(load_ratio) > 0.5` (among healthy nodes)
Append to the report: "[Correlation] Load is unevenly distributed (max X, min Y); recommend checking load balancing"

**Pattern C: Synchronized disk growth**
Condition: `≥ 2 nodes with disk_root_pct > 75%`
Append to the report: "[Correlation] Multiple nodes have high disk usage; possibly uniform log files that were never cleaned up"

---

## Writing the Report to MEMORY.md

After every check, write a brief summary into the MEMORY.md diagnosis history:

```markdown
### <YYYY-MM-DD HH:MM> — Cluster quick check
- **Cluster score**: <N>/100
- **Abnormal nodes**: <node list> (write "none" if there are none)
- **Main issues**: <one-sentence description>
- **Actions**: <which actions were performed this time; if none, write "check only, no actions">
```
