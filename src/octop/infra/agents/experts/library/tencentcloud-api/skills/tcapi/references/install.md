# Installing TCCLI

**Preferred: install it into the Python virtual environment (venv) bundled with Octop** — consistent with the Octop runtime, version-controllable, does not pollute the system Python, and needs no sudo. Agent commands run by Octop experts inherit that environment.

**Locate the Octop venv** (via the working directory of the octop main process):

```sh
OCTOP_PID=$(pgrep -f '\.venv/bin/octop run' | head -1)
OCTOP_ROOT=$([ -n "$OCTOP_PID" ] && readlink -f /proc/$OCTOP_PID/cwd || echo /workspace/octop)
```

**Installation methods (in priority order)**:

```sh
# Method one (recommended): install into the Octop venv with uv
uv pip install --python "$OCTOP_ROOT/.venv/bin/python3" tccli

# Method two: without uv, use the venv's own pip (run ensurepip first)
"$OCTOP_ROOT/.venv/bin/python3" -m ensurepip --upgrade
"$OCTOP_ROOT/.venv/bin/python3" -m pip install tccli

# Method three: system pip (when using tccli standalone on desktop/CLI)
pip install tccli

# If upgrading from a version below 3.0.252.3, uninstall first and then install:
# pip uninstall tccli jmespath && pip install tccli
```

Upgrading works the same way, adding `-U`: `uv pip install --python "$OCTOP_ROOT/.venv/bin/python3" -U tccli`

Other system installation methods:

```sh
# macOS Homebrew
brew tap tencentcloud/tccli
brew install tccli
# Update: brew upgrade tccli

# Install from source
# git clone https://github.com/TencentCloud/tencentcloud-cli.git && cd tencentcloud-cli && python setup.py install
```

Verify the installation:

```sh
"$OCTOP_ROOT/.venv/bin/tccli" --version   # verify inside the venv
tccli --version                            # verify the system installation
```
