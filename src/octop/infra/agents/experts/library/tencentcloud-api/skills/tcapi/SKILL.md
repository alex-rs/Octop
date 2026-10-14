---
name: tcapi
display_name: Tencent Cloud API Assistant
description: Skill to call Cloud API for Tencent Cloud. Used for cloud automation or resource management. Triggered when the user needs to query, create, or manage Tencent Cloud resources, or to run Cloud API automation. Prefer the tccli from the venv bundled with Octop; credentials support fully automatic OAuth login.
metadata:
  octop:
    emoji: "☁️"
    label:
      zh: "Tencent Cloud API"
      en: "Tencent Cloud API"
    summary:
      zh: "Query and manage Tencent Cloud resources with tccli and OAuth."
      en: "Query and manage Tencent Cloud resources with tccli and OAuth."
version: 1.0.0
tags: [tccli, cloud-api, tencent-cloud, automation]
keywords: [tencent cloud, tccli, cloud api, cloud resources, cloud management, automated operations]
prompt_template: Run the {action} operation on the {service} product
examples:
  - Query the CVM instances in the Guangzhou region
  - Create a pay-as-you-go cloud server
  - View the COS bucket list
---

# Tencent Cloud API Assistant

Always use the **tccli** command-line tool to call Tencent Cloud APIs, covering operations such as querying, creating, modifying, and deleting cloud resources.

## Applicable scenarios

- Cloud resource query and management (CVM / COS / CBS / VPC / TKE and 200+ other products)
- Automated operations (batch operations, scheduled tasks, script orchestration)
- Cloud API action exploration and documentation search

## Not applicable

- Does not support IaC orchestration tools such as Terraform / Pulumi
- Does not do multi-cloud management (Tencent Cloud only)
- Does not do top-ups, account registration, or other non-API operations

## Prerequisites

- tccli is installed; if not, see [references/install.md](references/install.md)
- Credentials are configured (see "Step 2 Credential configuration" below)

## Core principles

> 1. **Search best practices first → then check the API documentation → finally call the API**. Do not skip the documentation search and call directly, so as to avoid using the wrong API or missing parameters.
> 2. **Online documentation is the live state; the local tccli is a version snapshot**. Judge whether an action/parameter exists by the online documentation (`cloudcache.tencentcs.com`); because of version differences the local tccli may lack newer actions or retain old retired ones. When the local side reports "no such action" or the server side reports "action retired", check the online documentation first to confirm the real situation, then decide whether to upgrade tccli or switch to an alternative action.

## Execution flow

### Step 0: Environment self-check (mandatory for the first task; one probe chains all branches)

**Prefer the tccli in the Python virtual environment (venv) bundled with Octop**: it shares Octop's environment, its version is controllable, and it does not pollute the system Python. Probe order: ① Octop venv → ② system PATH → ③ install temporarily into the venv.

```sh
# ① Locate the Octop venv (via the working directory of the octop main process; fall back to the common path if the process is not found)
OCTOP_PID=$(pgrep -f '\.venv/bin/octop run' | head -1)
OCTOP_ROOT=$([ -n "$OCTOP_PID" ] && readlink -f /proc/$OCTOP_PID/cwd || echo /workspace/octop)
TCCLI="$OCTOP_ROOT/.venv/bin/tccli"

# ② Probe level by level: inside the venv → PATH → if neither has it, install into the venv
if [ -x "$TCCLI" ]; then :
elif command -v tccli >/dev/null 2>&1; then TCCLI=tccli
else uv pip install --python "$OCTOP_ROOT/.venv/bin/python3" tccli; fi

# ③ Verify that it runs and that credentials are valid
"$TCCLI" cvm DescribeRegions >/dev/null 2>&1 && echo "TCCLI_OK" || echo "TCCLI_NEED_CHECK"
```

> If the system has no `uv`: run `"$OCTOP_ROOT/.venv/bin/python3" -m ensurepip --upgrade`, then `python3 -m pip install tccli` with the same path.

Decision branches:

| Probe result | Status | Handling |
|:--------|:-----|:-----|
| Returns `TCCLI_OK` | Installed, runnable, credentials valid | Go straight to Step 1 |
| `command not found` / installation failed | **Not installed** | Follow [references/install.md](references/install.md) to install into the Octop venv (recommended) or install system-wide |
| `bad interpreter` / `No module named tccli` | **Installed but the shebang/environment is broken** | Switch to the Step 5 compatibility mode (call `tccli.main` directly through the venv's `python3 -c`) and use it consistently for the rest of this session |
| Reports `secretId is invalid` / `AuthFailure.SecretIdNotFound` | **Credentials missing** | Go to Step 2 to configure credentials |

> Once the probe passes (`TCCLI_OK`), there is no need to repeat the self-check in this session; just call directly. In all later examples, `tccli` means the detected `$TCCLI` (venv first).

### Step 1: Search the API documentation

Before calling, use curl + grep to search services, actions, best practices, and data structures. See [references/refs.md](references/refs.md) for the complete search methods.

#### 1.1 Discover the service

Search for the tccli service name (such as cvm, cbs):

```sh
curl -s https://cloudcache.tencentcs.com/capi/refs/services.md | grep "Cloud Virtual Machine"
```

Reference output:

```
[cvm](service/cvm/index.md) | Cloud Virtual Machine | 2017-03-12 | ...
```

#### 1.2 Discover best practices

First search whether a best practice matching the current scenario exists:

```sh
curl -s https://cloudcache.tencentcs.com/capi/refs/service/cvm/practices.md | grep reinstall
```

#### 1.3 Search for the action

If the best practices do not cover it, search the service's action list (the action name is the tccli `<Action>`):

```sh
curl -s https://cloudcache.tencentcs.com/capi/refs/service/cvm/actions.md | grep "resize\|disk"
```

#### 1.4 Read the action documentation

Get the parameter descriptions and the supported regions:

```sh
curl -s https://cloudcache.tencentcs.com/capi/refs/service/cvm/action/ResizeInstanceDisks.md
```

#### 1.5 Read the data structures

Data structures referenced by the documentation can be examined further:

```sh
curl -s https://cloudcache.tencentcs.com/capi/refs/service/cvm/model/SystemDisk.md
```

### Step 2: Credential configuration (fully automatic OAuth, no manual commands for the user)

**Principle: the Agent drives everything automatically; the user only needs to click "authorize" once in the browser.** When missing credentials are detected (`AuthFailure.SecretIdNotFound`), do not make the user run commands by hand; execute the automated flow below directly.

#### 2.1 First probe the `auth login` capability (mandatory)

```sh
tccli auth login --help >/dev/null 2>&1 && echo "AUTH_LOGIN_OK" || echo "AUTH_LOGIN_UNSUPPORTED"
```

#### 2.2 Automatic OAuth (the standard action when `AUTH_LOGIN_OK`)

How `tccli auth login` behaves: start a local callback server (ports 9000–9100) → print the authorization link → block waiting for the browser to complete the authorization callback. Automation hinges on four points: **`BROWSER=echo` prevents a headless environment from failing to open a browser and exiting with an error; running in the background keeps the session from hanging; extracting the link from the log and pushing it to the user; treating the credential file landing on disk as the success criterion (rather than process exit)**.

```sh
# ① Start login in the background (BROWSER=echo makes webbrowser silently "succeed": it only prints the link and does not really open a browser)
BROWSER=echo nohup tccli auth login > /tmp/tccli_auth.log 2>&1 &

# ② Poll the log for the authorization link (send it to the user in clickable form as soon as it is obtained)
for i in $(seq 1 10); do
  URL=$(grep -m1 -o 'https://cloud.tencent.com/open/authorize[^ ]*' /tmp/tccli_auth.log) && break
  sleep 1
done
echo "Please open this in your browser and complete the authorization (one click on 'authorize' is enough; I will detect it automatically and continue): $URL"

# ③ Baseline = the modification time of the login log (reliable across tool calls; shell variables do not survive across calls, so do not use them as a baseline)
LOG=/tmp/tccli_auth.log
CRED="$HOME/.tccli/default.credential"
```

**Listening for the authorization (actively wait for the callback to land on disk, with zero replies from the user):**

After sending the link, do not sit and wait for the user to reply — keep doing **bounded listening on the credential file**, so that the moment the user finishes clicking "authorize" it is detected automatically and the flow continues:

```sh
# ④ A single listening window: compare the mtimes of the credential and the log every 3 seconds, for at most 60 seconds (must be below the tool's single-execution timeout;
#    if the timeout ceiling is uncertain, make the window smaller, e.g. seq 1 10≈30 seconds; better to open several windows than to make one window too long)
for i in $(seq 1 20); do
  CRED_TS=$(stat -c %Y "$CRED" 2>/dev/null || echo 0)
  LOG_TS=$(stat -c %Y "$LOG" 2>/dev/null || echo 0)
  [ "$CRED_TS" -gt "$LOG_TS" ] && echo "AUTH_DONE" && break
  sleep 3
done
```

- If `AUTH_DONE` appears within the window → immediately run verification ⑤ and automatically echo the identity (the user does not need to say anything throughout).
- The window times out with no result → **do not judge it a failure and do not resend the link**: say "the authorization link remains valid, I am still listening", then open another listening window (3~5 windows in a row is recommended, about 3~5 minutes); after that you may still hand the turn back, and confirm with ⑤ once the user replies — both paths lead to the same place.
- If during listening the auth process has disappeared and the credential has not landed on disk (`pgrep -f 'auth login'` is empty), only then check the log to locate the cause (port occupied, network unreachable, callback not reachable, etc.) and, after fixing it, start again from ①.

**Verification plan (the authoritative criterion; every scenario eventually goes through this step):**

```sh
# ⑤ The credential file is newer than the login log → authorization succeeded; the identity must then be actually verified
CRED_TS=$(stat -c %Y "$CRED" 2>/dev/null || echo 0)
LOG_TS=$(stat -c %Y "$LOG" 2>/dev/null || echo 0)
if [ "$CRED_TS" -gt "$LOG_TS" ]; then
  tccli sts GetCallerIdentity    # Success → echo the account following the "identity confirmation" rules
else
  tail -5 "$LOG"                 # Not successful → look at the log state; never resend the link because of a timeout
fi
```

- **Success criterion = credential file mtime > login log mtime** (regardless of whether the auth process is still around); the log line "login succeeded, key credentials have been written" is synonymous.
- **Once the credential has landed on disk, never repeat `auth login`** — repeating it invalidates the link the user has already authorized, forcing the user to click again.
- **A tool execution timeout ≠ login failure**: if the listening-window command is killed by a tool timeout, simply run ⑤ once on its own right after; the credential file is the source of truth, and the link is never resent on this basis.

> When the environment can open a browser (such as the desktop version of Octop), drop `BROWSER=echo` and in step ② just say "the browser has popped up, please complete the authorization".

#### 2.3 Fallback path (`AUTH_LOGIN_UNSUPPORTED`, older tccli)

Older versions have no `auth` subcommand. **Upgrade automatically first, then follow 2.2** (installed into the Octop venv, no sudo needed):

```sh
uv pip install --python "$OCTOP_ROOT/.venv/bin/python3" -U tccli
# Without uv: "$OCTOP_ROOT/.venv/bin/python3" -m ensurepip --upgrade && ... -m pip install -U tccli
```

After upgrading, probe again (2.1) and in general `auth login` will then be supported. Only if the upgrade fails (e.g. an offline environment) fall back to semi-manual: guide the user to run the interactive `tccli configure` in their own terminal to enter the keys — **the Agent still does not fill them in, does not ask for them, and does not print them**.

For full details on multiple accounts (--profile), logout, and credential precedence troubleshooting see [references/auth.md](references/auth.md).

**Security red lines**: it is strictly forbidden to ask the user for SecretId/SecretKey, and any operation that might print credentials must be refused (especially `tccli configure list`). In the fully automatic OAuth flow the Agent never touches the plaintext keys, so this red line is satisfied by design.

### Step 3: Call the API

Basic form:

```sh
tccli <service> <Action> [--param value ...] [--region <region>]
```

Input parameters:

| Parameter | Type | Required | Description |
|:-----|:-----|:-----|:-----|
| `service` | string | Yes | Product identifier, such as `cvm`, `cbs`, `vpc`. Obtained by searching as in Step 1.1 |
| `Action` | string | Yes | Action name, such as `DescribeInstances`, `RunInstances`. Obtained by searching as in Step 1.3 |
| `--region` | string | Depends on the action | Region, such as `ap-guangzhou`. Required for most products; may be omitted for global actions (cam, account, dnspod, domain, ssl, ba, tag) |
| `--param value` | Various types | Depends on the action | Action parameters; simple types take the value directly, complex types take a JSON string |

Common example — query the CVM regions:

```sh
tccli cvm DescribeRegions
```

Query instances (a region must be specified):

```sh
tccli cvm DescribeInstances --region ap-guangzhou
```

Parameter rules:

- Parameters of non-simple types must be standard JSON, for example: `--Placement '{"Zone":"ap-guangzhou-2"}'`.
- Example of a creation-type action (replace the parameters as needed):
  ```sh
  tccli cvm RunInstances --InstanceChargeType POSTPAID_BY_HOUR \
    --Placement '{"Zone":"ap-guangzhou-2"}' --InstanceType S1.SMALL1 --ImageId img-xxx \
    --SystemDisk '{"DiskType":"CLOUD_BASIC","DiskSize":50}' --InstanceCount 1 ...
  ```

Output format: tccli returns standard JSON containing a `Response` field. Example:

```json
{
  "Response": {
    "TotalCount": 1,
    "InstanceSet": [{"InstanceId": "ins-xxx", "InstanceName": "test", ...}],
    "RequestId": "eac6b301-..."
  }
}
```

Empty result output: when a query matches nothing, list fields return an empty array and count fields are 0:

```json
{
  "Response": {
    "TotalCount": 0,
    "InstanceSet": [],
    "RequestId": "eac6b301-..."
  }
}
```

Efficiency constraints: the Tencent Cloud API default rate limit is **10 calls/second** (lower for some actions), so batch operations must control the call rate to avoid triggering `RequestLimitExceeded`. Serial calls or added intervals are recommended; do not bombard in parallel.

Avoid parallel calls: tccli currently has a configuration file contention problem with parallel calls, which causes responses to fail. For now, call the actions one by one.

### The local parameter coercion trap (type coercion)

Some tccli versions coerce certain parameters by the local schema before sending them, which conflicts with what the cloud expects, resulting in "permanently InvalidParameter" even though the user actually filled the parameter in correctly — this is **the local tccli's fault, not the user's**:

- **Typical signal**: the server returns `InvalidParameter` with a message pointing to "parameter X has the wrong value type / should be date", while the value you passed in is semantically correct. For example, some TRTC date parameters are locally labelled `Timestamp` and coerced into an integer timestamp, whereas the cloud actually wants a plain `YYYY-MM-DD` date.
- **Identification**: first run `tccli <svc> <Action> --help` to see the parameter type annotations; if the local type is Timestamp/Integer while the online documentation says Date/String, the diagnosis is essentially confirmed.
- **Mitigation (in priority order)**:
  1. Check the online documentation to confirm the real type and format of the parameter (use a plain date rather than a timestamp when necessary);
  2. Try `--cli-unfold-arguments` to stop tccli from doing local merging/conversion;
  3. If local coercion still blocks you, bypass tccli and connect directly with the Python SDK (`tencentcloud-sdk-python`), assigning the raw value (such as a plain date string) to the request parameter as-is, which then passes the cloud's type validation.
- **Important**: this kind of `InvalidParameter` is a "false parameter error"; do not pin it on the user filling in the parameter wrongly.

### Step 3.5: Output parsing rules (stdout/stderr separation and JSON robustness)

tccli's stdout and stderr are two independent streams and must be strictly distinguished when parsing; otherwise warning/error text gets swallowed as a result and parsing crashes.

**① Capture the streams separately; never blindly use `2>&1`**
- A normal call parses stdout only; write stderr to a file separately for diagnosis:
  ```sh
  tccli <service> <Action> [--region <region>] 2>/tmp/tccli_err.log
  ```
- Do not treat `2>&1` as a habitual pattern — as soon as tccli spits `WARNING` / `DeprecationWarning` / version notices to stderr, the merged stream stuffs non-JSON text in front of stdout and `json.loads` crashes outright.

**② "Carve out the JSON" before parsing**
- Even after separating the streams, first use a regex to extract the closed range from the first `{` to the last `}` (or `[...]`) and only then `json.loads`, so that prefix/suffix text (version notices, spaces, carriage returns) does not cause a failure:
  ```python
  import re, json
  m = re.search(r'\{.*\}|\[.*\]', raw, re.DOTALL)
  data = json.loads(m.group(0)) if m else None
  ```

**③ Fallback when parsing fails (do not raise a Traceback)**
- If stdout cannot be parsed as JSON: report "unexpected JSON output" and echo the first N characters of the raw stdout for diagnosis, instead of throwing a Python stack.
- If stdout has no JSON while stderr carries exception information, parse it by the following rules:
  - **Anchor first**: use `[TencentCloudSDKException]` as the sole authoritative anchor to extract `code` / `message` / `requestId`, and **ignore noise such as the `usage:` help block on the same stderr line** (these often crowd into the same stretch as the exception, and you must not "declare a parameter error whenever usage appears" and hit the wrong target).
  - **Distinguish local errors from server-side errors**: with a `requestId` → the server accepted and returned it (such as `InvalidParameter` / `InternalError` / `UnauthorizedOperation`); without a `requestId` and with only `usage:` → a local argparse parameter parsing error, unrelated to the cloud.
  - Translate gracefully into a readable error (see the Step 4 anomaly table); do not degrade into a crash.
- Note: anomalies such as server-side errors, permission denials, and retired actions mostly land on **stderr**, so separating the streams is a precondition for correctly translating error codes.

### Step 4: Anomaly handling

When a call fails, tccli returns JSON containing an `Error` field:

```json
{
  "Response": {
    "Error": { "Code": "AuthFailure.SecretIdNotFound", "Message": "secretId is invalid" },
    "RequestId": "xxx"
  }
}
```

Common errors and their handling:

| Error code | Meaning | Handling |
|:------|:-----|:---------|
| `AuthFailure.SecretIdNotFound` | Credentials missing or invalid | Run the fully automatic OAuth flow of Step 2: `BROWSER=echo` background `auth login` → push the authorization link → poll and wait → verify and echo; for older versions upgrade automatically first (see Step 2 / references/auth.md) |
| `AuthFailure.UnauthorizedOperation` | No permission | Check the CAM policy and confirm the sub-account has permission for this action |
| `InvalidParameterValue` | Invalid parameter value | Consult the action documentation to confirm the valid range of the parameter |
| `ResourceNotFound` | Resource does not exist | Confirm that the resource ID and region are correct |
| `RequestLimitExceeded` | Request rate exceeded | Wait and retry, or reduce the concurrency of calls |
| `UnsupportedOperation` / `DeprecatedOperation` / `InvalidAction` | Action retired/renamed, or recognized locally but already phased out in the cloud | Search the online documentation to confirm the current action and switch to an alternative; do not stubbornly cling to the old action |
| Local `invalid choice: 'XxxAction'` / argparse error, not returned by the server | **The older local tccli lacks this newer action** (release snapshot behind the cloud) | Guide the user to upgrade with `pip install -U tccli`; or check the online documentation to confirm the action exists before operating |
| `DryRunOperation` | DryRun operation succeeded | Not a real error; it means parameter validation passed |
| `UnsupportedRegion` | Unsupported region | Consult the action documentation to confirm the list of supported regions |
| `ResourceInsufficient` | Insufficient resources | Try another availability zone or adjust the specification and retry |
| Network timeout / connection failure | Network unreachable | Check network connectivity and whether a proxy is needed |
| `InternalError` (message contains `nil pointer` / `nil pointer dereference`) | The action is retired in the cloud / the backend service has been torn down | **This is not a random server-side failure; stop retrying**; search the online documentation to confirm the real situation and switch to an alternative action |
| `AuthFailure.TokenFailure` / `FailedOperation.RefreshTokenError` | The OAuth token has expired (browser authorization expired or was revoked) | First follow Step 2 ④ to probe whether the credential file has been updated (a previous authorization may in fact have succeeded but been misjudged); only if it has not been updated, run the fully automatic OAuth of Step 2 again (`tccli auth login --profile <name>`); afterwards echo the current account following the "identity confirmation" rules before continuing |

### Step 5: Fallback when tccli is unavailable

When running `tccli` directly reports `bad interpreter`, `No module named tccli`, or `command not found`, it usually means tccli's shebang points to a Python interpreter that has been uninstalled (an environment problem that not every user encounters). In that case **prefer calling `tccli.main` directly with the Octop venv's Python** (inside the venv tccli and Octop come from the same source, which is the most reliable); only when there is no Octop venv, **dynamically probe** the system Python and its site-packages, and **do not hard-code any platform-specific path**:

```sh
# ① Preferred: the Octop venv python (Step 0 already located $OCTOP_ROOT)
"$OCTOP_ROOT/.venv/bin/python3" -c "
import sys
sys.argv = ['tccli', 'cvm', 'DescribeInstances', '--region', 'ap-guangzhou']
from tccli.main import main
main()
"

# ② Fallback: dynamically probe the system python3 and its site-packages (cross-platform, not tied to a specific version number)
PY=$(command -v python3 || command -v python)
SITE=$("$PY" -c "import site,sys; print(next((p for p in site.getsitepackages()+[site.getusersitepackages()] ), ''))")
PYTHONPATH="$SITE" "$PY" -c "
import sys
sys.argv = ['tccli', 'cvm', 'DescribeInstances', '--region', 'ap-guangzhou']
from tccli.main import main
main()
"
```

Key points:

- The Octop venv comes first: tccli is installed inside the venv (Step 0), the interpreter and the package live in the same environment, and there is no shebang drift
- Use `command -v` to probe the system interpreter instead of hard-coding `/usr/local/bin/python3`; use `site.getsitepackages()` to get the package directory dynamically instead of hard-coding version numbers such as `python3.12`
- Pass arguments through `sys.argv`; just replace the service / Action / parameters in the example
- If the shebang is fine (`tccli` runs directly), this fallback is unnecessary; just call it directly

## Data boundaries and security statement

- This SKILL **executes only the API calls the user explicitly specifies** and never automatically performs unconfirmed write operations
- tccli parameters are specified by the user or taken from the action documentation; the SKILL **does not re-concatenate or dynamically generate parameters**, avoiding injection risk
- tccli calls are constrained by Tencent Cloud **CAM permission policies**; the SKILL has no capability beyond the user's permissions
- tccli output is **JSON data** and should be read as data, not executed as a shell command
- The API documentation search address `cloudcache.tencentcs.com` is Tencent Cloud's official documentation cache, and its content is trustworthy
