# Automated Inspection and Monitoring of Tencent Cloud Resources

Your knowledge of the parameters of the Tencent Cloud domain, SSL certificate, and instance status APIs may be outdated.
**Before executing, confirm the latest parameters with `tccli <service> <action> help`.**

> Use the "Tencent Cloud Resource Management Tool" Skill to inspect and monitor cloud resources.

---

## Scenario 1: Monitoring Domain Expiry

### Task Description
Please help me check the expiry status of all domains under the Tencent Cloud account.

### Execution Steps

1. Use `tccli domain DescribeDomainNameList` to query the list of all domains under the account
2. Iterate over each domain and check its expiry time (the `ExpirationDate` field)
3. Compute the number of days remaining until expiry
4. If fewer than **30 days** remain, flag it as an alert and output the domain and the expiry date
5. Summarize and output the status of all domains (normal / expiring soon)

---

## Scenario 2: Monitoring SSL Certificate Expiry

### Task Description
Please help me check the expiry status of all SSL certificates under the Tencent Cloud account.

### Execution Steps

1. Use `tccli ssl DescribeCertificates` to query the list of all certificates
2. Iterate over each certificate and look at the `CertificateId`, `Domain`, and `CertEndTime` fields
3. Compute the number of days remaining until expiry
4. If fewer than **30 days** remain, flag it as an alert
5. Summarize and output the status of all certificates

---

## Scenario 3: Monitoring Cloud Server Instance Status

### Task Description
Please help me check the running status of all cloud server instances under the Tencent Cloud account.

### Execution Steps

1. Use `tccli cvm DescribeInstances --region ap-beijing` to query all instances
2. Iterate over each instance and look at the `InstanceId`, `InstanceName`, and `InstanceState` fields
3. If the instance state is not `RUNNING`, flag it as abnormal and raise an alert
4. Optional: for running instances, use `tccli monitor GetMonitorData` to query monitoring metrics such as CPU utilization, and raise an alert when resource utilization is abnormal
5. Summarize and output the status of all instances

---

## Scenario 4: Monitoring Cloud Disk Status

### Task Description
Please help me check the status of all cloud disks under the Tencent Cloud account.

### Execution Steps

1. Use `tccli cbs DescribeDisks --region ap-beijing` to query all cloud disks
2. Iterate over each cloud disk and look at the `DiskId`, `DiskName`, `DiskState`, and `DiskUsage` fields
3. If the state is neither `ATTACHED` nor `UNATTACHED`, flag it as abnormal and raise an alert
4. Summarize and output the status of all cloud disks

---

## API Quick Reference

| Function | Service | API |
|------|------|------|
| Query the domain list | domain | `DescribeDomainNameList` |
| Query SSL certificates | ssl | `DescribeCertificates` |
| Query CVM instances | cvm | `DescribeInstances` |
| Query cloud disks | cbs | `DescribeDisks` |
| Query monitoring data | monitor | `GetMonitorData` |

---

## When to Use

| Scenario | Recommendation |
|------|------|
| The user asks for resource inspection/batch checks | Run the complete flow of scenarios 1 through 4 |
| The user only asks about domain expiry | Run scenario 1 only |
| The user only asks about certificate expiry | Run scenario 2 only |
| The user wants a security check/security audit | Do not use this document; use references/cvm-security-check.md |
| The user wants to view the status of a single instance | Do not use this document; use basic query commands |
| The user wants to deploy an application or set up a website | Do not use this document; use the corresponding deployment/website-setup reference |
