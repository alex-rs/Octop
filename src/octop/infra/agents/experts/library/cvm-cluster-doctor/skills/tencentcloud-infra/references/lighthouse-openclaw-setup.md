# Deploying OpenClaw on Tencent Cloud Lighthouse (clawdbot image)

Your knowledge of the parameters for the Tencent Cloud Lighthouse instance creation, image query, and password reset APIs may be outdated.
**Before executing, confirm the latest parameters with `tccli lighthouse <operation> help` first.**

> The complete flow for creating an OpenClaw instance on a Tencent Cloud Lightweight Application Server (Lighthouse) via the tccli command line.

---

## Prerequisites

### 1. Install tccli

```bash
python3 -m pip install tccli
```

### 2. Configure Tencent Cloud credentials

Go to the [Tencent Cloud API key console](https://console.cloud.tencent.com/cam/capi) to obtain the SecretId and SecretKey.

```bash
tccli configure set secretId <SecretId>
tccli configure set secretKey <SecretKey>
tccli configure set region <region>
tccli configure set output json
```

Verify the credentials:

```bash
tccli sts GetCallerIdentity
```

---

## Step 1: Query OpenClaw images

```bash
tccli lighthouse DescribeBlueprints --region <region>
```

Filter for the images whose names contain keywords such as `openclaw`, `claw`, or `clawdbot` with python/jq, then take the BlueprintId.

---

## Step 2: Query bundles

```bash
tccli lighthouse DescribeBundles --region <region>
```

Filter by the CPU/memory spec you need (for example 4c8g), then take the BundleId.

---

## Step 3: Create the instance

```bash
tccli lighthouse CreateInstances \
  --region <region> \
  --BundleId <bundle-id> \
  --BlueprintId <blueprint-id> \
  --InstanceName <name> \
  --InstanceCount 1 \
  --InstanceChargePrepaid '{"Period":<months>,"RenewFlag":"NOTIFY_AND_MANUAL_RENEW"}' \
  --LoginConfiguration '{"AutoGeneratePassword":"YES"}'
```

> ⚠️ `--InstanceChargePrepaid` is a required parameter; omitting it fails immediately.

---

## Step 4: Wait for the instance to be ready

Poll the instance status until it becomes `RUNNING` and obtains a public IP (usually about 30-60 seconds):

```bash
tccli lighthouse DescribeInstances \
  --region <region> \
  --InstanceIds '["<instance-id>"]'
```

State transition: `PENDING` → `RUNNING`

---

## Step 5: Set the root password

In `AutoGeneratePassword` mode the initial password cannot be retrieved directly, so set one yourself:

```bash
tccli lighthouse ResetInstancesPassword \
  --region <region> \
  --InstanceIds '["<instance-id>"]' \
  --Password '<password>' \
  --UserName 'root'
```

---

## SSH login

```bash
ssh root@<ip>
```

> 💡 After the first login, change the root password right away: `passwd root`

---

## Common operations commands

```bash
# Check instance status
tccli lighthouse DescribeInstances --region <region> --InstanceIds '["<instance-id>"]'

# Reboot
tccli lighthouse RebootInstances --region <region> --InstanceIds '["<instance-id>"]'

# Shut down
tccli lighthouse StopInstances --region <region> --InstanceIds '["<instance-id>"]'

# Start up
tccli lighthouse StartInstances --region <region> --InstanceIds '["<instance-id>"]'

# List firewall rules
tccli lighthouse DescribeFirewallRules --region <region> --InstanceId "<instance-id>"

# Renew
tccli lighthouse RenewInstances --region <region> --InstanceIds '["<instance-id>"]' \
  --InstanceChargePrepaid '{"Period":<months>,"RenewFlag":"NOTIFY_AND_MANUAL_RENEW"}'
```

---

## Notes

1. **Credential safety**: the SecretKey must never appear in logs or code comments; prefer encrypted storage in the `tencent-cloud-tools` keystore
2. **High-risk operations**: for Stop/Terminate and similar actions, rehearse with `--dry-run` first
3. **Password change**: change the root password immediately after the first SSH login
4. **Renewal reminder**: watch the instance expiry date and renew ahead of time or enable auto-renewal

---

## When to use

| Scenario | Recommendation |
|------|------|
| The user wants to deploy OpenClaw / clawdbot | Follow the complete flow in this document |
| The user wants to deploy other applications on Lighthouse | Do not use this document; use references/lighthouse-app-deploy.md |
| The user wants to build a website (WordPress/BT Panel) | Do not use this document; use references/lighthouse-website-setup.md |
| The user wants to manage an existing Lighthouse instance | See the "Common operations commands" section of this document |
| The user wants to attach a cloud disk to an instance | Do not use this document; use references/cbs-bindto-cvm.md |
