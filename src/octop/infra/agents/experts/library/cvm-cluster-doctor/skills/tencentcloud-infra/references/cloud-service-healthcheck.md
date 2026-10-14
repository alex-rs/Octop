# Cloud Service Health Diagnosis

Your knowledge of the parameters of the Tencent Cloud monitoring metric and tag APIs may be outdated.
**Before executing, confirm the latest parameters with `tccli <service> <action> help`.**

> Perform a **deep health diagnosis** of the user's cloud services: analyze service performance through monitoring metrics (CPU/memory/disk/connections/latency, etc.) and output a health score plus a complete inspection report.
> **The whole process is read-only and changes nothing. By default no full scan is performed; the user must specify the inspection scope explicitly (except when the user explicitly asks for a full inspection).**

### ⚠️ Difference from "resource status inspection"

| auto-check-resource.md (resource status inspection) | This document (service health diagnosis) |
|---------------------------------------|------------------------|
| Checks whether domains/certificates are expiring and whether instances are running | Deep diagnosis of monitoring metrics such as CPU/memory/disk/connections/latency |
| No scoring system, only a status list | Has a health score (0-100) and a complete inspection report |
| Execute the scenarios directly | Must first let the user choose an inspection method (method 1/2/3) |

**If what the user asks for is:**
- "domain expiry", "certificate expiry", "whether the instance is running", "resource status" → ⛔ **do not use this document**; use `auto-check-resource.md`
- "service inspection", "health check", "diagnose the service", "performance check", "monitoring metrics" → ✅ **use this document**

---

## Execution Rules

### 🔒 Hard security limits (globally enforced)

> ⛔ **Any write operation is absolutely forbidden**. The entire inspection flow **only allows read/query operations** (Describe*, Get*),
> and **executing any create, modify, delete, restart, stop, or other write-type operation is strictly forbidden** (Create*, Modify*, Delete*, Start*, Stop*, Reboot*, Reset*, etc.).
> The purpose of the inspection is to diagnose and find problems; remediation advice is given in text only and **must not be executed on the user's behalf**.

> ⛔ **Full inspections are forbidden by default**. Do not automatically scan all resources in the account without the user explicitly specifying the inspection scope.
> The inspection scope must be clearly determined by the user through "method 1 (tag discovery)" or "method 2 (manual specification)".
> **Exception**: when the user explicitly requests a full inspection (such as "inspect all resources for me", "full scan", "check all instances in the account"),
> the full inspection may be run, following the "method 3 (full scan)" flow.

### Complete Inspection (trigger words: inspect services for me, check service health, service inspection, diagnose service status, cloud service health check, whether the service is normal)

When the user requests a service inspection, **the following rules must be strictly followed**:

1. **Determine the inspection method first**: the user must explicitly choose "method 1 (tag discovery)", "method 2 (manual specification)", or "method 3 (full scan)"; **do not skip this step and do not decide on your own**
2. **Determine the inspection scope first**: use Phase 0 to establish the list of resources to inspect; do not skip it
3. **Execute all phases in order**: Phase 0 → Phase 1 → Phase 2 → Phase 3 → Phase 4
4. **Run even on empty results**: when a resource type is not found, note "no resources of this type found" in the report
5. **Produce a complete report**: after all phases have been executed, you must output a complete report using the "inspection report template" at the end of this document
6. **Flag status**: for every check item, clearly flag the status (✅ normal / ⚠️ warning / ❌ abnormal)
7. **Read-only operations**: use only query-type APIs such as Describe* / Get* throughout, and never execute any change operation

### Single-Item Check

When the user requests only one specific check (such as "check Redis health" or "take a look at the database status"), you may run Phase 1 + Phase 2 for the specified resource type only, without executing every phase. The user must still provide an explicit resource ID, and you must not scan all resources yourself.

---

## Phase 0: Determine the Inspection Scope

### Step 1: Determine the region

Ask the user for the target region. If the user does not specify one, use `ap-guangzhou` by default and tell the user.

### Step 2: Let the user choose a resource association method

There are three ways to determine the inspection scope. **You must present the available methods to the user and let the user choose explicitly**; do not skip this automatically or decide for the user:

```
Please choose how the inspection resources are associated:

Method 1 (tag discovery): automatically discover all resources associated with a service through Tencent Cloud tags (Tag).
  Applies when: a unified service tag has already been applied to the cloud resources (such as Service=order-system).

Method 2 (manual specification): you manually provide the resource types and instance IDs to inspect.
  Applies when: no tags are configured, or you only want to inspect a few specific resources.

Method 3 (full scan): scan all known cloud resource types in the current region and inspect them one by one.
  ⚠️ Takes longer when there are many resources; use it only when you confirm you need a full check.

Enter 1, 2, or 3 to choose a method:
```

> ⛔ **Do not start an inspection when the user has not explicitly chosen a method.**
> If the user's request contains neither tag information nor resource IDs and does not explicitly ask for a full scan, you must first show the selection prompt above.
> If the user's request already contains tag information (such as "inspect resources with Service=xxx"), it can be treated as method 1 already chosen.
> If the user's request already contains concrete resource IDs (such as "inspect ins-xxx and cdb-xxx"), it can be treated as method 2 already chosen.
> If the user's request explicitly asks for a full scan (such as "inspect all resources for me", "full scan", "check all instances"), it can be treated as method 3 already chosen.

#### Method 1: Automatic discovery based on tags (Tag) (⭐ recommended)

Users associate different cloud resources of the same business through a unified tag. An agreed tag key might be `Service`, with a value such as the business name `order-system`.

**Steps**:

1. First ask the user for the service name or tag information
2. If the user is unsure which tags exist, query the existing tags first:

```bash
# query all tag keys under the account
tccli tag DescribeTagKeys --region ap-guangzhou

# query all tag values under a given tag key
tccli tag DescribeTagValues --TagKeys '["Service"]' --region ap-guangzhou
```

3. Query all resources associated through the tag:

```bash
tccli tag DescribeResourcesByTags --TagFilters '[{"TagKey":"Service","TagValue":["order-system"]}]' --region ap-guangzhou
```

4. From the results, group and summarize resources by the `ServiceType` field. **This is not limited to specific resource types**; every resource associated with the tag is included in the inspection scope.

Known resource type mapping (with a refined diagnostic plan):

| ServiceType | Product name | Monitor Namespace | Dimension Key |
|-------------|---------|-------------------|---------------|
| `cvm` | CVM cloud server | `QCE/CVM` | `InstanceId` |
| `cdb` | CDB MySQL | `QCE/CDB` | `InstanceId` |
| `redis` | Redis cache | `QCE/REDIS_MEM` | `instanceid` (lowercase) |
| `ckafka` | CKafka message queue | `QCE/CKAFKA` | `instanceId` |
| `lighthouse` | Lighthouse instance | `QCE/LIGHTHOUSE` | `InstanceId` |
| `cynosdb` | TDSQL-C MySQL | `QCE/CYNOSDB_MYSQL` | `InstanceId` |
| `mariadb` | MariaDB | `QCE/MARIADB` | `InstanceId` |
| `postgres` | PostgreSQL | `QCE/POSTGRES` | `resourceId` |
| `mongodb` | MongoDB | `QCE/CMONGO` | `target` |
| `clb` | Load balancer | `QCE/LB_PUBLIC` / `QCE/LB_PRIVATE` | `vip` |
| `nat` | NAT gateway | `QCE/NAT_GATEWAY` | `natId` |
| `es` | Elasticsearch | `QCE/CES` | `uInstanceId` |

**If you encounter a ServiceType that is not listed in the table above**, classify that resource as "unknown type" and follow the generic diagnostic flow (see the generic diagnosis parts of Phase 1 and Phase 2).

> ⚠️ **Note**: If the tag query returns no resources, the user may not have configured tags; guide the user to method 2.

#### Method 2: The user manually specifies resource IDs

When the user has not configured tags, or the tag query returns nothing, guide the user to provide the resource list manually:

```
Please tell me which cloud resources the service you want to inspect contains.
Please provide the resource type and instance ID, for example:
- CVM: ins-xxxx
- CDB: cdb-xxxx
- Redis: crs-xxxx
- CKafka: ckafka-xxxx
- CLB: lb-xxxx
- MongoDB: cmgo-xxxx
- Other resources: state the product type and instance ID

You can also provide a combination of tccli service name and instance ID directly, such as "postgres pg-xxxx".
```

> 💡 After the Agent receives the resource information from the user, it should identify the resource type automatically from the instance ID prefix or the user's description and map it to the corresponding tccli service name. If it cannot be identified, confirm the product type with the user.

#### Method 3: Full scan (only when the user explicitly requests it)

> ⚠️ Use this method **only when the user proactively and explicitly requests a full inspection** (such as "inspect all resources for me", "full scan", "check all instances").
> The Agent must not suggest or trigger this method on its own initiative.

**Steps**:

1. Confirm the region and the range of product types to scan with the user:

```
You have requested a full scan; please confirm:
- Region: ap-guangzhou (state it if you need another region)
- Scan scope: by default, all instances of the following product types are scanned:
  CVM, CDB, Redis, CKafka, Lighthouse, CLB, MongoDB, PostgreSQL, MariaDB, TDSQL-C, NAT gateway, Elasticsearch
- If you need to add or remove product types, please state them

Once confirmed, the scan begins.
```

2. After the user confirms, query the instance list of each product one by one:

```bash
# query product type by product type (Describe queries only, read-only operations)
tccli cvm DescribeInstances --region ap-guangzhou
tccli cdb DescribeDBInstances --region ap-guangzhou
tccli redis DescribeInstances --region ap-guangzhou
tccli ckafka DescribeInstances --region ap-guangzhou
tccli lighthouse DescribeInstances --region ap-guangzhou
# ... other products work the same way
```

3. Aggregate all discovered instances, build the resource list, and then proceed to step 3.

> 💡 A full scan may involve a large number of resources and API calls. If there are too many resources (more than 50), inspecting them in batches or narrowing the scope is recommended.

### Step 3: Build the resource list

Whichever method is used, finally build a resource list table and show it to the user for confirmation:

```
The following resources were discovered; the inspection is about to begin:

| No. | Resource type | Resource ID | Name | Region | Diagnostic mode |
|------|---------|---------|------|------|---------|
| 1    | CVM     | ins-xxx | web-01 | ap-guangzhou | refined |
| 2    | CDB     | cdb-xxx | mysql-01 | ap-guangzhou | refined |
| 3    | Redis   | crs-xxx | cache-01 | ap-guangzhou | refined |
| 4    | CKafka  | ckafka-x | mq-01 | ap-guangzhou | refined |
| 5    | CLB     | lb-xxx  | slb-01 | ap-guangzhou | generic |
```

> 💡 "Refined" mode uses preset core metrics and dedicated thresholds; "generic" mode discovers metrics dynamically through `DescribeBaseMetrics` and uses generic thresholds.

---

## Phase 1: Resource Status Check

For each resource in the resource list, check the basic running status.

### CVM instance status

```bash
tccli cvm DescribeInstances --region ap-guangzhou \
  --InstanceIds '["ins-xxxxx"]'
```

Fields to look at:
- `InstanceState`: should be `RUNNING` (not `STOPPED` / `SHUTDOWN` / `TERMINATING`)
- `ExpiredTime`: check whether it is about to expire (within 30 days)
- `RestrictState`: whether it is isolated (`PROTECTIVELY_ISOLATED`)

### CDB MySQL instance status

```bash
tccli cdb DescribeDBInstances --region ap-guangzhou \
  --InstanceIds '["cdb-xxxxx"]'
```

Fields to look at:
- `Status`: should be `1` (running)
- `DeadlineTime`: check whether it is about to expire
- `TaskStatus`: should be `0` (no task)

### Redis instance status

```bash
tccli redis DescribeInstances --region ap-guangzhou \
  --InstanceId crs-xxxxx
```

Fields to look at:
- `Status`: should be `2` (running)
- `DeadlineTime`: check whether it is about to expire

### CKafka instance status

```bash
tccli ckafka DescribeInstances --region ap-guangzhou \
  --InstanceId ckafka-xxxxx
```

Fields to look at:
- `Status`: should be `1` (running)
- `ExpireTime`: check whether it is about to expire

### Generic status check for other/unknown resource types

For resource types that are not in the known list above, run the following generic discovery flow:

**Step 1: Determine the tccli service name and query API**

```bash
# try using tccli to view the operations the service supports
tccli <service-name> help
```

Most Tencent Cloud products follow the `Describe*Instances` or `Describe*` pattern to query instance information.

**Step 2: Query the instance details**

```bash
# try the common query patterns
tccli <service-name> DescribeInstances help
# or
tccli <service-name> Describe<resource-type>s help
```

**Step 3: Extract the key status fields from the results**

Generic fields to look at (most products have them):
- `Status` / `InstanceState` / `State`: running status
- `ExpiredTime` / `DeadlineTime` / `ExpireTime`: expiry time
- `InstanceId` / resource ID: used for subsequent monitoring queries

> 💡 **Tip**: If the instance details cannot be queried through tccli (e.g. the product does not support DescribeInstances), skip the status check and go straight to Phase 2 to try pulling monitoring data.

### Annotating status check results

| Status | Annotation |
|------|------|
| Running | ✅ normal |
| Stopped but not isolated | ⚠️ warning |
| Isolated/in arrears | ❌ abnormal |
| Expires within 30 days | ⚠️ expiring soon |

---

## Phase 2: Monitoring Metric Diagnosis

Pull the core monitoring metrics of each resource through `tccli monitor GetMonitorData` and compare them against the thresholds to decide whether they are abnormal.

### Time range

By default, pull the data of **the last 1 hour**, with a granularity of 300 seconds (5 minutes). The time range can be adjusted to the user's needs.

```
StartTime: current time - 1 hour (ISO 8601 format)
EndTime: current time (ISO 8601 format)
Period: 300
```

### CVM monitoring metrics

| Metric | MetricName | Normal range | Warning threshold | Critical threshold |
|------|-----------|---------|---------|---------|
| CPU utilization | `CpuUsage` | < 70% | ≥ 70% | ≥ 90% |
| Memory utilization | `MemUsage` | < 70% | ≥ 70% | ≥ 90% |
| Base CPU utilization | `BaseCpuUsage` | < 70% | ≥ 70% | ≥ 85% |
| TCP connections | `TcpCurrEstab` | stable | continuously growing | sudden 50%+ increase |
| Internal network outbound bandwidth | `LanOuttraffic` | < 60% | ≥ 60% | ≥ 80% |

```bash
# CVM CPU utilization
tccli monitor GetMonitorData --region ap-guangzhou \
  --Namespace QCE/CVM \
  --MetricName CpuUsage \
  --Instances '[{"Dimensions":[{"Name":"InstanceId","Value":"ins-xxxxx"}]}]' \
  --Period 300 \
  --StartTime "2026-03-26T08:00:00+08:00" \
  --EndTime "2026-03-26T09:00:00+08:00"
```

> 💡 For other CVM metrics (MemUsage, BaseCpuUsage, etc.), just replace `--MetricName`; the Namespace and Dimensions format stays the same.

### CDB MySQL monitoring metrics

| Metric | MetricName | Normal range | Warning threshold | Critical threshold |
|------|-----------|---------|---------|---------|
| CPU utilization | `CpuUseRate` | < 60% | ≥ 60% | ≥ 80% |
| Memory utilization | `MemoryUseRate` | < 70% | ≥ 70% | ≥ 85% |
| Disk utilization | `VolumeRate` | < 70% | ≥ 70% | ≥ 85% |
| Replication delay | `SlaveDelay` | 0s | ≥ 5s | ≥ 10s |
| Connection utilization | `ConnectionUseRate` | < 60% | ≥ 60% | ≥ 80% |
| Slow queries | `SlowQueries` | 0 | > 0 | > 10/min |

```bash
# CDB MySQL CPU utilization
tccli monitor GetMonitorData --region ap-guangzhou \
  --Namespace QCE/CDB \
  --MetricName CpuUseRate \
  --Instances '[{"Dimensions":[{"Name":"InstanceId","Value":"cdb-xxxxx"}]}]' \
  --Period 300 \
  --StartTime "2026-03-26T08:00:00+08:00" \
  --EndTime "2026-03-26T09:00:00+08:00"
```

### Redis monitoring metrics

| Metric | MetricName | Normal range | Warning threshold | Critical threshold |
|------|-----------|---------|---------|---------|
| CPU utilization | `CpuUtil` | < 60% | ≥ 60% | ≥ 80% |
| Memory utilization | `MemUtil` | < 60% | ≥ 60% | ≥ 80% |
| Connections | `Connections` | stable | near 80% of the limit | near 95% of the limit |
| Command execution errors | `CmdErr` | 0 | > 0 | persistently > 0 |
| Average execution latency | `AvgExecLatency` | < 5ms | ≥ 5ms | ≥ 10ms |

```bash
# Redis memory utilization
tccli monitor GetMonitorData --region ap-guangzhou \
  --Namespace QCE/REDIS_MEM \
  --MetricName MemUtil \
  --Instances '[{"Dimensions":[{"Name":"instanceid","Value":"crs-xxxxx"}]}]' \
  --Period 300 \
  --StartTime "2026-03-26T08:00:00+08:00" \
  --EndTime "2026-03-26T09:00:00+08:00"
```

> ⚠️ **Note**: The Redis Namespace is `QCE/REDIS_MEM` (not `QCE/REDIS`), and the Dimension name is the lowercase `instanceid`.

### CKafka monitoring metrics

| Metric | MetricName | Normal range | Warning threshold | Critical threshold |
|------|-----------|---------|---------|---------|
| Message backlog | `MsgHeap` | stable/declining | continuously growing | growing sharply |
| Produce rate | `ProducerTps` | stable | down 30%+ | down 50%+ |
| Consume rate | `ConsumerTps` | stable | down 30%+ | down 50%+ |
| Disk utilization | `DiskUsage` | < 60% | ≥ 60% | ≥ 80% |

```bash
# CKafka message backlog
tccli monitor GetMonitorData --region ap-guangzhou \
  --Namespace QCE/CKAFKA \
  --MetricName MsgHeap \
  --Instances '[{"Dimensions":[{"Name":"instanceId","Value":"ckafka-xxxxx"}]}]' \
  --Period 300 \
  --StartTime "2026-03-26T08:00:00+08:00" \
  --EndTime "2026-03-26T09:00:00+08:00"
```

### Generic monitoring diagnosis for other/unknown resource types

For resources that are not in the known product list above, complete the monitoring diagnosis through **dynamic discovery**.

**Step 1: Determine the Monitor Namespace**

First try to find the Namespace from the known mapping table in Phase 0. If it is not in the table, use the following command to query all products that support monitoring:

```bash
tccli monitor DescribeProductList --Module monitor
```

Match the Namespace corresponding to that resource type from the results.

**Step 2: Dynamically obtain the list of available metrics**

```bash
# query all monitoring metrics supported under that Namespace
tccli monitor DescribeBaseMetrics --Namespace <Namespace>
```

Each metric in the result contains:
- `MetricName`: the English name of the metric
- `MetricCName`: the Chinese name of the metric
- `Dimensions`: the dimensions required
- `Unit`: the unit (%, MB, Count, ms, etc.)
- `Periods`: the supported statistical granularities

**Step 3: Filter the core metrics from the metric list**

Automatically filter the metrics to pull according to the following priority (select at most 6):

| Priority | Metric keywords (matched against MetricName or MetricCName) | Description |
|--------|----------------------------------------------|------|
| 🔴 P0 | `Cpu`, `CpuUsage`, `CpuUtil`, `CpuUseRate` | CPU utilization |
| 🔴 P0 | `Mem`, `Memory`, `MemUsage`, `MemUtil` | Memory utilization |
| 🟠 P1 | `Disk`, `Volume`, `Storage`, `DiskUsage`, `VolumeRate` | Disk/storage utilization |
| 🟠 P1 | `Connection`, `Conn`, `ActiveConn` | Connections/connection utilization |
| 🟡 P2 | `Latency`, `Delay`, `ResponseTime` | Latency/response time |
| 🟡 P2 | `Error`, `Fail`, `Reject` | Errors/failure rate |
| 🔵 P3 | `Traffic`, `Bandwidth`, `InBandwidth`, `OutBandwidth` | Traffic/bandwidth |
| 🔵 P3 | `Qps`, `Tps`, `Requests` | Request volume/throughput |

> 💡 **Matching logic**: against the metric list returned by `DescribeBaseMetrics`, perform case-insensitive partial matching on the keywords above. For each priority, select the first matching metric. If a priority has no match, skip it.

**Step 4: Pull the metric data**

```bash
# generic pull template (replace Namespace, MetricName, Dimension)
tccli monitor GetMonitorData --region ap-guangzhou \
  --Namespace <Namespace> \
  --MetricName <MetricName> \
  --Instances '[{"Dimensions":[{"Name":"<DimensionKey>","Value":"<resource ID>"}]}]' \
  --Period 300 \
  --StartTime "<1 hour ago>" \
  --EndTime "<current time>"
```

> ⚠️ The **Name value of the Dimension** comes from the `Dimensions` field returned by `DescribeBaseMetrics`; do not hard-code guesses.

**Step 5: Generic threshold judgement**

For metrics without preset thresholds, judge by the following generic rules:

| Metric type | Unit | Normal range | Warning threshold | Critical threshold |
|---------|------|---------|---------|---------|
| Utilization type | `%` | < 70% | ≥ 70% | ≥ 90% |
| Latency type | `ms` | < 100ms | ≥ 100ms | ≥ 500ms |
| Error/failure type | `Count` | 0 | > 0 | persistently > 0 |
| Connection-count type | `Count` | stable, not growing | continuously growing | sudden 50%+ increase |
| Traffic/throughput type | `MB`/`Count` | stable | abnormal fluctuation 30%+ | abnormal fluctuation 50%+ |

> 💡 For utilization-type metrics (unit %), threshold judgement is the most reliable. Other metric types lack an absolute baseline and should be judged together with the trend (whether they spike or plunge). Mark these in the report as **generic threshold references** and recommend that users adjust them according to their actual business.

### How to analyze the metric data

After the monitoring data has been pulled, analyze it as follows:

1. **Compute the average**: take the average of all data points in the time window and compare it with the threshold
2. **Compute the maximum**: take the peak value in the time window to identify whether there was a spike
3. **Trend judgement**: compare data points before and after to decide whether the metric is stable, rising, or falling

---

## Phase 3: Alarm Policy Coverage Check

Check whether these resources are covered by Monitor alarm policies.

According to the product types involved in the resource list, query the alarm policies of the corresponding Namespace one by one:

```bash
# query alarm policies by Namespace (replace with the actual Namespaces involved)
tccli monitor DescribeAlarmPolicies --region ap-guangzhou --Module monitor --Namespace <Namespace>
```

Examples of alarm policy queries for common products:
```bash
tccli monitor DescribeAlarmPolicies --region ap-guangzhou --Module monitor --Namespace QCE/CVM
tccli monitor DescribeAlarmPolicies --region ap-guangzhou --Module monitor --Namespace QCE/CDB
tccli monitor DescribeAlarmPolicies --region ap-guangzhou --Module monitor --Namespace QCE/REDIS_MEM
tccli monitor DescribeAlarmPolicies --region ap-guangzhou --Module monitor --Namespace QCE/CKAFKA
```

> 💡 For unknown resource types, use the Namespace determined in Phase 2 to query alarm policies. If the Namespace cannot be determined, note "alarm coverage could not be checked".

Key points to check:
- Whether each resource is covered by at least one alarm policy
- Whether the alarm policies cover the core metrics (CPU, memory, disk, etc.)
- Whether alarm notification channels are configured (SMS, email, WeChat, etc.)

Annotating rules:
- ✅ Covered by an alarm policy that includes the core metrics
- ⚠️ Has an alarm policy but is missing coverage of key metrics
- ❌ Not covered by any alarm policy

---

## Phase 4: Health Scoring and Report

### Per-resource health score

Based on the results of Phase 1 (status) and Phase 2 (metrics), compute a health score for each resource:

| Score range | Label | Criteria |
|---------|------|---------|
| 80-100 points | ✅ healthy | The resource is running and all core metrics are within the normal range |
| 60-79 points | ⚠️ sub-healthy | The resource is running and 1-2 metrics have reached the warning threshold |
| 0-59 points | ❌ abnormal | The resource is not running, or a metric has reached the critical threshold |

**Deduction rules**:
- Base score: 100 points
- Each metric that reaches the **warning threshold**: deduct 10 points
- Each metric that reaches the **critical threshold**: deduct 20 points
- The resource is **not running**: drop straight to 40 points
- The resource is **isolated/in arrears**: drop straight to 20 points
- **No alarm policy coverage**: deduct 5 points
- **Generic-diagnosis resources** (non-refined metrics): mark `[generic diagnosis]` in the report and tell the user that the thresholds are reference values

### Overall service health

```
Service health = the lowest health score among all resources (weakest-link principle)

  ✅ healthy:     lowest resource score ≥ 80
  ⚠️ sub-healthy: lowest resource score between 60-79
  ❌ abnormal:    lowest resource score < 60
```

> The weakest-link principle is used (taking the lowest score), because a single abnormal critical resource can affect the availability of the entire service.

---

## Inspection Report Template

After all the phases above have been executed, you **must** output an inspection report in the following format:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏥 Cloud Service Health Inspection Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 Service name: <service name or tag value>
📌 Inspection time: <current time>
📌 Inspection region: <region>
📌 Total resources: <resource count>

┌─────────────────────────────────────────────────┐
│ 📊 Overall service health: ✅/⚠️/❌ <status> (<score>/100)  │
└─────────────────────────────────────────────────┘

## Resource List and Status

| Resource type | Resource ID | Name | Running status | Health |
|---------|--------|------|---------|--------|
| CVM     | ins-xxx | web-01  | ✅ RUNNING | 95/100 |
| CDB     | cdb-xxx | mysql-01 | ✅ running | 62/100 ⚠️ |
| Redis   | crs-xxx | cache-01 | ✅ running | 90/100 |
| CKafka  | ckafka-x| mq-01   | ✅ running | 85/100 |
| CLB     | lb-xxx  | slb-01  | ✅ running | 88/100 [generic diagnosis] |
| MongoDB | cmgo-xx | mongo-01 | ✅ running | 78/100 ⚠️ [generic diagnosis] |

## Abnormal/Warning Metric Details

(only the resources with warnings or abnormalities are listed)

### ⚠️ CDB mysql-01 (cdb-xxx) — health 62/100

| Metric | Current value (average) | Peak | Threshold | Status |
|------|------------|------|------|------|
| CPU utilization | 82% | 91% | warning ≥60% critical ≥80% | ❌ critical |
| Memory utilization | 72% | 78% | warning ≥70% critical ≥85% | ⚠️ warning |
| Disk utilization | 87% | 89% | warning ≥70% critical ≥85% | ❌ critical |
| Replication delay | 0s | 0s | warning ≥5s critical ≥10s | ✅ normal |
| Connection utilization | 45% | 52% | warning ≥60% critical ≥80% | ✅ normal |
| Slow queries | 23/5min | 45 | > 0 watch | ⚠️ watch |

## Alarm Policy Coverage

| Resource | Alarm coverage | Description |
|------|---------|------|
| CVM ins-xxx | ✅ covered | CPU/memory/disk alarms are configured |
| CDB cdb-xxx | ❌ not covered | Configuring an alarm policy is recommended |
| Redis crs-xxx | ✅ covered | Memory/connection alarms are configured |
| CKafka ckafka-x | ⚠️ partially covered | Missing a message backlog alarm |

## Remediation Advice (by priority)

> ⚠️ The following are suggestions, **for reference only; the user must confirm them and execute them personally**. The inspection process does not automatically execute any remediation operation.

1. 🔴 [urgent] <resource name> <specific problem>, recommended <remediation plan>
2. 🟠 [high] <resource name> <specific problem>, recommended <remediation plan>
3. 🟡 [medium] <resource name> <specific problem>, recommended <remediation plan>
4. 🔵 [low] <resource name> <specific problem>, recommended <remediation plan>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## API Quick Reference

| Function | Service | API |
|------|------|------|
| Query tag keys | tag | `DescribeTagKeys` |
| Query tag values | tag | `DescribeTagValues` |
| Query resources by tag | tag | `DescribeResourcesByTags` |
| Query CVM instances | cvm | `DescribeInstances` |
| Query CDB instances | cdb | `DescribeDBInstances` |
| Query Redis instances | redis | `DescribeInstances` |
| Query CKafka instances | ckafka | `DescribeInstances` |
| Query monitoring data | monitor | `GetMonitorData` |
| Query alarm policies | monitor | `DescribeAlarmPolicies` |
| Query the metrics a product supports | monitor | `DescribeBaseMetrics` |
| Query the monitoring product list | monitor | `DescribeProductList` |

---

## Monitor Namespace and Dimension Quick Reference

### Known products quick reference

| Cloud product | ServiceType | Namespace | Dimension Key |
|--------|-------------|-----------|---------------|
| CVM | `cvm` | `QCE/CVM` | `InstanceId` |
| CDB MySQL | `cdb` | `QCE/CDB` | `InstanceId` |
| Redis | `redis` | `QCE/REDIS_MEM` | `instanceid` (lowercase) |
| CKafka | `ckafka` | `QCE/CKAFKA` | `instanceId` |
| Lighthouse | `lighthouse` | `QCE/LIGHTHOUSE` | `InstanceId` |
| TDSQL-C MySQL | `cynosdb` | `QCE/CYNOSDB_MYSQL` | `InstanceId` |
| MariaDB | `mariadb` | `QCE/MARIADB` | `InstanceId` |
| PostgreSQL | `postgres` | `QCE/POSTGRES` | `resourceId` |
| MongoDB | `mongodb` | `QCE/CMONGO` | `target` |
| CLB (public network) | `clb` | `QCE/LB_PUBLIC` | `vip` |
| NAT gateway | `nat` | `QCE/NAT_GATEWAY` | `natId` |
| Elasticsearch | `es` | `QCE/CES` | `uInstanceId` |

> ⚠️ Pay special attention:
> - The Redis Namespace is `QCE/REDIS_MEM`, and the Dimension key is the **lowercase** `instanceid`
> - The PostgreSQL Dimension key is `resourceId` (not InstanceId)
> - The MongoDB Dimension key is `target`

### Namespace discovery for unknown products

If a product is not in the table above, determine the Namespace and Dimension through the following steps:

```bash
# 1. query the list of all products that support monitoring
tccli monitor DescribeProductList --Module monitor

# 2. after finding the matching Namespace, query the metrics and dimensions under it
tccli monitor DescribeBaseMetrics --Namespace <Namespace>
```

The `Dimensions` field of each metric returned by `DescribeBaseMetrics` is exactly the dimension information that product requires.

---

## When to Use

| Scenario | Recommendation |
|------|------|
| The user says "service inspection", "health check", "diagnose the service" | ✅ First let the user choose method 1, method 2, or method 3, then run the complete Phase 0-4 flow |
| The user says "look at CPU/memory utilization", "monitoring metric anomaly", "performance check" | ✅ The user must provide a resource ID; run only the corresponding product part of Phase 2 |
| The user says "check all my servers" but does not explicitly ask for a full scan | ⛔ Do not run a full scan; guide the user to a tag-based or manually specified scope |
| The user explicitly asks for "a full inspection/scan of all resources" | ✅ After confirming the region and product scope, follow method 3 (full scan) |
| The user says "domain expiry", "certificate expiry", "is the resource expiring" | ⛔ **Do not use this document**; use references/auto-check-resource.md |
| The user says "check instance status", "is the instance running", "cloud disk status" | ⛔ **Do not use this document**; use references/auto-check-resource.md |
| The user says "resource inspection", "batch check resource status" | ⛔ **Do not use this document**; use references/auto-check-resource.md |
| The user wants a security check/security audit | ⛔ Do not use this document; use references/cvm-security-check.md |
| The user wants to deploy an application or set up a website | ⛔ Do not use this document; use the corresponding deployment/website-setup reference |
