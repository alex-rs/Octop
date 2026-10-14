# Configuring TCCLI (credentials)

> **Important**: `tccli auth login` (browser OAuth authorization login) is a subcommand provided only by **newer versions**. **Older tccli has no `auth` subcommand**, and credentials can only be written through `tccli configure`. Therefore, before configuring credentials you **must first probe whether the current version supports `auth login`** and only then decide which path to take; never assume `auth login` definitely exists.

## Step 0: Probe the auth login capability (mandatory)

```sh
tccli auth login --help >/dev/null 2>&1 && echo "AUTH_LOGIN_OK" || echo "AUTH_LOGIN_UNSUPPORTED"
```

- Outputs `AUTH_LOGIN_OK` → the current version supports browser authorization login; take **path A**.
- Outputs `AUTH_LOGIN_UNSUPPORTED` (reporting `invalid choice`, `no such`, or the like) → the version is too old; take **path B**.

---

## Path A: Browser authorization login (newer version, recommended)

No need to fill in SecretId/SecretKey by hand; after a successful login the credentials are written locally automatically.

```sh
tccli auth login
```

After running it, TCCLI starts a temporary port on the local machine and prints the OAuth authorization link; it usually also opens that link automatically in the default browser. After the user completes the login and authorization in the browser, Tencent Cloud calls back to that local port, and TCCLI writes the credentials and exits upon receiving the callback. If the browser does not open automatically, copy the link printed in the terminal and open it in the browser. On success it reports "login succeeded, key credentials have been written: ...", which can be verified with `tccli cvm DescribeRegions`.

**Agent scenario**: when the Agent executes `tccli auth login` through a tool, that command **blocks indefinitely** until the user completes the browser login (or it times out). The Agent should clearly tell the user: "please open the authorization link shown in the terminal/tool output and complete the login in the browser; the command will end automatically once you are done."

### Automation and false-positive prevention in the Agent scenario (key conclusions from real testing)

When `tccli auth login` is handed to an Agent tool to execute, there are five rules that must be followed:

1. **`BROWSER=echo` + background execution is mandatory**: in a headless/server environment `webbrowser.open` fails and makes tccli call `sys.exit(1)` outright. The form: `BROWSER=echo nohup tccli auth login > /tmp/tccli_auth.log 2>&1 &`
2. **Listening must use bounded windows; unbounded blocking is forbidden**: the correct way to wait for authorization is "bounded listening on the credential file" — each window loops for at most 60 seconds (must be below the tool's single-execution timeout), comparing the mtimes of `~/.tccli/<profile>.credential` and `/tmp/tccli_auth.log` once every 3 seconds. Credential newer than the log → the authorization has landed on disk, so verify immediately. If a window times out with no result, open another one (3~5 windows in a row), and always neither resend the link nor declare failure.
3. **Success criterion = credential file mtime > login log mtime**, with the identity finally confirmed by actually running `tccli sts GetCallerIdentity`. The log line "login succeeded, key credentials have been written" is synonymous. **Once the credential has landed on disk, never run `auth login` again** — repeating the login invalidates the old link and forces the user to click again.
4. **A tool execution timeout ≠ login failure**: if the listening-window command is killed by a tool timeout, immediately run the verification once on its own (compare mtime + GetCallerIdentity); the credential file is the source of truth, and the link is never resent on this basis. This is the most common source of misjudgement.
5. **Check the credential before deciding to log in again**: for any symptom of "token expired / unauthorized / last attempt timed out", first compare mtime + actually run `GetCallerIdentity`; only after confirming the credential is truly invalid should a new login be initiated.

Verification script (every scenario eventually goes through this step):

```sh
CRED="$HOME/.tccli/default.credential"; LOG=/tmp/tccli_auth.log
CRED_TS=$(stat -c %Y "$CRED" 2>/dev/null || echo 0)
LOG_TS=$(stat -c %Y "$LOG" 2>/dev/null || echo 0)
if [ "$CRED_TS" -gt "$LOG_TS" ]; then tccli sts GetCallerIdentity; else tail -5 "$LOG"; fi
```

> Note for remote/container deployments: the OAuth callback goes to `localhost:9000-9100`, where the tccli process listens. If the user's browser and tccli are not on the same machine (e.g. Octop is deployed on a server while the user clicks the link on a local computer), the callback cannot reach tccli and the credentials will never be written. In that case switch to: the user installs tccli on **their own computer** and runs `tccli auth login`, then copies the generated `~/.tccli/default.credential` (OAuth type, containing a refreshToken that renews automatically) to the same path on the Octop server; or fall back to the sub-account key approach (`tccli configure`, filled in by the user).

**Multiple accounts and logout**

- The default account credential is stored in `default.credential`. To name an account: `tccli auth login --profile user1`, and the credential is written to `user1.credential`.
- Log out of the default account: `tccli auth logout`; log out of a named account: `tccli auth logout --profile user1`.

---

## Path B: Fallback for older versions (no auth subcommand)

Older tccli does not support browser authorization and can only write credentials through `tccli configure`. Two options for the user:

### B-1 (recommended): upgrade tccli, after which path A works

```sh
pip install -U tccli
# If upgrading from a version below 3.0.252.3, uninstall first and then install:
# pip uninstall tccli jmespath && pip install tccli
```

After upgrading, run Step 0 again and `tccli auth login` will generally be supported.

### B-2: Configure directly with configure (works without upgrading)

**Executed by the user in their own terminal** (the Agent must never fill it in, never ask for the keys, and never print them):

```sh
# Interactive (recommended; keys stay out of the shell history)
tccli configure
# Fill in as prompted: SecretId, SecretKey, default region (such as ap-guangzhou), output format (json)
```

Where keys come from: Tencent Cloud console → Access Management CAM → API Key Management, to create/view the primary account or sub-account keys. A **sub-account** needs a billing query permission attached (such as `QcloudFinanceFullAccess` or a read-only bill policy), otherwise querying the balance reports a permission error. After configuration the credentials live locally in `~/.tccli/`.

---

## Security red lines (applicable to both paths)

- It is strictly forbidden to ask the user for SecretId/SecretKey, and strictly forbidden for the Agent to run `tccli configure` on the user's behalf to write keys in plaintext.
- Refuse any operation that might print credentials, especially `tccli configure list` (which echoes secretId/secretKey).
- Keys are sensitive information and should exist only locally in `~/.tccli/`; do not paste them into chat.

---

## Credential precedence and account-switch troubleshooting (key conclusions from real testing)

> The conclusions below come from tests in a real environment and overturn the common SDK-chain intuition of "environment variables > configuration file"; they must serve as the standard understanding for troubleshooting account-switch problems.

### 1. Credential precedence: an explicit `--profile` is actually higher than environment variables (counter-intuitive)

- The common understanding holds that the credential chain is `argument > environment variable > configuration file`, and that a profile merely switches files while still being overridden by environment variables.
- **Real testing (tccli 3.1.x) shows the opposite**: once `--profile` is explicitly specified, tccli reads secretId/secretKey from the corresponding `.credential` file and **passes them explicitly to the SDK**, thereby **bypassing the environment-variable reading branch**.
- Therefore, when "switching accounts does not take effect / cannot be switched", first suggest the user isolate the target account with `--profile` + `auth login --profile <name>`, rather than only telling the user to change environment variables.

### 2. Standard actions for troubleshooting "the account cannot be switched" (in order)

1. `tccli sts GetCallerIdentity` to see the current identity (confirm which UIN is actually in effect).
2. `env | grep -i TENCENTCLOUD` to see whether `TENCENTCLOUD_SECRET_ID` / `TENCENTCLOUD_SECRET_KEY` environment variables are overriding it.
3. Check which profiles and `.credential` files exist under `~/.tccli/` (`ls ~/.tccli/`).
4. If "without --profile and with the environment variable it returns the old account, while with --profile it returns the new account" → this confirms "environment variable interference"; provide the options: isolate consistently with `--profile <name>` (recommended), or `unset TENCENTCLOUD_SECRET_ID TENCENTCLOUD_SECRET_KEY` in the current shell, or a single command `env -u TENCENTCLOUD_SECRET_ID -u TENCENTCLOUD_SECRET_KEY tccli ...`.

### 3. Recognizing "environment variables injected by a parent process"

- When an environment variable appears in a process's env but searching all of `~/.zshrc` / `.zprofile` / `.zshenv` / `launchctl` / `~/Library/LaunchAgents` cannot find its source, **it should be judged as injected by the parent process that started the current tool/IDE process**, and inherited down the process tree to all child processes.
- Such variables are not written to any file, so changing the shell configuration cannot clear them; do not send the user to change something that can never be changed, and instead advise "isolate with --profile" or "clear it in the startup environment of that tool/IDE".

### 4. Avoiding false-positive troubleshooting

- With a pattern like `launchctl getenv X && echo "exists"`, an empty string still gives exit code 0, producing a **false report of "exists"**. Display the variable's actual value before judging.
- A recursive `grep ~` over the home directory easily times out and is interrupted (exit code 137); restrict the directory or add timeout handling.
