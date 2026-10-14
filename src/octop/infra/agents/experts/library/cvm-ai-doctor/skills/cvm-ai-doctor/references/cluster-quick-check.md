# Cluster Quick Check

> **Goal: complete a 3-layer snapshot of the whole cluster within 30 seconds and report each node's health state.**
> All API operations are performed through the tencentcloud-infra skill;
> see references/skill-collaboration-tencentcloud.md for details.

---

## Prerequisites

1. MEMORY.md contains `cluster_config.known_nodes` (the discovered node list)
2. OAuth credentials are valid (for how to check, see references/skill-collaboration-tencentcloud.md — the "OAuth Credential Check" protocol)
3. If these are not met, run references/cluster-discovery.md first

---

## 3-Layer Snapshot Execution Order

```
Step 0 (~1s)  : OAuth credential check
Step 1 (~2s)  : Layer 1 — instance state (DescribeInstances)
Step 2 (~3s)  : Layer 2A — cloud monitoring metrics (GetMonitorData, pulled in parallel for all nodes)
Step 3 (~15s) : Layer 2B — TAT OS snapshot (RunCommand, one API call covers all nodes)
Step 3b (~5s) : Poll TAT results (DescribeInvocationTasks)
Step 4 (~2s)  : Summarize → score → generate the report
─────────────────────────────────────────────────
Total time: about 25-30 seconds
```

---

## Step 1: Layer 1 — Instance State

**Command to run (have tencentcloud-infra execute it):**
```bash
tccli cvm DescribeInstances \
  --region <cluster_config.region> \
  --InstanceIds '<known_nodes InstanceId array>'
```

**Fields to collect:**
- `InstanceId`
- `InstanceName`
- `InstanceState`: RUNNING / STOPPED / SHUTDOWN / TERMINATING / REBOOTING

**Mark immediately:**
- `STOPPED` / `SHUTDOWN` / `TERMINATING` → node score = **0**; do not run Layer 2B afterwards
- `REBOOTING` → wait and skip this round (mark it as "rebooting, snapshot skipped")
- `RUNNING` → continue to Layer 2A and 2B

---

## Step 2: Layer 2A — Cloud Monitoring Metrics (5-minute average)

**For all RUNNING nodes, run in parallel (have tencentcloud-infra execute it):**

```bash
# Set the time window (last 15 minutes)
END_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
START_TIME=$(date -u -d "15 minutes ago" +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || \
             date -u -v-15M +"%Y-%m-%dT%H:%M:%SZ")   # macOS compatible

# Pull CPU usage for each RUNNING node
tccli monitor GetMonitorData \
  --Namespace QCE/CVM \
  --MetricName CpuUsage \
  --Period 300 \
  --StartTime "$START_TIME" \
  --EndTime "$END_TIME" \
  --Instances '[{"Dimensions":[{"Name":"InstanceId","Value":"ins-xxx"}]}]'

# Pull memory usage for each RUNNING node
tccli monitor GetMonitorData \
  --Namespace QCE/CVM \
  --MetricName MemUsage \
  --Period 300 \
  --StartTime "$START_TIME" \
  --EndTime "$END_TIME" \
  --Instances '[{"Dimensions":[{"Name":"InstanceId","Value":"ins-xxx"}]}]'
```

**How to compute:**
Take the mean of the `DataPoints[*].Values` array (ignoring nulls).
If there are no data points, mark that node's CPU/memory metrics as `N/A`.

---

## Step 3: Layer 2B — TAT OS Live Snapshot

## ⚡ Script-First Path: Run TAT with cluster_os_snapshot.sh

If `scripts/cluster_os_snapshot.sh` exists, **base64-encode the script file contents and pass them to TAT directly**,
with no need to expand inline commands.

**Division of work**:
- **Agent (local)**: read the script file and base64-encode it (see the commands below)
- **tencentcloud-infra**: run `tccli tat RunCommand` to send the encoded content to the remote CVM
- **Remote CVM**: TAT decodes and runs the script automatically, returning KEY=VALUE results

**Step A — The Agent encodes locally (choose based on the OS LightClaw runs on):**

```bash
# Linux / macOS (-w 0 forces single-line output, no tr pipe needed)
SKILL_DIR="<cvm-ai-doctor skill directory>"
CONTENT=$(base64 -w 0 < "$SKILL_DIR/scripts/cluster_os_snapshot.sh")
echo "$CONTENT"   # copy this output as the value of TAT --Content
```

```powershell
# Windows PowerShell (use this version when LightClaw runs on Windows)
$SKILL_DIR = "<cvm-ai-doctor skill directory>"
$CONTENT = [Convert]::ToBase64String([IO.File]::ReadAllBytes("$SKILL_DIR\scripts\cluster_os_snapshot.sh"))
Write-Output $CONTENT   # copy this output as the value of TAT --Content
```

**Step B — Have tencentcloud-infra execute it (one API call covering all nodes):**

```bash
tccli tat RunCommand \
  --region <region> \
  --InstanceIds '["ins-xxx","ins-yyy","ins-zzz"]' \
  --CommandType SHELL \
  --Timeout 30 \
  --Content "<base64 string output by Step A>"
```

> The `scripts/` path is relative to the cvm-ai-doctor skill directory. The Agent should expand it to an absolute path.
> If the script file does not exist, fall back to the inline command below.

---

**Fallback: inline command (use when the script does not exist)**

**TAT snapshot one-liner (run it against all RUNNING nodes with TAT=Online):**

```bash
h=$(hostname -s 2>/dev/null||echo unknown); \
l=$(awk '{print $1}' /proc/loadavg 2>/dev/null||echo -1); \
c=$(nproc 2>/dev/null||echo 1); \
m=$(free -m 2>/dev/null|awk '/Mem:/{printf "%.0f/%d",$3,$2}'); \
d=$(df / 2>/dev/null|awk 'NR==2{print $5}'|tr -d '%'); \
s=$(systemctl is-active sshd 2>/dev/null||echo unknown); \
echo "HOST=$h LOAD=$l NCPU=$c MEM_MB=$m DISK_ROOT_PCT=$d SSH=$s"
```

**Have tencentcloud-infra execute it (one API call):**
```bash
COMMAND_CONTENT=$(cat <<'EOF'
h=$(hostname -s 2>/dev/null||echo unknown); l=$(awk '{print $1}' /proc/loadavg 2>/dev/null||echo -1); c=$(nproc 2>/dev/null||echo 1); m=$(free -m 2>/dev/null|awk '/Mem:/{printf "%.0f/%d",$3,$2}'); d=$(df / 2>/dev/null|awk 'NR==2{print $5}'|tr -d '%'); s=$(systemctl is-active sshd 2>/dev/null||echo unknown); echo "HOST=$h LOAD=$l NCPU=$c MEM_MB=$m DISK_ROOT_PCT=$d SSH=$s"
EOF
)

tccli tat RunCommand \
  --region <region> \
  --InstanceIds '["ins-xxx","ins-yyy","ins-zzz"]' \
  --CommandType SHELL \
  --Timeout 30 \
  --Content "$(printf '%s' "$COMMAND_CONTENT" | base64 -w 0)"
```

**Poll the results (up to 12 times, 5 seconds apart):**
```bash
tccli tat DescribeInvocationTasks --InvocationId <inv-id>
```

Termination condition: all `TaskStatus` = `SUCCESS` or `FAILED` or `TIMEOUT`

**Decode the TAT output:**
```bash
echo "<base64_output>" | base64 -d
# resulting format: HOST=xxx LOAD=0.85 NCPU=4 MEM_MB=2048/8192 DISK_ROOT_PCT=55 SSH=active
```

**Parse the memory percentage:**
```
MEM_MB=2048/8192  →  MEM_PCT = round(2048/8192 * 100) = 25%
```

---

## Step 4: Summary Data Structure (passed to the scoring module)

For each node, assemble the following fields and hand them to references/cluster-health-score.md to compute the score:

```
Data for node ins-xxx:
  instance_state: RUNNING
  cpu_cloud_avg_pct: 42.3          # Layer 2A; leave blank if N/A
  mem_cloud_avg_pct: 68.1          # Layer 2A; leave blank if N/A
  load: 0.85                       # Layer 2B TAT
  ncpu: 4                          # Layer 2B TAT
  load_ratio: 0.21                 # load / ncpu
  mem_used_mb: 2048                # Layer 2B TAT
  mem_total_mb: 8192               # Layer 2B TAT
  mem_pct: 25.0                    # Layer 2B TAT computed
  disk_root_pct: 55                # Layer 2B TAT
  sshd_active: true                # Layer 2B TAT
  tat_available: true              # whether an OS snapshot is available
  tat_status: SUCCESS              # SUCCESS / FAILED / TIMEOUT
```

## ⚡ Script-First Path: Use cluster_score.sh Instead of Manual Calculation

After summarizing each node's data, if `scripts/cluster_score.sh` exists, **call the script to score directly** and skip manual calculation:

```bash
# Each line represents one node, in KV format:
{
  echo "node=ins-aaa name=api-1 instance_state=RUNNING load_ratio=0.21 mem_pct=25 disk_root_pct=55 sshd_active=true cpu_cloud_avg_pct=42 mem_cloud_avg_pct=68 tat_available=true"
  echo "node=ins-bbb name=api-2 instance_state=RUNNING load_ratio=1.8  mem_pct=82 disk_root_pct=79 sshd_active=true cpu_cloud_avg_pct=88 mem_cloud_avg_pct=84 tat_available=true"
  # ... one line per node
} | bash scripts/cluster_score.sh
```

The script output contains each node's score, the deduction details, and the cluster's lowest score (bucket principle); hand it to the LLM to write the report narrative directly.

If the script does not exist, compute manually per `references/cluster-health-score.md`.

---

## Special Cases

| Case | Handling |
|------|---------|
| TAT Timeout (instance IO too high) | Mark that node `tat_status: TIMEOUT`; score using cloud metrics only |
| TAT FAILED (command execution failed) | Record the error message; score using cloud metrics only |
| All TAT runs timed out | Report "unable to obtain an OS snapshot; cloud metrics only" |
| No cloud monitoring data | Mark `N/A` and skip the cloud-metric deductions |
| Instance REBOOTING | Skip this snapshot and retry on the next inspection |
| Cross-region cluster | Call TAT RunCommand separately for each region and merge the results |
