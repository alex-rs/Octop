# Cluster Remediation Operations

> **Risk-gated guide to cluster-level remediation operations.**
> All operations are performed through the tencentcloud-infra skill (TAT or cloud API).
> **Remediation must be serial: after each node, verify recovery before moving on to the next.**

---

## Risk Level System

### 🟢 Automatic Execution (no confirmation needed; read-only or low risk)
- Pull instance state and monitoring metrics
- Run read-only diagnostic commands via TAT (ps, df, ss, journalctl, cat)
- Show reports and recommendations

### 🟡 Single Confirmation (reversible service-level operations)
**You must inform the user before executing, and only proceed after they confirm:**
- Restart a single service via TAT: `systemctl restart <service>`
- Clean up temporary files in /tmp via TAT: `find /tmp -mtime +7 -delete`
- Force log rotation via TAT: `logrotate -f /etc/logrotate.conf`
- Clean up old log files via TAT (only those older than 7 days)

**Confirmation prompt template:**
```
⚠️ About to run on <N> nodes: systemctl restart nginx
Impact: the nginx service will restart for about 15-30 seconds, during which that node serves no traffic
Reversible: yes (it recovers automatically after the restart)
The load balancer will remove the node automatically once its health check fails

Confirm execution? (reply "yes" to continue)
```

### 🔴 Explicit Confirmation (cloud instance lifecycle, major impact)
**The user must explicitly say "confirm restart ins-xxx" before you execute:**
- Restart an instance: `tccli cvm RebootInstances`
- Stop an instance: `tccli cvm StopInstances`
- Start an instance: `tccli cvm StartInstances`

**Confirmation prompt template:**
```
🔴 High-risk operation: about to restart instance ins-xxx (order-api-3)
---
Impact:
- The instance will be unavailable for about 1-3 minutes (during the restart)
- Connections currently in progress will be interrupted
- If CLB health checks are configured, traffic will shift to the other nodes automatically

Precautions:
- Current number of RUNNING nodes in the cluster: 3/4
- After the restart only 2/4 nodes will handle traffic; please confirm the remaining nodes have enough capacity

To continue, reply explicitly: confirm restart ins-xxx
```

### 💀 Never Execute (even if the user explicitly asks)
- **Restarting ≥ 50% of the nodes at the same time** (may make the whole service unavailable)
- `rm -rf` on any directory
- `DROP TABLE` / `DELETE FROM`
- Deleting /etc/ssh or the sshd configuration
- Emptying an entire log directory (cleaning old files is allowed; clearing the current logs is not)

When such a request comes in, reply:
```
❌ This operation is extremely risky (it affects the whole cluster's availability), so it cannot be executed.

Safe alternatives:
1. Restart node by node (2 minutes apart, at most 1 node at a time)
2. Confirm the instance is healthy in the Tencent Cloud console before acting

If the operation is truly necessary, please do it manually in the Tencent Cloud console and notify the relevant team in advance.
```

---

## Serial Remediation Principles

**Core rule: never operate on more than one node concurrently**

```
Correct flow:
  node1 → run the operation → wait 10 seconds → verify recovery →
  node2 → run the operation → wait 10 seconds → verify recovery →
  node3 → ...

Wrong approach (forbidden):
  node1, node2, and node3 run the operation at the same time ❌
```

Maximum concurrency: **1 node** (no matter how many nodes the cluster has)

---

## Common Remediation Playbook

### Operation A: Restart a Service in the Cluster (🟡 medium risk)

**Scenario:** a service (such as nginx/java/node) has crashed or is responding abnormally

**Execution flow:**

```
1. Confirm the scope (which nodes?)
2. Print the risk notice and wait for user confirmation

3. Run TAT on node 1 (through tencentcloud-infra):
   tccli tat RunCommand \
     --InstanceIds '["ins-xxx"]' \
     --CommandType SHELL --Timeout 30 \
     --Content "$(printf '%s' 'systemctl restart nginx' | base64 -w 0)"

4. Wait for TAT to finish (poll DescribeInvocationTasks)

5. Verify the service recovered (run via TAT):
   systemctl is-active nginx && echo "OK" || echo "FAILED"

6. If verification passes, wait 10 seconds and run the same operation on node 2
7. If verification fails, pause and report
```

### Operation B: Clean Up Disk Space (🟡 medium risk)

**Scenario:** disk usage > 80%

**Execution flow (clean only safe files; never delete business data):**

```bash
# Clean /tmp files older than 7 days
find /tmp -mtime +7 -delete 2>/dev/null && echo "tmp cleaned"

# Force log rotation
logrotate -f /etc/logrotate.conf 2>/dev/null && echo "logrotate done"

# Clean old compressed logs (keep the newest 3 *.gz files)
find /var/log -name "*.gz" | sort | head -n -3 | xargs rm -f 2>/dev/null && echo "old gz cleaned"
```

**Do not execute:** deleting any .log file (they are being written to); do not clear the current logs in /var/log/\*

### Operation C: Restart an Instance (🔴 high risk)

**Scenario:** a node is unresponsive, the kernel is deadlocked, or TAT cannot reach it

**Execution flow:**

```
1. Confirm the node's state: DescribeInstances
2. Confirm the CLB health check has already removed the node (otherwise traffic will be lost during the restart)
3. Print the 🔴 high-risk notice and wait for explicit user confirmation

4. Execute the restart through tencentcloud-infra:
   tccli cvm RebootInstances \
     --region <region> \
     --InstanceIds '["ins-xxx"]' \
     --StopType SOFT

5. Poll DescribeInstances every 10 seconds until InstanceState = RUNNING
   Maximum wait: 10 minutes (600 seconds)

6. Once the instance is RUNNING, wait another 30 seconds for the system services to finish starting

7. Run a recovery check via TAT:
   systemctl is-active sshd && \
   uptime && \
   free -m | awk '/Mem:/{print "MEM:", $3"/"$2, "MB"}' && \
   df / | awk 'NR==2{print "DISK:", $5}'

8. Update the MEMORY.md diagnosis history
```

### Operation D: Start a Stopped Instance (🔴 high risk)

**Scenario:** a STOPPED instance is found in the cluster and it was not a planned shutdown

```
1. Confirm first: ask the user whether stopping this instance was planned
2. If it was not planned, print the 🔴 notice and wait for confirmation

3. Start it through tencentcloud-infra:
   tccli cvm StartInstances \
     --region <region> \
     --InstanceIds '["ins-xxx"]'

4. Poll DescribeInstances until RUNNING
5. Wait 60 seconds (for services to start)
6. Verify via TAT (same as operation C step 7)
```

---

## Post-Remediation Verification Criteria

After the operation completes, use the following criteria to decide whether the fix succeeded:

| Metric | Success criterion |
|------|---------|
| sshd status | `systemctl is-active sshd` = `active` |
| Target service | `systemctl is-active <service>` = `active` |
| Disk | `disk_root_pct < 80%` (after cleanup) |
| Instance state | `DescribeInstances InstanceState` = `RUNNING` |
| System load | `load/ncpu < 1.0` (within 5 minutes of the restart) |

---

## Operation Logging

After every remediation operation, write to the MEMORY.md diagnosis history:

```markdown
### <YYYY-MM-DD HH:MM> — Cluster remediation operation
- **Symptom**: <issue reported by the user>
- **Affected nodes**: [ins-xxx, ins-yyy]
- **Actions**: <what was executed>
- **Result**: <success/partial failure>
- **Verification**: <verification commands and results>
```
