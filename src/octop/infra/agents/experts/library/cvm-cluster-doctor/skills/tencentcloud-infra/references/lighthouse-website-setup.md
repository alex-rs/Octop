# Website Building Guide with Lighthouse

Your knowledge of the parameters for the Tencent Cloud Lighthouse, domain registration, and DNS resolution APIs may be outdated.
**Before executing, confirm the latest parameters with `tccli <service> <operation> help` first.**

> Applies to: Tencent Cloud Lighthouse + an application image (WordPress, WooCommerce, BT Panel, LAMP/LNMP, etc.) + domain registration + DNS binding
> The whole process is completed through the `tccli` command line, with no need to log in to the console

---

## 1. Preparation

### 1.1 Credential configuration

```bash
TC="<tencent-cloud-tools>/scripts"

# First-time configuration (choose SecretId/Key or QR scan or STS)
bash $TC/tc.sh --setup

# Verify credentials
bash $TC/tc.sh --check-cred
```

### 1.2 Required permissions

| Permission | Description |
|------|------|
| `QcloudLighthouseFullAccess` | Create/manage lightweight servers |
| `QcloudDomainFullAccess` | Buy/manage domains |
| `QcloudDNSPodFullAccess` | Add/modify DNS records |
| `QcloudTATFullAccess` | TAT automation assistant (retrieve panel password) |

> Sub-accounts must be granted the policies above in the CAM console.

### 1.3 Domain information template

Buying a domain requires a verified information template (real-name verification):

```bash
# List existing templates
bash $TC/tc.sh domain DescribeTemplateList

# If you have no template, create one in the console:
# https://console.cloud.tencent.com/domain/template
```

---

## 2. One-click website setup (automation script)

```bash
TC="<tencent-cloud-tools>/scripts"

# Interactive mode (recommended, guided throughout)
python3 $TC/create_site.py

# Non-interactive mode (specify every parameter)
python3 $TC/create_site.py \
  --region <region> \
  --bundle <bundle-id> \
  --blueprint <blueprint-id> \
  --name <instance-name> \
  --domain <domain> \
  --template <template-id>
```

The script automatically:
1. Creates the Lighthouse instance
2. Waits for the instance to be RUNNING and obtains the public IP
3. Buys the domain
4. Waits for domain registration to complete
5. Adds DNS A records (@ and www)
6. Retrieves the BT Panel initial password through TAT
7. Prints the complete deployment report

Helper commands:

```bash
# List bundles only
python3 $TC/create_site.py --list-bundles --region <region>

# Check domain availability only
python3 $TC/create_site.py --query-domain <keyword>

# Add DNS records only (existing instance + existing domain)
python3 $TC/create_site.py --dns-only --domain <domain> --ip <ip>
```

---

## 3. Step-by-step manual operation

### 3.1 Query bundles and images

```bash
# Bundle list
tccli lighthouse DescribeBundles --region <region>

# Query application images (WordPress, WooCommerce, BT Panel, LAMP, etc.)
tccli lighthouse DescribeBlueprints --region <region>
```

Filter for the application image you need by keyword with jq/python (for example `wordpress`, `woo`, `bt`, `lamp`, `node`).

### 3.2 Create the Lighthouse instance

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

> ⚠️ `--InstanceChargePrepaid` is a required parameter; omitting it raises an error.

### 3.3 Wait for the instance to start

```bash
tccli lighthouse DescribeInstances \
  --region <region> \
  --InstanceIds '["<instance-id>"]'
```

State transition: `PENDING` → `RUNNING` (about 30-60 seconds)

### 3.4 Check domain availability

```bash
# Single lookup
tccli domain CheckDomain --DomainName "<domain>"

# Batch lookup across multiple suffixes
for suffix in .com .site .store .net .shop; do
  tccli domain CheckDomain --DomainName "<keyword>${suffix}"
done
```

### 3.5 Buy a domain

```bash
# List approved information templates
tccli domain DescribeTemplateList

# Buy the domain
tccli domain CreateDomainBatch \
  --TemplateId <template-id> \
  --Period 1 \
  --Domains '["<domain>"]' \
  --PayMode 1 \
  --AutoRenewFlag 0

# Check registration status
tccli domain CheckBatchStatus --LogIds '[<log-id>]'
```

> **Note**: the `BuyDomain` interface does not exist; the correct interface is `CreateDomainBatch` (it supports a single domain).

### 3.6 Add DNS records

```bash
# Root domain A record
tccli dnspod CreateRecord \
  --Domain "<domain>" \
  --SubDomain "@" \
  --RecordType "A" \
  --RecordLine "default" \
  --Value "<ip>" \
  --TTL 600

# www A record
tccli dnspod CreateRecord \
  --Domain "<domain>" \
  --SubDomain "www" \
  --RecordType "A" \
  --RecordLine "default" \
  --Value "<ip>" \
  --TTL 600

# Verify the DNS records
tccli dnspod DescribeRecordList --Domain "<domain>"
```

> ⏳ Global DNS propagation usually takes 5-30 minutes.

### 3.7 Retrieve the BT Panel initial password (TAT, for BT Panel images)

Use the TAT automation assistant to run the `bt default` command inside the instance:

```python
import sys, base64, time
sys.path.insert(0, '<tencent-cloud-tools>/scripts')
from keystore import get_credentials
from tencentcloud.common import credential
from tencentcloud.tat.v20201028 import tat_client, models

cred_data = get_credentials('default')
cred = credential.Credential(cred_data['secret_id'], cred_data['secret_key'])
client = tat_client.TatClient(cred, "<region>")

# RunCommand (Content must be Base64-encoded)
req = models.RunCommandRequest()
req.InstanceIds = ['<instance-id>']
req.Content = base64.b64encode(b"bt default").decode()
req.CommandType = 'SHELL'
req.Username = 'root'
req.Timeout = 30
resp = client.RunCommand(req)

# Query the result (use Filters; InvocationId cannot be passed directly)
time.sleep(8)
req2 = models.DescribeInvocationTasksRequest()
f = models.Filter()
f.Name = "invocation-id"
f.Values = [resp.InvocationId]
req2.Filters = [f]
result = client.DescribeInvocationTasks(req2)
for task in result.InvocationTaskSet:
    print(base64.b64decode(task.TaskResult.Output).decode())
```

---

## 4. Post-setup configuration

### 4.1 BT Panel initialization (for BT Panel images)

1. Open `http://<ip>:8888/tencentcloud`
2. Log in with the initial username and password
3. **Immediately change** the administrator password (Panel → Security)
4. Bind the domain: Panel → Website → Edit site → Domain management

### 4.2 Apply for an SSL certificate (HTTPS)

**Through the BT Panel:**
1. BT Panel → SSL → Let's Encrypt → Free application
2. Select the domains (@ and www)
3. Check "Force HTTPS"

**Command-line approach (for images without BT Panel):**
```bash
# Use certbot to apply for a Let's Encrypt certificate
certbot --nginx -d <domain> -d www.<domain>
# or
certbot --apache -d <domain> -d www.<domain>
```

### 4.3 Application-specific configuration

Complete the matching initialization for the image type you chose:

- **WordPress/WooCommerce**: Admin → Settings → General, change the site address to `https://<domain>`; the first visit to WooCommerce opens the setup wizard (store details, payment methods, shipping)
- **LAMP/LNMP**: configure the virtual host, upload the site files, and set up the database
- **Node.js / Python, etc.**: deploy the application code and configure a reverse proxy (Nginx/Apache)
- **Pure OS images**: install the web server, database, and runtime environment as needed

---

## 5. Common issues

| Issue | Cause and fix |
|------|-----------|
| The domain is unreachable | DNS propagation takes 5-30 minutes; first confirm the service works by accessing it through the IP, then check resolution with `nslookup <domain>` |
| BT Panel returns 404 | Port 8888 + path `/tencentcloud` (the Tencent Cloud exclusive build); confirm the firewall allows 8888 |
| Instance creation errors out | `--InstanceChargePrepaid` is required: `{"Period":1,"RenewFlag":"NOTIFY_AND_MANUAL_RENEW"}` |
| Buying a domain errors out | Confirm the template `AuditStatus=="Approved"`, sufficient balance, and that you use `CreateDomainBatch` rather than `BuyDomain` |
| TAT query errors out | `--InvocationId` cannot be passed directly; use Filters: `f.Name="invocation-id"` |
| Switching the domain's DNS provider | `tccli domain ModifyDomainDNSBatch --Domains '["<domain>"]' --Dns '["ns1.dnspod.net","ns2.dnspod.net"]'` |

---

## 6. API quick reference

| Function | Service | Interface |
|------|------|------|
| Query bundles | lighthouse | `DescribeBundles` |
| Query images | lighthouse | `DescribeBlueprints` |
| Create instance | lighthouse | `CreateInstances` |
| Query instances | lighthouse | `DescribeInstances` |
| Reset password | lighthouse | `ResetInstancesPassword` |
| Check domain | domain | `CheckDomain` |
| Buy domain | domain | `CreateDomainBatch` |
| Check registration status | domain | `CheckBatchStatus` |
| List templates | domain | `DescribeTemplateList` |
| Change DNS provider | domain | `ModifyDomainDNSBatch` |
| Add DNS record | dnspod | `CreateRecord` |
| Query DNS records | dnspod | `DescribeRecordList` |
| Modify DNS record | dnspod | `ModifyRecord` |
| Delete DNS record | dnspod | `DeleteRecord` |
| Run a command on the instance | tat | `RunCommand` |
| Query execution result | tat | `DescribeInvocationTasks` |

---

## When to use

| Scenario | Recommendation |
|------|------|
| The user wants to build a website / set up a site / WordPress / BT Panel | Follow the flow in this document |
| The user wants to buy a domain / bind a domain / set up DNS records | See sections 3.4-3.6 of this document |
| The user only wants to deploy application code (not build a site) | Do not use this document; use references/lighthouse-app-deploy.md |
| The user wants to deploy OpenClaw | Do not use this document; use references/lighthouse-openclaw-setup.md |
| The user wants to attach a cloud disk | Do not use this document; use references/cbs-bindto-cvm.md |
| The user wants a security check | Do not use this document; use references/cvm-security-check.md |
