# Cluster Node Discovery

> This document guides the Agent on how to discover, validate, and persist the cluster node list.
> All cloud API calls are made through the **tencentcloud-infra** skill.

---

## Prerequisite Check: OAuth Credential Validity

Before every cluster operation, you **must first validate the credentials** (OAuth Token expires after 2 hours).

For how to do this, see **references/skill-collaboration-tencentcloud.md — the "OAuth Credential Check" protocol**.

- Credentials valid → continue
- Credentials expired or missing → guide the user to refresh them, then continue

---

## Discovery Methods (highest to lowest priority)

### Method A: MEMORY.md Cache (fastest, use first)

1. Read the MEMORY.md `cluster_config.last_discovery` timestamp
2. If it is **< 1 hour** old, use `cluster_config.known_nodes` directly and skip the API calls
3. If it is ≥ 1 hour old, run methods B/C/D to rediscover and update the cache

### Method B: Tag Filtering (recommended, suited to long-lived stable clusters)

Call the tencentcloud-infra skill and run:

```bash
tccli cvm DescribeInstances \
  --region <region> \
  --Filters '[{"Name":"tag:<tag_key>","Values":["<tag_value>"]}]' \
  --Limit 100
```

Extract the following from the response for each instance:
- `InstanceId`: unique instance identifier (e.g. `ins-abc123`)
- `InstanceName`: instance name
- `PrivateIpAddresses[0]`: private IP
- `PublicIpAddresses[0]`: public IP (may be empty)
- `InstanceState`: current state (RUNNING/STOPPED/SHUTDOWN, etc.)
- `Placement.Zone`: availability zone

**Multi-region handling:**
If MEMORY.md `cluster_config.additional_regions` is non-empty, call DescribeInstances once per region and merge the results.

### Method C: Explicit Instance ID List (precise control)

```bash
tccli cvm DescribeInstances \
  --InstanceIds '["ins-xxx","ins-yyy","ins-zzz"]'
```

### Method D: Full Discovery (account-wide, use with caution)

```bash
tccli cvm DescribeInstances --region <region> --Limit 100
```

⚠️ A large account may have many instances; confirm the user's intent before using full mode.
When there are more than 100 instances, paginate (increment Offset).

---

## TAT Agent Availability Check

After discovering nodes, verify whether the TAT automation assistant is available (CVM instances only; Lighthouse has no TAT):

```bash
tccli tat DescribeAutomationAgentStatus \
  --InstanceIds '["ins-xxx","ins-yyy"]'
```

- Status `Online` → TAT available, run the full 3-layer diagnosis
- Status `Offline` or `Installing` → **degraded mode**: use cloud metrics only (Layer 1 + Layer 2A),
  and mark the report with `⚠️ OS snapshot unavailable (TAT Agent offline)`

---

## User Guidance Flow (first-time cluster setup)

If MEMORY.md has no cluster configuration, guide the user through setup:

```
I need to know which CVM instances to manage. Please choose a configuration method:

1. Tag filtering (recommended): select in bulk by service tag
   Example: all instances with "Service=order-api"

2. Explicit instance IDs: type ins-xxx,ins-yyy directly

3. Full (all instances in the current region)

Please tell me which method you choose, plus the relevant information (tag key/value or instance ID list)?
```

After receiving the reply, run the corresponding discovery method, then **show the discovery result for the user to confirm**:

```
Discovered the following nodes (N in total):
- ins-abc123 (order-api-1) | 10.0.0.1 | RUNNING
- ins-def456 (order-api-2) | 10.0.0.2 | RUNNING
- ins-ghi789 (order-api-3) | 10.0.0.3 | STOPPED ⚠️

Save this cluster configuration? (Subsequent checks will use this list; no re-discovery needed within 1 hour)
```

---

## Writing to MEMORY.md

After the user confirms, write the following into MEMORY.md:

```markdown
## Cluster Configuration (cluster_config)

cluster:
  name: "<cluster name provided by the user, or the default prod-<region>>"
  region: <region>
  additional_regions: []
  instance_filter:
    method: tag                    # tag | id_list | all
    tag_key: <tag key>
    tag_value: <tag value>
  instance_ids: []                 # fill in when method=id_list
  last_discovery: "<ISO 8601 timestamp>"
  known_nodes:
    - id: ins-abc123
      name: order-api-1
      private_ip: 10.0.0.1
      state: RUNNING
      tat_available: true
    - id: ins-def456
      name: order-api-2
      private_ip: 10.0.0.2
      state: RUNNING
      tat_available: true
    - id: ins-ghi789
      name: order-api-3
      private_ip: 10.0.0.3
      state: STOPPED
      tat_available: false
```

---

## Special Handling for Lighthouse Instances

If a discovered instance is a Lighthouse (lightweight application server), a different command is required:

```bash
# Lighthouse uses tccli lighthouse, not tccli cvm
tccli lighthouse DescribeInstances --region <region>
```

Lighthouse instances have **no TAT support**, so only cloud monitoring metrics can be used (Layer 2A degraded mode).

---

## Error Handling

| Error case | Handling |
|---------|---------|
| DescribeInstances returns an empty list | Report "No instances found for this region/tag; please confirm the tag is correct" |
| API call fails (insufficient permissions) | Report "Please confirm the tccli credentials have the QcloudCVMReadOnlyAccess permission" |
| OAuth expired | Abort the current flow and guide the user to refresh the OAuth Token |
| More than 100 instances | Fetch in pages, incrementing Offset by 100 each time, until all are retrieved |
