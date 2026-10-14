# cvm-ai-doctor × tencentcloud-infra Collaboration Protocol

> This document defines how the two skills work together to complete cluster diagnosis and management tasks.
> **Core principle: skills collaborate through Markdown prose instructions, with the Agent acting as orchestrator; there are no code-level API calls.**

---

## Responsibility Split

| Responsibility | cvm-ai-doctor | tencentcloud-infra |
|------|:---:|:---:|
| Node discovery (DescribeInstances) | ❌ | ✅ |
| Cloud monitoring metrics (GetMonitorData) | ❌ | ✅ |
| TAT batch command execution (RunCommand) | ❌ | ✅ |
| TAT result polling (DescribeInvocationTasks) | ❌ | ✅ |
| Instance lifecycle (Reboot/Stop/Start) | ❌ | ✅ |
| OS data parsing and diagnostic analysis | ✅ | ❌ |
| Cross-node correlation analysis | ✅ | ❌ |
| Cluster health scoring | ✅ | ❌ |
| Diagnostic report generation | ✅ | ❌ |
| MEMORY.md cluster configuration maintenance | ✅ | ❌ |
| OAuth credential management | ❌ | ✅ |

---

## Core Protocol: TAT Remote Command Execution (Cluster OS Snapshot)

### ⚡ Script-First Path

**Prefer** the matching script in the `scripts/` directory of the `cvm-ai-doctor` skill: base64-encode it locally, then send it to the remote CVM through TAT for execution. This avoids the LLM reassembling the command every time, reduces token consumption, and makes it less likely that command details are omitted or altered.

**Step A — Agent encodes locally (choose according to the OS where LightClaw runs):**

```bash
# Linux / macOS (-w 0 forces single-line output; no tr pipe needed)
SKILL_DIR="<absolute path to the cvm-ai-doctor skill>"

# Layer 2B quick snapshot
CONTENT=$(base64 -w 0 < "$SKILL_DIR/scripts/cluster_os_snapshot.sh")

# Deep analysis (choose the matching script by anomaly type)
# CONTENT=$(base64 -w 0 < "$SKILL_DIR/scripts/cluster_deep_cpu.sh")
# CONTENT=$(base64 -w 0 < "$SKILL_DIR/scripts/cluster_deep_memory.sh")
# CONTENT=$(base64 -w 0 < "$SKILL_DIR/scripts/cluster_deep_disk.sh")
# CONTENT=$(base64 -w 0 < "$SKILL_DIR/scripts/cluster_deep_ssh.sh")
# CONTENT=$(base64 -w 0 < "$SKILL_DIR/scripts/cluster_deep_network.sh")
```

```powershell
# Windows PowerShell (ReadAllBytes produces no line breaks; no extra handling needed)
$SKILL_DIR = "<absolute path to the cvm-ai-doctor skill>"

# Layer 2B quick snapshot
$CONTENT = [Convert]::ToBase64String([IO.File]::ReadAllBytes("$SKILL_DIR\scripts\cluster_os_snapshot.sh"))

# Deep analysis (choose the matching script by anomaly type)
# $CONTENT = [Convert]::ToBase64String([IO.File]::ReadAllBytes("$SKILL_DIR\scripts\cluster_deep_cpu.sh"))
# $CONTENT = [Convert]::ToBase64String([IO.File]::ReadAllBytes("$SKILL_DIR\scripts\cluster_deep_memory.sh"))
# $CONTENT = [Convert]::ToBase64String([IO.File]::ReadAllBytes("$SKILL_DIR\scripts\cluster_deep_disk.sh"))
# $CONTENT = [Convert]::ToBase64String([IO.File]::ReadAllBytes("$SKILL_DIR\scripts\cluster_deep_ssh.sh"))
# $CONTENT = [Convert]::ToBase64String([IO.File]::ReadAllBytes("$SKILL_DIR\scripts\cluster_deep_network.sh"))
```

**Step B — Have tencentcloud-infra execute it (put the Step A output into --Content):**

```bash
tccli tat RunCommand \
  --region <region> \
  --InstanceIds '["ins-xxx","ins-yyy","ins-zzz"]' \
  --CommandType SHELL \
  --Timeout 30 \
  --Content "<output of Step A>"
```

> **Script path note**: the `scripts/` directory is relative to the cvm-ai-doctor skill directory. The Agent should expand it to an absolute path before issuing the instruction.
> **Fallback rule**: if the script file does not exist, fall back to the inline commands in cluster-quick-check.md / cluster-deep-analysis.md.

---

### Fallback: Inline Command Path (when the script does not exist)

### Instruction issued by cvm-ai-doctor (spoken to the Agent):

```
Please call the tencentcloud-infra skill to execute the following TAT batch command:

Region: ap-guangzhou
InstanceIds: ["ins-xxx", "ins-yyy", "ins-zzz"]
CommandType: SHELL
Timeout: 30
Content (before base64 encoding):
  h=$(hostname -s 2>/dev/null||echo unknown); \
  l=$(awk '{print $1}' /proc/loadavg 2>/dev/null||echo -1); \
  c=$(nproc 2>/dev/null||echo 1); \
  m=$(free -m 2>/dev/null|awk '/Mem:/{printf "%.0f/%d",$3,$2}'); \
  d=$(df / 2>/dev/null|awk 'NR==2{print $5}'|tr -d '%'); \
  s=$(systemctl is-active sshd 2>/dev/null||echo unknown); \
  echo "HOST=$h LOAD=$l NCPU=$c MEM_MB=$m DISK_ROOT_PCT=$d SSH=$s"

tccli command:
  tccli tat RunCommand \
    --region ap-guangzhou \
    --InstanceIds '["ins-xxx","ins-yyy","ins-zzz"]' \
    --CommandType SHELL \
    --Timeout 30 \
    --Content "$(printf '%s' '<the command above>' | base64 -w 0)"
```

### What tencentcloud-infra returns after execution (example):

```json
{
  "InvocationId": "inv-abc123",
  "Response": {
    "RequestId": "...",
    "InvocationId": "inv-abc123"
  }
}
```

### After receiving the InvocationId, cvm-ai-doctor issues a polling instruction:

```
Please call the tencentcloud-infra skill to poll the following TAT execution results:

tccli tat DescribeInvocationTasks \
  --InvocationId inv-abc123

Polling strategy:
- Interval: 5 seconds
- Maximum polls: 12 times (60 seconds in total)
- Termination condition: TaskStatus = SUCCESS or FAILED for all tasks
```

### TAT output decoding rules:

The `TaskResult.Output` field of TAT is base64-encoded; decode it as follows:

```bash
echo "<base64_string>" | base64 -d
```

After decoding you get single-line text in the following format:
```
HOST=order-api-1 LOAD=0.85 NCPU=4 MEM_MB=2048/8192 DISK_ROOT_PCT=55 SSH=active
```

**cvm-ai-doctor is responsible for parsing this output**; tencentcloud-infra only executes commands and returns the raw result.

---

## Core Protocol: Pulling Cloud Monitoring Metrics

### Instruction issued by cvm-ai-doctor:

```
Please call the tencentcloud-infra skill to pull the CPU and memory monitoring metrics for the following instances:

Time window: the last 15 minutes (EndTime = current time, StartTime = current time - 15 minutes)
Period: 300 (5-minute aggregation)

Execute for each instance:
  tccli monitor GetMonitorData \
    --Namespace QCE/CVM \
    --MetricName CpuUsage \
    --Instances '[{"Dimensions":[{"Name":"InstanceId","Value":"ins-xxx"}]}]' \
    --Period 300 \
    --StartTime "<StartTime>" \
    --EndTime "<EndTime>"

  tccli monitor GetMonitorData \
    --Namespace QCE/CVM \
    --MetricName MemUsage \
    --Instances '[{"Dimensions":[{"Name":"InstanceId","Value":"ins-xxx"}]}]' \
    --Period 300 \
    --StartTime "<StartTime>" \
    --EndTime "<EndTime>"
```

### Handling the returned data:

tencentcloud-infra returns a `DataPoints` array, and **cvm-ai-doctor** computes the averages:
- Take the mean of `DataPoints[*].Values` as the node's 5-minute average CPU/memory utilization
- If DataPoints is empty, mark that metric as "data unavailable"

---

## Core Protocol: Instance Lifecycle Operations

### 🔴 High-risk operations; they may only be issued after explicit user confirmation

**Restart an instance:**
```
Please call the tencentcloud-infra skill to restart the following instance:

tccli cvm RebootInstances \
  --region <region> \
  --InstanceIds '["ins-xxx"]' \
  --StopType SOFT

After execution, poll the DescribeInstances status every 10 seconds until the instance returns to RUNNING.
Timeout: 10 minutes
```

**Stop an instance:**
```
Please call the tencentcloud-infra skill:

tccli cvm StopInstances \
  --region <region> \
  --InstanceIds '["ins-xxx"]' \
  --StopType SOFT
```

**Start an instance:**
```
Please call the tencentcloud-infra skill:

tccli cvm StartInstances \
  --region <region> \
  --InstanceIds '["ins-xxx"]'
```

---

## Degraded Mode: When TAT Is Unavailable

When the TAT Agent status is Offline, run the degraded flow:

1. Skip TAT RunCommand (Layer 2B)
2. Still run Layer 1 (DescribeInstances) + Layer 2A (GetMonitorData)
3. In the report, annotate every node without an OS snapshot with: `⚠️ OS snapshot unavailable (TAT offline)`
4. When scoring, skip OS-related metrics (load, SSH status) and score based only on cloud metrics
5. Label the scoring result: "cloud metrics only, lower confidence"

---

## Collaboration Scenario Mapping

| User says | cvm-ai-doctor action | tencentcloud-infra action |
|--------|-------------------|------------------------|
| Check cluster health status | Read cluster-quick-check.md, direct execution | DescribeInstances + GetMonitorData + TAT RunCommand |
| High load on a cluster node | Read cluster-deep-analysis.md, direct deep TAT | TAT RunCommand (ps aux, top, etc.) |
| Restart a CVM | Read cluster-remediation.md, confirm risk then direct | RebootInstances + poll DescribeInstances |
| Discover a new cluster | Read cluster-discovery.md, direct discovery | DescribeInstances + DescribeAutomationAgentStatus |
| Query a node's memory trend | Read cluster-deep-analysis.md, direct the pull | GetMonitorData (past 24 hours) |

---

## Core Protocol: OAuth Credential Check

**This check must be run before every call to any tccli command.**

```bash
python3 scripts/tccli-oauth-helper.py --status
```

> `scripts/` is a relative path under the tencentcloud-infra skill directory; it resolves automatically from the skill's deployment location, so no hard-coded absolute path is needed.

**Handling the return value:**
- Output contains `valid` → credentials are valid, continue execution
- Output contains `expired` or `missing` → abort the current operation and prompt the user to refresh credentials:
  ```
  ⚠️ OAuth credentials have expired; cluster operations are paused.
  Please complete OAuth authorization first, then re-initiate this operation.
  ```

---

## Important Constraints

1. **Credential pre-check**: before each API execution through tencentcloud-infra, first confirm the credentials are valid following the "OAuth Credential Check" protocol above
2. **Region consistency**: TAT is Region-Scoped, so clusters spanning regions must be called in per-region batches
3. **Lighthouse special handling**: Lighthouse instances use `tccli lighthouse`, which has no TAT support
4. **Batch first**: TAT RunCommand accepts an InstanceIds array that covers all nodes in a single API call; do not call instances one by one
5. **Wait for results**: TAT executes asynchronously; you must poll DescribeInvocationTasks until completion and must not assume it has already finished
