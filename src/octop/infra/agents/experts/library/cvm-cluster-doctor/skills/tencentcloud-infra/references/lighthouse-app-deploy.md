# Tencent Cloud Lighthouse Application Deployment Guide

Your knowledge of the parameters for the Tencent Cloud Lighthouse instance creation, firewall configuration, and image query APIs may be outdated.
**Before executing, confirm the latest parameters with `tccli lighthouse <operation> help` first.**

> Applies to: deploying any web application on Tencent Cloud Lighthouse (Go / Node.js / Python / Java / static site / Docker / GitHub project, etc.)
> The whole process is completed through `tccli` + SSH, with no need to log in to the console

---

## 1. Overall flow

```
Phase 1: Create the instance
  1. Query images → choose the OS
  2. Query bundles → choose CPU/memory/bandwidth
  3. Create the instance → get the instance ID
  4. Wait for RUNNING → get the public IP
  5. Reset the password → get SSH login credentials
  6. Open firewall ports

Phase 2: Deploy the application
  7. Prepare the code (local project / GitHub clone / Docker image)
  8. Upload or pull the code to the instance
  9. Install the runtime + build + start
  10. Configure the systemd / pm2 / docker-compose daemon

Phase 3: Verify and optimize
  11. Verify the service is reachable
  12. (Optional) Bind a domain + HTTPS + Nginx reverse proxy
```

---

## 2. Phase 1: Create the instance

### 2.1 Credential configuration

```bash
export TENCENTCLOUD_SECRET_ID="<your-secret-id>"
export TENCENTCLOUD_SECRET_KEY="<your-secret-key>"
```

> Required permission: `QcloudLighthouseFullAccess`

### 2.2 Query images

```bash
# Pure OS images (Ubuntu 24.04 recommended)
tccli lighthouse DescribeBlueprints --region <region> \
  --cli-unfold-argument \
  --Filters.0.Name blueprint-type \
  --Filters.0.Values PURE_OS

# Application images (WordPress / BT Panel / Docker CE, etc.)
tccli lighthouse DescribeBlueprints --region <region> \
  --cli-unfold-argument \
  --Filters.0.Name blueprint-type \
  --Filters.0.Values APP_OS
```

Filtering example (using Ubuntu 24.04 as the example):
```bash
... | python3 -c "
import json, sys
data = json.load(sys.stdin)
for b in data.get('BlueprintSet', []):
    if 'Ubuntu' in b.get('OsName', '') and '24.04' in b.get('OsName', ''):
        print(f\"BlueprintId: {b['BlueprintId']}  OsName: {b['OsName']}\")
"
```

**Image selection advice:**

| Deployment type | Recommended image |
|---------|---------|
| Go / Rust / C++ | Ubuntu 24.04 (pure OS, compile it yourself) |
| Node.js / Python / Ruby | Ubuntu 24.04 (pure OS, install the runtime) |
| Docker projects | Docker CE application image (Docker preinstalled) |
| WordPress / CMS | WordPress application image |
| Panel-based management needed | BT Panel application image |

### 2.3 Query bundles

```bash
tccli lighthouse DescribeBundles --region <region> \
  --cli-unfold-argument \
  --Filters.0.Name bundle-type \
  --Filters.0.Values GENERAL_BUNDLE
```

**Bundle selection advice:**

| Application type | Recommended spec |
|---------|---------|
| Static site / lightweight API | 2 vCPU 2G |
| Go / Node.js web application | 2 vCPU 4G |
| Java / database / multiple Docker containers | 4 vCPU 8G |

### 2.4 Create the instance

```bash
tccli lighthouse CreateInstances --region <region> \
  --cli-unfold-argument \
  --BundleId <bundle-id> \
  --BlueprintId <blueprint-id> \
  --InstanceName "<name>" \
  --InstanceChargePrepaid.Period 1 \
  --LoginConfiguration.AutoGeneratePassword YES \
  --InstanceCount 1 \
  --Zones <zone>
```

> ⚠️ Common pitfalls:
> - `--InstanceChargePrepaid.Period` is required and is measured in months
> - `AutoGeneratePassword` must be the uppercase `YES` or `NO`, not `True`/`true`/`Yes`

### 2.5 Wait for the instance to start

```bash
# Poll every 15-30 seconds until RUNNING
tccli lighthouse DescribeInstances --region <region> \
  --cli-unfold-argument \
  --InstanceIds <instance-id> 2>&1 | python3 -c "
import json, sys
data = json.load(sys.stdin)
inst = data['InstanceSet'][0]
print(f\"State: {inst['InstanceState']}\")
pub = inst.get('PublicAddresses', [])
print(f\"Public IP: {pub[0] if pub else 'unassigned'}\")
"
```

State transition: `PENDING` → `RUNNING` (about 30-60 seconds)

### 2.6 Reset the password

```bash
tccli lighthouse ResetInstancesPassword --region <region> \
  --cli-unfold-argument \
  --InstanceIds <instance-id> \
  --Password '<password>' \
  --UserName root
```

> Password requirements: 8-30 characters, containing at least three of uppercase letters, lowercase letters, digits, and special characters.
> After the reset, wait about 15-20 seconds for it to take effect.

### 2.7 Open firewall ports

```bash
# Open HTTP 80
tccli lighthouse CreateFirewallRules --region <region> \
  --cli-unfold-argument \
  --InstanceId <instance-id> \
  --FirewallRules.0.Protocol TCP \
  --FirewallRules.0.Port 80 \
  --FirewallRules.0.CidrBlock "0.0.0.0/0" \
  --FirewallRules.0.Action ACCEPT \
  --FirewallRules.0.FirewallRuleDescription "HTTP"
```

> A return of `InvalidParameter.FirewallRulesExist` means the rule already exists and can be ignored.

Commonly opened ports:

| Port | Purpose |
|------|------|
| 80 | HTTP |
| 443 | HTTPS |
| 8080 | Common application port |
| 3000 | Node.js / Grafana |
| 5000 | Flask / Registry |
| 8888 | BT Panel |

---

## 3. Phase 2: Deploy the application

The following sections cover each source and technology stack separately. Every approach assumes Phase 1 is complete (the instance is RUNNING, the password has been reset, and the ports are open).

Define SSH shortcuts for later use:
```bash
SSH="sshpass -p '<password>' ssh -o StrictHostKeyChecking=no root@<public-IP>"
SCP="sshpass -p '<password>' scp -o StrictHostKeyChecking=no"
```

---

### Option A: Deploy a local project (upload the code)

Applies to: the code already exists locally and is packaged and uploaded to the instance.

```bash
# 1. Package locally
cd /path/to/project
tar czf /tmp/project.tar.gz --exclude='.git' --exclude='node_modules' .

# 2. Upload
$SCP /tmp/project.tar.gz root@<public-IP>:/tmp/

# 3. Extract remotely
$SSH 'mkdir -p /opt/app && cd /opt/app && tar xzf /tmp/project.tar.gz'
```

---

### Option B: Deploy a GitHub project (clone directly)

Applies to: pulling an open-source project from GitHub / GitLab / Gitee.

```bash
$SSH '
apt update && apt install -y git
cd /opt
git clone https://github.com/<user>/<repo>.git app
cd app
# Switch branch or version if needed
# git checkout v1.0.0
'
```

> A private repository needs an SSH Key or a Personal Access Token:
> `git clone https://<token>@github.com/<user>/<repo>.git`

---

### Option C: Docker deployment

Applies to: the project has a Dockerfile or docker-compose.yml.

```bash
$SSH '
# Install Docker (unless this is a Docker CE image)
curl -fsSL https://get.docker.com | sh
systemctl enable docker && systemctl start docker

# Pull and run
docker run -d --name app --restart=always -p 80:8080 <image>

# Or use docker-compose
cd /opt/app
docker compose up -d
'
```

---

### Install + build + run for each technology stack

#### Go project

```bash
$SSH '
# Install Go
wget -q https://go.dev/dl/go1.22.5.linux-amd64.tar.gz -O /tmp/go.tar.gz
rm -rf /usr/local/go && tar -C /usr/local -xzf /tmp/go.tar.gz
export PATH=$PATH:/usr/local/go/bin

# Build
cd /opt/app
go build -o server ./cmd/server/
# or go build -o server .
'
```

#### Node.js project

```bash
$SSH '
# Install Node.js (via NodeSource)
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs

# Install dependencies & build
cd /opt/app
npm install
npm run build  # if there is a build step
'
```

#### Python project

```bash
$SSH '
apt update && apt install -y python3 python3-pip python3-venv

cd /opt/app
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
'
```

#### Java project (Spring Boot)

```bash
$SSH '
apt update && apt install -y openjdk-21-jdk-headless

cd /opt/app
# If there is a Maven Wrapper
./mvnw package -DskipTests
# or upload the jar directly
'
```

#### Pure static site (HTML/CSS/JS)

```bash
$SSH '
apt update && apt install -y nginx

# Copy the static files into the Nginx default directory
cp -r /opt/app/* /var/www/html/
systemctl restart nginx
'
```

---

### Configure the process supervisor (systemd)

Applies to applications that must run continuously, such as Go / Node.js / Python / Java.

```bash
$SSH 'cat > /etc/systemd/system/app.service <<EOF
[Unit]
Description=Web Application
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/app
ExecStart=<start command>
Environment=PORT=80
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable app
systemctl restart app
'
```

**ExecStart examples for each technology stack:**

| Stack | ExecStart |
|--------|-----------|
| Go | `/opt/app/server` |
| Node.js | `/usr/bin/node /opt/app/index.js` |
| Python (Gunicorn) | `/opt/app/venv/bin/gunicorn -w 4 -b 0.0.0.0:80 app:app` |
| Python (Uvicorn) | `/opt/app/venv/bin/uvicorn main:app --host 0.0.0.0 --port 80` |
| Java | `/usr/bin/java -jar /opt/app/target/app.jar --server.port=80` |

> Node.js can also use pm2 instead of systemd:
> ```bash
> npm install -g pm2
> cd /opt/app && pm2 start index.js --name app
> pm2 startup && pm2 save
> ```

---

## 4. Phase 3: Verify and optimize

### 4.1 Verify the service

```bash
# Check the service status
$SSH 'systemctl status app --no-pager'

# HTTP check
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://<public-IP>/

# Open in a browser
http://<public-IP>
```

### 4.2 View logs

```bash
# systemd service logs
$SSH 'journalctl -u app -n 100 --no-pager'

# Docker logs
$SSH 'docker logs app --tail 100'

# pm2 logs
$SSH 'pm2 logs app --lines 100'
```

### 4.3 Bind a domain

```bash
# Add a DNS A record
tccli dnspod CreateRecord \
  --Domain "<domain>" \
  --SubDomain "@" \
  --RecordType "A" \
  --RecordLine "default" \
  --Value "<public-IP>" \
  --TTL 600

# www subdomain
tccli dnspod CreateRecord \
  --Domain "<domain>" \
  --SubDomain "www" \
  --RecordType "A" \
  --RecordLine "default" \
  --Value "<public-IP>" \
  --TTL 600
```

> DNS takes effect within 5-30 minutes.

### 4.4 HTTPS + Nginx reverse proxy

```bash
$SSH '
apt install -y nginx certbot python3-certbot-nginx

# Nginx reverse proxy configuration
cat > /etc/nginx/sites-available/app <<EOF
server {
    listen 80;
    server_name <domain> www.<domain>;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

ln -sf /etc/nginx/sites-available/app /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

# Apply for an SSL certificate (the domain must already resolve to this IP)
certbot --nginx -d <domain> -d www.<domain> --non-interactive --agree-tos -m <email>
'
```

> When using an Nginx reverse proxy, the application listens on 8080 (or another internal port) while Nginx listens on 80/443.

### 4.5 Update the code

```bash
# Option A: upload from local
tar czf /tmp/project.tar.gz --exclude='.git' --exclude='node_modules' .
$SCP /tmp/project.tar.gz root@<public-IP>:/tmp/
$SSH 'cd /opt/app && tar xzf /tmp/project.tar.gz && <rebuild> && systemctl restart app'

# Option B: GitHub pull
$SSH 'cd /opt/app && git pull && <rebuild> && systemctl restart app'

# Option C: Docker update
$SSH 'docker pull <image> && docker stop app && docker rm app && docker run -d --name app --restart=always -p 80:8080 <image>'
```

---

## 5. Common issues

| Issue | Cause and fix |
|------|-----------|
| `AutoGeneratePassword` parameter error | The value must be the uppercase string `YES` / `NO` |
| `sshpass: command not found` | `apt install sshpass` |
| SSH connection refused | Wait 15-20 seconds after the password reset; check the firewall for port 22 |
| Page unreachable | Check the firewall rules + whether the application listens on `0.0.0.0` (not `127.0.0.1`) |
| Go build fails | Confirm `go.mod` exists; check `go version` |
| Node.js `npm install` fails | When memory is short, add swap: `fallocate -l 1G /swapfile && mkswap /swapfile && swapon /swapfile` |
| systemd service fails to start | Inspect the error log with `journalctl -u app -n 50 --no-pager` |
| Docker port conflict | Check port usage with `docker ps`; investigate with `netstat -tlnp` |
| Domain unreachable | DNS propagation takes 5-30 minutes; first connect directly by IP to confirm the service works |
| Let's Encrypt application fails | Confirm the domain resolves to the instance IP and that port 80 is reachable |

---

## 6. API quick reference

| Function | Service | Interface |
|------|------|------|
| Query bundles | lighthouse | `DescribeBundles` |
| Query images | lighthouse | `DescribeBlueprints` |
| Create instance | lighthouse | `CreateInstances` |
| Query instances | lighthouse | `DescribeInstances` |
| Reset password | lighthouse | `ResetInstancesPassword` |
| Create a firewall rule | lighthouse | `CreateFirewallRules` |
| Query firewall rules | lighthouse | `DescribeFirewallRules` |
| Add DNS record | dnspod | `CreateRecord` |
| Query DNS records | dnspod | `DescribeRecordList` |
| Modify DNS record | dnspod | `ModifyRecord` |
| Delete DNS record | dnspod | `DeleteRecord` |

---

## When to use

| Scenario | Recommendation |
|------|------|
| The user wants to deploy a Go/Node/Python/Java/Docker application | Follow the three-phase flow in this document |
| The user wants to deploy a GitHub project | See Option B in this document |
| The user wants to build a website (WordPress/BT Panel/CMS) | Do not use this document; use references/lighthouse-website-setup.md |
| The user wants to deploy OpenClaw | Do not use this document; use references/lighthouse-openclaw-setup.md |
| The user wants to bind a domain and HTTPS | See Phase 4 of this document |
| The user wants a security check | Do not use this document; use references/cvm-security-check.md |
