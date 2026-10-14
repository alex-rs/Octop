# Cloud Server Security Check

Your knowledge of the parameters and limits of the Tencent Cloud security group rule and CAM permission APIs may be outdated.
**Before executing, confirm the latest parameters with `tccli <service> <action> help`.**

> Perform a comprehensive security check on cloud servers through the tccli command-line tool.

---

## Execution Rules

### Comprehensive Security Check (trigger words: comprehensive security check, security audit, security assessment, security inspection, check security configuration, check cloud server security)

When the user requests a comprehensive security check, **the following rules must be strictly followed**:

1. **Run every check scenario**: execute scenarios 1 through 6 in this document in order, **omitting nothing**
2. **Execute step by step**: each scenario must be completed strictly step by step according to its "Execution Steps"; do not skip any step
3. **Run even on empty results**: even when a scenario's query returns nothing (such as no public-network instances or no sub-users), you must still run the query and note "no related resources found" in the report
4. **Produce a comprehensive report**: after all scenarios have been executed, you must output a complete report using the "Comprehensive Security Assessment Report" template at the end of this document
5. **Flag risks**: for every check item, clearly flag the risk level (high/medium/low) and the status (✅ secure / ⚠️ warning / ❌ critical)

### Single-Item Security Check

When the user requests only one specific check (such as "check the security groups" or "check public exposure"), run only the corresponding scenario; there is no need to run every scenario.

---

## Scenario 1: Checking Security Group Rules for High-Risk Allowances

### Task Description
Please help me check all security group rules under the Tencent Cloud account and find configurations that may pose a security risk.

### Execution Steps

1. Use `tccli vpc DescribeSecurityGroups --region ap-beijing` to query the list of all security groups
2. Iterate over each security group and use `tccli vpc DescribeSecurityGroupPolicies --region ap-beijing --SecurityGroupId <sg-id>` to query its inbound and outbound rules
3. Check the inbound rules for the following high-risk configurations:
   - Rules whose source address is `0.0.0.0/0` (open to the entire internet)
   - Rules that allow high-risk ports (such as 22/SSH, 3389/RDP, 3306/MySQL, 6379/Redis, 27017/MongoDB)
   - Rules whose Action is `ACCEPT` with no source IP restriction
4. For each high-risk rule detected, output the security group ID, rule direction, port range, source address, and Action
5. Summarize the security assessment result and give remediation advice (such as restricting the source IP to the office network range)

---

## Scenario 2: Checking Cloud Server Public-Network Exposure

### Task Description
Please help me check the public-network exposure of all cloud server instances under the Tencent Cloud account and find the potential attack surface.

### Execution Steps

1. Use `tccli cvm DescribeInstances --region ap-beijing` to query all instances
2. Iterate over each instance and look at the following fields:
   - `PublicIpAddresses`: whether a public IP is bound
   - `SecurityGroupIds`: the list of associated security groups
3. For every instance with a public IP, query its associated security group rules (see scenario 1)
4. Focus on:
   - Whether an instance has a public IP but no security group bound
   - Whether management ports (22, 3389) are exposed to the internet
   - Whether database ports (3306, 5432, 6379, 27017) are exposed to the internet
5. Summarize the exposed port list and risk level for each public-network instance

---

## Scenario 3: Checking Key Pair and Login Method Security

### Task Description
Please help me check whether the login methods of all cloud servers under the Tencent Cloud account are secure.

### Execution Steps

1. Use `tccli cvm DescribeInstances --region ap-beijing` to query all instances
2. Iterate over each instance and check the `LoginSettings` field:
   - Whether a key pair is used (`KeyIds` is not empty) → secure
   - Whether password login is used (`KeepImageLogin` is false and there is no key pair) → higher risk
3. Use `tccli cvm DescribeKeyPairs --region ap-beijing` to query all key pairs
4. Check for orphan key pairs that are not associated with any instance
5. Summarize and output:
   - The number of instances that log in with a key pair
   - The number of instances that log in with a password (switching to a key pair is recommended)
   - The list of orphan key pairs (cleaning them up is recommended)

---

## Scenario 4: Checking Cloud Server Images and System Patches

### Task Description
Please help me check whether the operating system images used by all cloud servers under the Tencent Cloud account are too old.

### Execution Steps

1. Use `tccli cvm DescribeInstances --region ap-beijing` to query all instances
2. Iterate over each instance and look at the `ImageId` and `OsName` fields
3. Use `tccli cvm DescribeImages --region ap-beijing` to query the list of currently available public images
4. Compare the image each instance currently uses with the latest public image version
5. Flag instances running an outdated operating system (such as CentOS 7, which has reached end of maintenance, or Ubuntu 18.04)
6. Summarize the operating system information and upgrade advice for each instance

---

## Scenario 5: Checking Cloud Monitor Alarm Policy Coverage

### Task Description
Please help me check whether all cloud servers under the Tencent Cloud account have the necessary monitoring alarms configured.

### Execution Steps

1. Use `tccli cvm DescribeInstances --region ap-beijing` to query all instances and record the list of instance IDs
2. Use `tccli monitor DescribeAlarmPolicies --region ap-beijing --Module monitor --Namespace QCE/CVM` to query the alarm policies related to CVM
3. Check whether each instance is covered by at least one alarm policy
4. Check whether the alarm policies cover the following key metrics:
   - CPU utilization too high (such as > 90%)
   - Memory utilization too high (such as > 90%)
   - Disk utilization too high (such as > 85%)
   - Abnormal network inbound/outbound bandwidth
5. Check whether alarm notification channels are configured (SMS, email, WeChat, etc.)
6. Summarize and output:
   - The list of instances not covered by any alarm policy
   - The alarm policies that are missing key metrics
   - The alarm policies with no notification channel configured

---

## Scenario 6: Checking CAM Authorization and Access Control

### Task Description
Please help me check whether the CAM permission configuration related to cloud servers under the Tencent Cloud account is secure.

### Execution Steps

1. Use `tccli cam ListUsers` to query all sub-users
2. Use `tccli cam ListAttachedUserAllPolicies --TargetUin <uin> --Rp 200` to query the policies attached to each sub-user
3. Focus on:
   - Whether any sub-user has `AdministratorAccess` (super administrator) permission
   - Whether any sub-user has `QcloudCVMFullAccess` (full CVM access) without needing it for their work
   - Whether any sub-user has been unused for a long time (check `LastLoginTime`)
4. Use `tccli cam ListAccessKeys --TargetUin <uin>` to check the API key status
5. Check for old keys that have not been rotated (created more than 90 days ago)
6. Summarize and output:
   - The list of over-privileged users
   - The list of users who have not logged in for a long time
   - The list of API keys that need rotation

---

## Comprehensive Security Assessment Report (mandatory output for a comprehensive security check)

After all the scenarios above have been executed, you **must** compile a security assessment report containing every check item below:

| Check item | Status | Risk level | Description |
|--------|------|----------|------|
| Security group rules | ✅ / ⚠️ / ❌ | High/Medium/Low | Whether high-risk ports are open to the entire internet |
| Public exposure | ✅ / ⚠️ / ❌ | High/Medium/Low | Exposure of management ports and database ports |
| Login method | ✅ / ⚠️ / ❌ | High/Medium/Low | Key pair vs password login |
| System image | ✅ / ⚠️ / ❌ | High/Medium/Low | Whether an outdated operating system is in use |
| Monitoring alarms | ✅ / ⚠️ / ❌ | High/Medium/Low | Coverage of key metric alarms |
| CAM permissions | ✅ / ⚠️ / ❌ | High/Medium/Low | Least privilege and key rotation |

The report should also include:
- **Overall security score**: a composite score based on the risk level of each check item (excellent/good/fair/poor/dangerous)
- **High-priority remediation advice**: list the issues with a "high" risk level and the concrete remediation steps
- **Medium- and low-priority improvement advice**: list the issues with a "medium/low" risk level and the direction for improvement

---

## API Quick Reference

| Function | Service | API |
|------|------|------|
| Query security groups | vpc | `DescribeSecurityGroups` |
| Query security group rules | vpc | `DescribeSecurityGroupPolicies` |
| Query CVM instances | cvm | `DescribeInstances` |
| Query key pairs | cvm | `DescribeKeyPairs` |
| Query images | cvm | `DescribeImages` |
| Query alarm policies | monitor | `DescribeAlarmPolicies` |
| Query sub-users | cam | `ListUsers` |
| Query user policies | cam | `ListAttachedUserAllPolicies` |
| Query API keys | cam | `ListAccessKeys` |

---

## When to Use

| Scenario | Recommendation |
|------|------|
| The user asks for a comprehensive security check/security audit | Run the complete flow of scenarios 1 through 6 and output the comprehensive report |
| The user only asks about a specific security group rule | Run scenario 1 only |
| The user only asks about public exposure | Run scenario 2 only |
| The user wants to view resource status (not from a security angle) | Do not use this document; use basic query commands |
| The user wants to modify security group rules | This document only performs checks; for modification see `tccli vpc help` |
| The user wants a resource inspection (domain/certificate/instance status) | Do not use this document; use references/auto-check-resource.md |
