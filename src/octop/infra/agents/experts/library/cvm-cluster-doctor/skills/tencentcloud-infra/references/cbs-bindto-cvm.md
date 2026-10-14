# Buying a Cloud Disk (CBS) and Attaching It to a Cloud Server

Your knowledge of the parameters of the Tencent Cloud CBS, CVM attachment, and TAT remote execution APIs may be outdated.
**Before executing, confirm the latest parameters with `tccli <service> <action> help`.**

> Use case: buy a new cloud disk (CBS) for an existing CVM cloud server or Lighthouse instance, then complete attachment, partitioning, formatting, and automatic-mount configuration.
> Everything is done through the tccli command line; no console login is needed.

---

## Prerequisites

### Required Permissions

| Permission | Description |
|------|------|
| `QcloudCBSFullAccess` | Create/manage cloud disks |
| `QcloudCVMFullAccess` | Manage cloud servers (CVM scenario) |
| `QcloudLighthouseFullAccess` | Manage Lighthouse instances (Lighthouse scenario) |
| `QcloudTATFullAccess` | TAT automation assistant (remote execution of disk initialization commands) |

> Sub-accounts must be granted the policies above in the CAM console.

### Key Constraints

- **Same availability zone**: the cloud disk must be in **the same availability zone** as the target cloud server (e.g. both in `ap-beijing-3`), otherwise it cannot be attached
- **Attachment limit**: each CVM can have at most 20 cloud disks attached; Lighthouse at most 5 cloud disks
- **Billing mode**: confirm that the cloud disk's billing mode matches the instance (prepaid subscription / pay-as-you-go)

---

## Scenario 1: Buying and Attaching a Cloud Disk for a CVM Cloud Server

### Task Description

Buy a new cloud disk (CBS) for an existing CVM cloud server and attach it to that server.

### Execution Steps

#### Step 1: Query the target CVM instance information

First confirm the target instance's availability zone, how many cloud disks are currently attached, and similar information:

```bash
tccli cvm DescribeInstances --region <region> --InstanceIds '["<instance-id>"]'
```

Look at the following fields:
- `Placement.Zone`: the availability zone of the instance (the same zone must be specified when creating the cloud disk later)
- `InstanceId`: instance ID
- `InstanceName`: instance name
- `InstanceState`: instance state (should be `RUNNING` or `STOPPED`)
- `DataDisks`: the list of currently attached data disks

> ⚠️ If the user only provided the instance name rather than the ID, query by name with Filters:
> ```bash
> tccli cvm DescribeInstances --region <region> --Filters '[{"Name":"instance-name","Values":["<name>"]}]'
> ```

#### Step 2: Query available cloud disk types and prices

```bash
# query the cloud disk types supported in the specified availability zone
tccli cbs DescribeDiskConfigQuota --region <region> --InquiryType INQUIRY_CBS_CONFIG --DiskZones '["<zone>"]'
```

Common cloud disk types:
| Type | DiskType | Description |
|------|----------|------|
| High-performance cloud disk | `CLOUD_PREMIUM` | Suitable for most I/O scenarios |
| SSD cloud disk | `CLOUD_SSD` | Suitable for small and medium databases |
| Enhanced SSD cloud disk | `CLOUD_HSSD` | Suitable for high-performance databases and core business |
| Extreme SSD cloud disk | `CLOUD_TSSD` | Suitable for large databases and high-IOPS scenarios |

Optional: query cloud disk prices:

```bash
tccli cbs InquirePriceCreateDisks --region <region> \
  --DiskType "<disk-type>" \
  --DiskSize <size-in-gb> \
  --DiskCount 1 \
  --DiskChargeType "PREPAID" \
  --DiskChargePrepaid '{"Period":<months>,"RenewFlag":"NOTIFY_AND_MANUAL_RENEW"}'
```

#### Step 3: Create the cloud disk

**Prepaid cloud disk** (for prepaid instances):

```bash
tccli cbs CreateDisks --region <region> \
  --DiskType "<disk-type>" \
  --DiskSize <size-in-gb> \
  --DiskCount 1 \
  --DiskName "<disk-name>" \
  --DiskChargeType "PREPAID" \
  --DiskChargePrepaid '{"Period":<months>,"RenewFlag":"NOTIFY_AND_MANUAL_RENEW"}' \
  --Placement '{"Zone":"<zone>"}'
```

**Pay-as-you-go cloud disk** (for pay-as-you-go instances):

```bash
tccli cbs CreateDisks --region <region> \
  --DiskType "<disk-type>" \
  --DiskSize <size-in-gb> \
  --DiskCount 1 \
  --DiskName "<disk-name>" \
  --DiskChargeType "POSTPAID_BY_HOUR" \
  --Placement '{"Zone":"<zone>"}'
```

> ⚠️ Creating a cloud disk is a **medium-risk operation**; confirm the following with the user before executing:
> - The cloud disk type and size
> - The billing mode and cost
> - The target availability zone

Record the returned `DiskId`.

#### Step 4: Wait for the cloud disk to become ready

```bash
tccli cbs DescribeDisks --region <region> --DiskIds '["<disk-id>"]'
```

State transition: `CREATING` → `UNATTACHED` (about 10-30 seconds)

Only once `DiskState` becomes `UNATTACHED` can the disk be attached.

#### Step 5: Attach the cloud disk to the CVM

```bash
tccli cbs AttachDisks --region <region> \
  --DiskIds '["<disk-id>"]' \
  --InstanceId "<instance-id>"
```

> ⚠️ The instance must be in the `RUNNING` or `STOPPED` state to attach.

#### Step 6: Confirm the attachment succeeded

```bash
tccli cbs DescribeDisks --region <region> --DiskIds '["<disk-id>"]'
```

Confirm the following fields:
- `DiskState`: should become `ATTACHED`
- `InstanceId`: should be the target instance ID
- `Attached`: should be `true`

#### Step 7: Initialize the disk inside the instance (executed remotely through TAT)

After a successful attachment, the cloud disk appears in the operating system as an unformatted raw disk that needs to be partitioned, formatted, and mounted on the file system.

**7a. Find the new disk device name**

```bash
# execute the command through TAT
tccli tat RunCommand --region <region> \
  --InstanceIds '["<instance-id>"]' \
  --Content "$(echo 'lsblk' | base64)" \
  --CommandType "SHELL" \
  --Username "root" \
  --Timeout 30
```

Wait a few seconds, then query the execution result:

```bash
tccli tat DescribeInvocationTasks --region <region> \
  --Filters '[{"Name":"invocation-id","Values":["<invocation-id>"]}]'
```

> The `Output` field in the result is Base64-encoded and must be decoded to view. The new disk usually appears as `vdb` (or `vdc`, `vdd`, etc., depending on how many disks already exist), with no partitions and no mount point.

**7b. Partition, format, and mount**

```bash
# run the one-shot initialization script through TAT
tccli tat RunCommand --region <region> \
  --InstanceIds '["<instance-id>"]' \
  --Content "$(echo 'DISK=/dev/vdb
MOUNT_POINT=/data

# create the partition
parted -s ${DISK} mklabel gpt
parted -s ${DISK} mkpart primary ext4 0% 100%
partprobe ${DISK}
sleep 2

# format
mkfs.ext4 ${DISK}1

# create the mount point and mount
mkdir -p ${MOUNT_POINT}
mount ${DISK}1 ${MOUNT_POINT}

# configure automatic mounting at boot (using a UUID, which is more reliable)
UUID=$(blkid -s UUID -o value ${DISK}1)
echo "UUID=${UUID} ${MOUNT_POINT} ext4 defaults 0 2" >> /etc/fstab

# verify
df -h ${MOUNT_POINT}
cat /etc/fstab | grep ${MOUNT_POINT}' | base64)" \
  --CommandType "SHELL" \
  --Username "root" \
  --Timeout 60
```

> ⚠️ **Important notes**:
> - The `DISK` variable must be replaced with the actual device name confirmed in step 7a (e.g. `/dev/vdb`)
> - `MOUNT_POINT` can be customized to the user's needs (common choices: `/data`, `/mnt/data`)
> - For CentOS 8+ / Ubuntu 20+, using the `xfs` file system instead of `ext4` is recommended
> - This operation **erases all data on the disk** and is only for a brand-new cloud disk

#### Step 8: Verify the final state

```bash
# view disk usage through TAT
tccli tat RunCommand --region <region> \
  --InstanceIds '["<instance-id>"]' \
  --Content "$(echo 'df -Th && echo "---" && lsblk && echo "---" && cat /etc/fstab' | base64)" \
  --CommandType "SHELL" \
  --Username "root" \
  --Timeout 30
```

Confirm:
- The new partition is mounted at the specified directory
- The file system type is correct
- An automatic mount entry has been added to `/etc/fstab`

---

## Scenario 2: Buying and Attaching a Cloud Disk for a Lighthouse Instance

### Task Description

Buy a new cloud disk for an existing Lighthouse instance and complete the attachment.

### Execution Steps

#### Step 1: Query the target Lighthouse instance information

```bash
tccli lighthouse DescribeInstances --region <region> --InstanceIds '["<instance-id>"]'
```

Look at the following fields:
- `Zone`: the availability zone of the instance
- `InstanceId`: instance ID
- `InstanceName`: instance name
- `InstanceState`: instance state (should be `RUNNING`)

#### Step 2: Query the currently attached cloud disks

```bash
tccli lighthouse DescribeDisks --region <region> \
  --Filters '[{"Name":"instance-id","Values":["<instance-id>"]}]'
```

> A single Lighthouse instance can have at most **5** data disks attached; confirm that the limit is not exceeded.

#### Step 3: Query the available cloud disk configurations

```bash
# query the Lighthouse cloud disk plans
tccli lighthouse DescribeDiskConfigs --region <region>
```

> Note: Lighthouse's cloud disk creation API differs from CVM's; use the Lighthouse-specific API.

#### Step 4: Create the Lighthouse cloud disk

```bash
tccli lighthouse CreateDisks --region <region> \
  --Zone "<zone>" \
  --DiskSize <size-in-gb> \
  --DiskType "<disk-type>" \
  --DiskChargePrepaid '{"Period":<months>,"RenewFlag":"NOTIFY_AND_MANUAL_RENEW"}' \
  --DiskCount 1 \
  --DiskName "<disk-name>"
```

> ⚠️ Lighthouse cloud disks only support the **prepaid subscription** billing mode.

Record the returned `DiskId`.

#### Step 5: Wait for the cloud disk to become ready

```bash
tccli lighthouse DescribeDisks --region <region> \
  --DiskIds '["<disk-id>"]'
```

State transition: `CREATING` → `UNATTACHED`

#### Step 6: Attach the cloud disk to the Lighthouse instance

```bash
tccli lighthouse AttachDisks --region <region> \
  --DiskIds '["<disk-id>"]' \
  --InstanceId "<instance-id>"
```

#### Step 7: Confirm the attachment succeeded

```bash
tccli lighthouse DescribeDisks --region <region> --DiskIds '["<disk-id>"]'
```

Confirm that `DiskState` becomes `ATTACHED` and `InstanceId` is the target instance.

#### Step 8: Initialize the disk inside the instance (executed remotely through TAT)

Lighthouse also supports the TAT automation assistant, and the initialization steps match the CVM scenario:

```bash
# find the new disk device name
tccli tat RunCommand --region <region> \
  --InstanceIds '["<instance-id>"]' \
  --Content "$(echo 'lsblk' | base64)" \
  --CommandType "SHELL" \
  --Username "root" \
  --Timeout 30
```

Then follow scenario 1, step 7b, to partition, format, and mount the disk.

---

## Scenario 3: Creating a Scheduled Snapshot Policy for a Cloud Disk

### Task Description

Configure a scheduled snapshot policy for the newly attached cloud disk to protect your data.

### Execution Steps

#### Step 1: Create the scheduled snapshot policy

```bash
tccli cbs CreateAutoSnapshotPolicy --region <region> \
  --Policy '[{"DayOfWeek":[0,3],"Hour":[2]}]' \
  --AutoSnapshotPolicyName "<policy-name>" \
  --IsActivated true \
  --RetentionDays 7
```

> The example above creates a snapshot automatically every Sunday and Wednesday at 2 a.m. and keeps them for 7 days.

Record the returned `AutoSnapshotPolicyId`.

#### Step 2: Bind the cloud disk to the snapshot policy

```bash
tccli cbs BindAutoSnapshotPolicy --region <region> \
  --AutoSnapshotPolicyId "<policy-id>" \
  --DiskIds '["<disk-id>"]'
```

#### Step 3: Verify the binding result

```bash
tccli cbs DescribeAutoSnapshotPolicies --region <region> \
  --AutoSnapshotPolicyIds '["<policy-id>"]'
```

Confirm that `DiskIdSet` contains the target cloud disk ID.

---

## FAQ

| Problem | Cause and solution |
|------|-----------|
| "Availability zone not supported" error when creating a cloud disk | Confirm that the `DiskType` you use is available in the target zone; query it with `DescribeDiskConfigQuota` |
| "Availability zone mismatch" error when attaching | The cloud disk and the instance must be in the same availability zone; attaching across zones is not possible |
| The new disk is not visible in the system after attaching | On Linux, run `lsblk` or `fdisk -l` to check; on Windows, initialize it in "Disk Management" |
| `df -h` does not show the partition | You must `mount` it to a directory first before it appears in `df` |
| The disk is not mounted automatically after a reboot | Check whether `/etc/fstab` is configured correctly; prefer a UUID over a device name |
| Lighthouse returns an error when creating a cloud disk | Lighthouse uses the dedicated API `lighthouse CreateDisks`; you cannot use CBS `CreateDisks` |
| The attachment limit is exceeded | CVM allows at most 20 and Lighthouse at most 5; detach unused disks first |

---

## API Quick Reference

### CBS (cloud disks - for CVM)

| Function | Service | API |
|------|------|------|
| Query cloud disks | cbs | `DescribeDisks` |
| Query cloud disk configurations | cbs | `DescribeDiskConfigQuota` |
| Query prices | cbs | `InquirePriceCreateDisks` |
| Create a cloud disk | cbs | `CreateDisks` |
| Attach a cloud disk | cbs | `AttachDisks` |
| Detach a cloud disk | cbs | `DetachDisks` |
| Create a snapshot | cbs | `CreateSnapshot` |
| Create a scheduled snapshot policy | cbs | `CreateAutoSnapshotPolicy` |
| Bind a snapshot policy | cbs | `BindAutoSnapshotPolicy` |
| Query snapshot policies | cbs | `DescribeAutoSnapshotPolicies` |
| Expand a cloud disk | cbs | `ResizeDisk` |
| Return a cloud disk | cbs | `TerminateDisks` |

### Lighthouse (Lighthouse cloud disks)

| Function | Service | API |
|------|------|------|
| Query cloud disks | lighthouse | `DescribeDisks` |
| Query cloud disk configurations | lighthouse | `DescribeDiskConfigs` |
| Create a cloud disk | lighthouse | `CreateDisks` |
| Attach a cloud disk | lighthouse | `AttachDisks` |
| Detach a cloud disk | lighthouse | `DetachDisks` |
| Renew a cloud disk | lighthouse | `RenewDisks` |
| Return a cloud disk | lighthouse | `TerminateDisks` |

### Common

| Function | Service | API |
|------|------|------|
| Query CVM instances | cvm | `DescribeInstances` |
| Query Lighthouse instances | lighthouse | `DescribeInstances` |
| Execute commands remotely | tat | `RunCommand` |
| Query execution results | tat | `DescribeInvocationTasks` |

---

## When to Use

| Scenario | Recommendation |
|------|------|
| The user wants to buy/create/attach a cloud disk | Follow scenario 1 or scenario 2 in this document |
| The user wants to configure scheduled snapshots | See scenario 3 in this document |
| The user only wants to view cloud disk status | Do not use this document; use `tccli cbs DescribeDisks` |
| The user wants a security check | Do not use this document; use references/cvm-security-check.md |
| The user wants to deploy an application or set up a website | Do not use this document; use the corresponding deployment/website-setup reference |
