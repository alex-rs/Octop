# Cluster Deep Analysis

> **After the quick check finds anomalies, run deep diagnostics on the problem nodes or on cluster-level correlation patterns.**
> Run this flow only after the quick check (cluster-quick-check.md) is complete and the user asks for a deep analysis.

---

## Single-Node Deep Diagnosis

When the user says "deep analysis of <node name>" or "why is <node> CPU so high",
send the following TAT commands to that node (executed through the tencentcloud-infra skill).

**Choose commands as needed; you do not need to run them all — pick based on the anomaly types found by the quick check:**

---

### Deep diagnosis of high CPU load

## ⚡ Script-first path: cluster_deep_cpu.sh

If `scripts/cluster_deep_cpu.sh` exists, **the Agent first encodes it locally, then has tencentcloud-infra execute it**:

```bash
# Step A — Agent encodes locally (Linux / macOS)
SKILL_DIR="<cvm-ai-doctor skill directory>"
CONTENT=$(base64 -w 0 < "$SKILL_DIR/scripts/cluster_deep_cpu.sh")
```
```powershell
# Step A — Agent encodes locally (Windows PowerShell)
$SKILL_DIR = "<cvm-ai-doctor skill directory>"
$CONTENT = [Convert]::ToBase64String([IO.File]::ReadAllBytes("$SKILL_DIR\scripts\cluster_deep_cpu.sh"))
```
```bash
# Step B — have tencentcloud-infra execute it
tccli tat RunCommand \
  --region <region> \
  --InstanceIds '["ins-xxx"]' \
  --CommandType SHELL \
  --Timeout 60 \
  --Content "<output of Step A>"
```

> If the script does not exist, use the inline commands below.

**Fallback: inline commands**

```bash
# Find the processes consuming the most CPU
ps aux --sort=-%cpu | head -20

# Live load details (non-interactive, batch mode)
top -bn1 | head -30

# Check for CPU throttling (container scenarios)
cat /sys/fs/cgroup/cpu/cpu.stat 2>/dev/null | head -5 || echo "no-cgroup"

# Check IO wait (whether disk IO is causing CPU waiting)
iostat -x 1 3 2>/dev/null | tail -20 || vmstat 1 3
```

---

### Deep diagnosis of high memory usage

## ⚡ Script-first path: cluster_deep_memory.sh

If `scripts/cluster_deep_memory.sh` exists, **the Agent first encodes it locally, then has tencentcloud-infra execute it**:

```bash
# Step A — Agent encodes locally (Linux / macOS)
SKILL_DIR="<cvm-ai-doctor skill directory>"
CONTENT=$(base64 -w 0 < "$SKILL_DIR/scripts/cluster_deep_memory.sh")
```
```powershell
# Step A — Agent encodes locally (Windows PowerShell)
$SKILL_DIR = "<cvm-ai-doctor skill directory>"
$CONTENT = [Convert]::ToBase64String([IO.File]::ReadAllBytes("$SKILL_DIR\scripts\cluster_deep_memory.sh"))
```
```bash
# Step B — have tencentcloud-infra execute it
tccli tat RunCommand \
  --region <region> \
  --InstanceIds '["ins-xxx"]' \
  --CommandType SHELL \
  --Timeout 60 \
  --Content "<output of Step A>"
```

> If the script does not exist, use the inline commands below.

**Fallback: inline commands**

```bash
# Find the processes consuming the most memory
ps aux --sort=-%mem | head -20

# Memory details (including Buffers/Cached/Swap)
free -m && cat /proc/meminfo | grep -E 'MemTotal|MemFree|Cached|SwapTotal|SwapFree|Shmem'

# Whether there are OOM kill records
dmesg 2>/dev/null | grep -i 'oom\|killed' | tail -10

# Swap usage
swapon --show 2>/dev/null || cat /proc/swaps
```

---

### Deep diagnosis of high disk usage

## ⚡ Script-first path: cluster_deep_disk.sh

If `scripts/cluster_deep_disk.sh` exists, **the Agent first encodes it locally, then has tencentcloud-infra execute it**:

```bash
# Step A — Agent encodes locally (Linux / macOS)
SKILL_DIR="<cvm-ai-doctor skill directory>"
CONTENT=$(base64 -w 0 < "$SKILL_DIR/scripts/cluster_deep_disk.sh")
```
```powershell
# Step A — Agent encodes locally (Windows PowerShell)
$SKILL_DIR = "<cvm-ai-doctor skill directory>"
$CONTENT = [Convert]::ToBase64String([IO.File]::ReadAllBytes("$SKILL_DIR\scripts\cluster_deep_disk.sh"))
```
```bash
# Step B — have tencentcloud-infra execute it
tccli tat RunCommand \
  --region <region> \
  --InstanceIds '["ins-xxx"]' \
  --CommandType SHELL \
  --Timeout 90 \
  --Content "<output of Step A>"
```

> If the script does not exist, use the inline commands below.

**Fallback: inline commands**

```bash
# Find the largest directories
du -sh /var/log/* /home/* /tmp/* /opt/* 2>/dev/null | sort -hr | head -20

# Large files on the root partition
find / -maxdepth 5 -type f -size +500M 2>/dev/null | head -10

# Disk IO details
df -h && iostat -x 1 3 2>/dev/null | tail -20

# Check inode usage (inode exhaustion also causes disk-full errors)
df -i | head -10
```

---

### Deep diagnosis of SSH service anomalies

## ⚡ Script-first path: cluster_deep_ssh.sh

If `scripts/cluster_deep_ssh.sh` exists, **the Agent first encodes it locally, then has tencentcloud-infra execute it**:

```bash
# Step A — Agent encodes locally (Linux / macOS)
SKILL_DIR="<cvm-ai-doctor skill directory>"
CONTENT=$(base64 -w 0 < "$SKILL_DIR/scripts/cluster_deep_ssh.sh")
```
```powershell
# Step A — Agent encodes locally (Windows PowerShell)
$SKILL_DIR = "<cvm-ai-doctor skill directory>"
$CONTENT = [Convert]::ToBase64String([IO.File]::ReadAllBytes("$SKILL_DIR\scripts\cluster_deep_ssh.sh"))
```
```bash
# Step B — have tencentcloud-infra execute it
tccli tat RunCommand \
  --region <region> \
  --InstanceIds '["ins-xxx"]' \
  --CommandType SHELL \
  --Timeout 30 \
  --Content "<output of Step A>"
```

> If the script does not exist, use the inline commands below.

**Fallback: inline commands**

```bash
# sshd service details
systemctl status sshd --no-pager -l 2>/dev/null || service ssh status

# Recent sshd logs
journalctl -u sshd -n 50 --no-pager 2>/dev/null || \
  tail -50 /var/log/auth.log 2>/dev/null || \
  tail -50 /var/log/secure 2>/dev/null

# Whether sshd is listening on a port
ss -tlnp | grep ':22\|:2222'
```

---

### Deep diagnosis of network anomalies

## ⚡ Script-first path: cluster_deep_network.sh

If `scripts/cluster_deep_network.sh` exists, **the Agent first encodes it locally, then has tencentcloud-infra execute it**:

```bash
# Step A — Agent encodes locally (Linux / macOS)
SKILL_DIR="<cvm-ai-doctor skill directory>"
CONTENT=$(base64 -w 0 < "$SKILL_DIR/scripts/cluster_deep_network.sh")
```
```powershell
# Step A — Agent encodes locally (Windows PowerShell)
$SKILL_DIR = "<cvm-ai-doctor skill directory>"
$CONTENT = [Convert]::ToBase64String([IO.File]::ReadAllBytes("$SKILL_DIR\scripts\cluster_deep_network.sh"))
```
```bash
# Step B — have tencentcloud-infra execute it
tccli tat RunCommand \
  --region <region> \
  --InstanceIds '["ins-xxx"]' \
  --CommandType SHELL \
  --Timeout 30 \
  --Content "<output of Step A>"
```

> If the script does not exist, use the inline commands below.

**Fallback: inline commands**

```bash
# Connection state summary
ss -s

# TCP connection details (exclude ESTABLISHED, look only at abnormal states)
ss -nt state CLOSE-WAIT | wc -l
ss -nt state TIME-WAIT | wc -l
ss -nt state FIN-WAIT-1 | wc -l

# Network error statistics
ip -s link show | grep -A2 'errors\|dropped'

# DNS resolution latency
time dig +short google.com 2>/dev/null || time nslookup google.com 2>/dev/null
```

### Quick system log scan (comprehensive)

```bash
# ERROR/CRITICAL logs from the last hour
journalctl --since "1 hour ago" -p err -n 50 --no-pager 2>/dev/null || \
  tail -200 /var/log/syslog 2>/dev/null | grep -iE 'error|critical|fatal' | tail -30

# System reboot records
last reboot 2>/dev/null | head -5
```

---

## 5 Cross-Node Correlation Analysis Patterns

When the quick check finds several nodes anomalous at the same time, selectively run deep analysis according to the pattern.

---

### Pattern 1: Memory Cascade

**Trigger condition:** ≥ 3 nodes with `mem_pct > 80%` (simultaneously)

**Hypothesis:** pressure from a shared backend resource (DB/Cache) propagates to all frontend nodes

**Diagnostic steps:**

1. Run TAT on the high-memory nodes (through tencentcloud-infra):
   ```bash
   ps aux --sort=-%mem | head -10 | awk '{print $1,$2,$4,$11}'
   ```

2. Compare the top memory processes across nodes:
   - **Same process name** (e.g. `java`/`node`/`python`) → suspect an application-layer memory leak
   - **Different process names** → suspect saturation of a shared backend resource

3. If a shared DB/Cache is suspected, check the related instances through tencentcloud-infra:
   ```bash
   # MySQL instance monitoring (assuming a separate CDB)
   tccli monitor GetMonitorData \
     --Namespace QCE/CDB \
     --MetricName Connections \
     --Instances '[{"Dimensions":[{"Name":"InstanceId","Value":"cdb-xxx"}]}]' \
     --Period 300 --StartTime "..." --EndTime "..."

   # Redis monitoring
   tccli monitor GetMonitorData \
     --Namespace QCE/REDIS_MEM \
     --MetricName CpuUsage \
     --Instances '[{"Dimensions":[{"Name":"instanceid","Value":"crs-xxx"}]}]' \
     --Period 300 --StartTime "..." --EndTime "..."
   ```

**Conclusion template:**
```
🔍 Pattern 1: Memory Cascade
- Affected nodes: [order-api-1, order-api-2, order-api-3]
- The top memory process on every node is: java (order service)
- Hypothesis: the application has a memory leak; review the recent deployment records
- Recommendations: ① check recent code changes ② rolling-restart the service (see cluster-remediation.md)
```

---

### Pattern 2: Load Asymmetry

**Trigger condition:** `MAX(load_ratio) - MIN(load_ratio) > 0.5` (among healthy nodes)
and only 1-2 nodes are heavily loaded

**Hypothesis:** the load balancing configuration has failed, so traffic is concentrated on a few nodes

**Diagnostic steps:**

1. Check the load balancer backend status through tencentcloud-infra:
   ```bash
   tccli clb DescribeTargetHealth \
     --LoadBalancerId lb-xxx \
     --ListenerIds '["lbl-xxx"]'
   ```

2. Run TAT on the heavily loaded nodes and check the connection count:
   ```bash
   ss -nt state ESTABLISHED | wc -l
   netstat -n | grep ESTABLISHED | wc -l 2>/dev/null
   ```

3. Compare the connection counts between the heavily loaded nodes and the healthy nodes

**Conclusion template:**
```
🔍 Pattern 2: Load Asymmetry
- Heavily loaded node: [order-api-3] (load_ratio=1.8), all other nodes < 0.3
- order-api-3 ESTABLISHED connections: 1240, all other nodes < 50
- Hypothesis: the CLB backend health check is malfunctioning, so order-api-3 receives all the traffic
- Recommendations: ① check the CLB backend health status ② confirm the service processes on order-api-1/2 are healthy
```

---

### Pattern 3: Disk Growth Correlation

**Trigger condition:** ≥ 2 nodes with `disk_root_pct > 75%`

**Hypothesis:** the unified log policy has failed, so logs on all nodes have not been cleaned up

**Diagnostic steps:**

1. Run TAT on the high-disk nodes (through tencentcloud-infra):
   ```bash
   du -sh /var/log/* 2>/dev/null | sort -hr | head -10
   find /var/log -name "*.log" -mtime -1 2>/dev/null | xargs du -sh 2>/dev/null | sort -hr | head -5
   ```

2. Compare the large-file directories across nodes
3. Check whether the logrotate configuration is working:
   ```bash
   logrotate --debug /etc/logrotate.conf 2>&1 | tail -20
   ```

**Conclusion template:**
```
🔍 Pattern 3: Disk Growth Correlation
- Affected nodes: [order-api-2, order-api-3] (disks 78%, 82%)
- Largest directories on both nodes: /var/log/nginx (15GB and 18GB respectively)
- Most recent modification: today (access_log keeps growing)
- logrotate last run: 7 days ago (abnormal)
- Recommendations: force a log rotation (logrotate -f /etc/logrotate.conf) and set up daily automatic cleanup
```

---

### Pattern 4: Network Degradation

**Trigger condition:** ≥ 2 nodes report network-related anomalies (high abnormal connection counts in ss / DNS timeouts)

**Diagnostic steps:**

1. Run TAT on several nodes and collect network diagnostics:
   ```bash
   ss -s 2>/dev/null | grep -E 'TCP|UDP'; \
   ip -s link show 2>/dev/null | grep -A1 'errors:'; \
   echo "CLOSE_WAIT: $(ss -nt state CLOSE-WAIT 2>/dev/null | wc -l)"; \
   echo "TIME_WAIT: $(ss -nt state TIME-WAIT 2>/dev/null | wc -l)"
   ```

2. Check whether all nodes belong to the same availability zone (if so, this may be an AZ-level problem)
3. Check through tencentcloud-infra whether the security group was modified by mistake:
   ```bash
   tccli vpc DescribeSecurityGroups --SecurityGroupIds '["sg-xxx"]'
   ```

---

### Pattern 5: Service Failure Cascade

**Trigger condition:** the same systemd service fails on ≥ 2 nodes at the same time (SSH=inactive in the TAT snapshot, or discovered by the deep check)

**Diagnostic steps:**

1. Run TAT on the problem nodes and collect service status:
   ```bash
   systemctl status <service_name> --no-pager -l 2>/dev/null | tail -30; \
   journalctl -u <service_name> --since "1 hour ago" -n 30 --no-pager 2>/dev/null
   ```

2. Check the most recent deployment time:
   ```bash
   who /var/log/wtmp 2>/dev/null | tail -10
   ls -lt /etc/systemd/system/ | head -10
   ```

3. Check dependency services (e.g. a failed database connection causing the application to crash)

---

## Deep Analysis Report Format

```
## Deep Analysis Report — <node name/pattern name>
Time: <YYYY-MM-DD HH:MM>

### Diagnostic Conclusion
<root cause hypothesis: one sentence>

### Evidence
- <specific data 1>
- <specific data 2>

### Impact Scope
- Affected nodes: [...]
- Estimated duration: <X minutes/hours>

### Remediation Recommendations
1. 🟡 [immediately] <action 1>
2. 🟡 [today] <action 2>
3. 🟢 [this week] <action 3>

> See references/cluster-remediation.md for remediation execution
```

---

## Historical Trend Analysis (on demand)

If the user asks to see trends ("how has this server's CPU been over the past day"), pull historical metrics through tencentcloud-infra:

```bash
# Past 24 hours, one data point per hour
tccli monitor GetMonitorData \
  --Namespace QCE/CVM \
  --MetricName CpuUsage \
  --Period 3600 \
  --StartTime "<24 hours ago>" \
  --EndTime "<current time>" \
  --Instances '[{"Dimensions":[{"Name":"InstanceId","Value":"ins-xxx"}]}]'
```

Format the DataPoints array as a simple table so the user can judge the trend.
