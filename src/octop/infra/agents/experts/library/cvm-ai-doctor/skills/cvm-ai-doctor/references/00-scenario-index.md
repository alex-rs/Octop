# Scenario Index

> **Purpose**: Tier 2 scenario routing table. When Tier 1 (the 10 scenarios built into SKILL.md) does not match, search keywords here to locate the diagnostic flow.
> **Platforms**: Linux (full) | macOS (full) | Windows (basic)
> **How to use**: search the user's keywords → find the matching scenario → run the recommended path

---

## Cross-Platform Rules

Detect the OS before running anything: `OS_TYPE=$(uname -s)`

| Resource | Linux | macOS | Windows |
|------|-------|-------|---------|
| Memory | `free -h` | `vm_stat` + `sysctl hw.memsize` | `wmic OS get TotalVisibleMemorySize,FreePhysicalMemory` |
| CPU | `lscpu` / `top -b -n 1` | `sysctl -n machdep.cpu.brand_string` / `top -l 1 -n 20` | PowerShell `Get-Process \| Sort CPU -Desc` |
| Disk | `df -h` / `lsblk` | `df -h` / `diskutil list` | `wmic logicaldisk get caption,size,freespace` |
| Network | `ip addr` / `ss` | `ifconfig` / `netstat` | `ipconfig /all` / `netstat -e` |
| Logs | `journalctl -p err` | `log show --predicate 'messageType == "error"'` | PowerShell `Get-WinEvent -FilterHashtable @{LogName='System'; Level=2}` |
| Services | `systemctl --failed` | `launchctl list \| grep '^\\-'` | `Get-Service \| Where Status -ne Running` |
| Package manager | `apt install` | `brew install` | `winget install` |

See the individual `commands/*.md` files for the detailed command tables.

**Linux-only scenarios** (no cross-platform adaptation needed): PipeWire, BTRFS/Snapper, and the systemctl-related deep features.

---

## High-Frequency Scenarios (⭐⭐⭐⭐⭐)

### 1.1 The system as a whole is slow/lagging
**Keywords**: slow, lag, sluggish, slow response

**Path**: Quick full scan with `resource-saturation-quick.md` → Deep on flagged component

**Commands**: `commands/debugging/diagnose-slowdown.md`, `commands/system-health/system-health-checkup.md`

---

### 1.2 Slow boot
**Keywords**: slow boot, slow startup, long startup time

**Path**: `system-logs-quick.md` → boot service analysis

**Commands**: `commands/debugging/boot/review-boot.md`, `commands/debugging/boot/check-boot-logs.md`, `commands/debugging/boot/failed-boot-services.md`, `commands/optimisation/optimize-boot-speed.md`

---

### 1.3 Application is slow
**Keywords**: one particular application is slow, browser is slow, IDE is slow, app lag

**Path**: confirm process resources → Deep CPU analysis → application-specific diagnostics

**Commands**: `commands/debugging/diagnose-slowdown.md`

---

### 2.1 High CPU usage
**Keywords**: high CPU, CPU at 100%, fan spinning wildly, CPU usage high

**Path**: `resource-saturation-quick.md` → `resource-saturation-deep-cpu.md` → identify high-CPU processes

**Commands**: `commands/hardware/hardware-profilers/by-component/profile-cpu.md`

---

### 2.2 Insufficient memory / high memory usage
**Keywords**: not enough memory, memory full, OOM, swap full, high memory usage

**Path**: `resource-saturation-quick.md` → `resource-saturation-deep-memory.md` → swap/OOM killer

**Commands**: `commands/hardware/hardware-profilers/by-component/profile-ram.md`

---

### 2.3 Insufficient disk space
**Keywords**: disk full, no space left, not enough space

**Path**: `df -h` → find large files → clean up

**Commands**: `commands/optimisation/large-files.md`, `commands/storage/storage-deep-dive.md`

---

### 2.4 Slow disk I/O
**Keywords**: slow disk, high I/O wait, disk slow, slow reads and writes

**Path**: `resource-saturation-quick.md` → `resource-saturation-deep-disk.md` → SMART check

**Commands**: `commands/storage/health-checks/check-drive-health.md`, `commands/storage/health-checks/smart-status.md`, `commands/storage/storage-deep-dive.md`

---

### 2.5 Slow network / network problems
**Keywords**: slow network, slow connection speed, high ping, connection timeout, network slow

**Path**: `resource-saturation-quick.md` → network diagnostics

**Commands**: `commands/network/diagnose-network-issues.md`, `commands/network/lan/diagnose-lan-connectivity.md`

---

### 3.1 Comprehensive health check
**Keywords**: check the system, health check, system check

**Path**: 3 Quick scans → Deep if there are anomalies → comprehensive report

**References**: `resource-saturation-quick.md`, `system-logs-quick.md`, `disk-smart-quick.md`, `hardware-health-quick.md`

**Commands**: `commands/system-health/system-health-checkup.md`

---

### 3.2 Periodic maintenance check
**Keywords**: periodic check, maintenance, routine check

**Path**: system updates → disk health → log errors → service status

**Commands**: `commands/system-health/system-upgrade.md`, `commands/system-health/review-startup-services.md`

---

### 4.1 System crash / reboot
**Keywords**: crash, reboot, kernel panic

**Path**: `system-logs-quick.md` → kernel logs → hardware errors

**References**: `system-logs-quick.md`, `hardware-health-quick.md`

**Commands**: `commands/debugging/diagnose-crash.md`

---

### 4.2 Service failure / failed startup
**Keywords**: service is down, service failed, failed startup, service will not start

**Path**: `systemctl --failed` → service logs → boot logs

**Commands**: `commands/debugging/boot/failed-boot-services.md`, `commands/logging/check-failed-units.md`

---

### 4.3 Error log analysis
**Keywords**: error, exception

**Path**: `system-logs-quick.md` → `system-logs-deep` → triage by category

**Commands**: `commands/logging/analyze-journal-errors.md`, `commands/logging/tail-system-logs.md`

---

### 5.1 Hardware health check
**Keywords**: hardware check, sensors, temperature

**Path**: `hardware-health-quick.md` → specific components

**Commands**: `commands/hardware/hardware-profilers/hardware-profile.md`, `commands/hardware/hardware-profilers/hardware-identity.md`

---

### 5.2 Disk hardware failure
**Keywords**: disk is broken, disk failed, SMART error, bad sectors

**Path**: `disk-smart-quick.md` → `disk-smart-deep.md`

**Commands**: `commands/storage/health-checks/check-drive-health.md`, `commands/storage/health-checks/smart-status.md`

---

### 5.3 Overheating / cooling problems
**Keywords**: high temperature, overheating, hot, thermal, fan

**Path**: `hardware-health-quick.md` → CPU frequency → fan status

---

### 5.4 GPU problems
**Keywords**: GPU, graphics card, graphics, display problems

**Path**: GPU status → driver check → GPU optimization

**Commands**: `commands/hardware/hardware-profilers/by-component/profile-gpu.md`, `commands/hardware/check-gpu-os-optimization.md`, `commands/hardware/review-gpu-settings.md`

---

### 6.1 Inaccurate time
**Keywords**: wrong time, clock is off, time sync, NTP

**Path**: `time-sync.md` Quick → Deep

---

## Medium-Frequency Scenarios (⭐⭐⭐⭐)

### 7.1 LAN connectivity problems
**Keywords**: local area network, LAN, intranet connection, cannot connect over SSH

**Commands**: `commands/network/lan/diagnose-lan-connectivity.md`, `commands/network/lan/scan-lan.md`, `commands/network/lan/lan-ssh-setup.md`, `commands/network/lan/smart-arp.md`

---

### 7.2 Firewall problems
**Keywords**: firewall, port blocked, connection refused

**Commands**: `commands/security/firewall/analyze-firewall.md`

---

### 8.1 Security audit
**Keywords**: security check, security audit, vulnerability scan, security assessment

**Commands**: `commands/security/posture-diagnostics/security-posture-check.md`, `commands/security/audits/probe-vulnerabilities.md`, `commands/security/audits/write-audit.md`

---

### 8.2 Permission problems
**Keywords**: insufficient permissions, permission denied, cannot access, access denied

**Commands**: `commands/configuration/permissions/debug-folder-permissions.md`

---

### 8.3 Spyware / viruses
**Keywords**: virus, trojan, spyware, malware, infected

**Commands**: `commands/security/detect-spyware.md`, `commands/security/av/install-clamav.md`

---

### 9.1 SSH configuration
**Keywords**: SSH, key, SSH key, remote connection

**Commands**: `commands/configuration/ssh/manage-ssh-keys.md`, `commands/configuration/ssh/list-ssh-connections.md`

---

### 9.2 Environment variables / PATH
**Keywords**: PATH, environment variables, command not found

**Commands**: `commands/configuration/check-path.md`, `commands/configuration/bash/validate-bashrc.md`, `commands/configuration/bash/add-bash-alias.md`

---

### 9.3 Git configuration
**Keywords**: Git, Git configuration, gitignore, Git username

**Commands**: `commands/configuration/git/check-git-config.md`, `commands/configuration/git/check-global-gitignore.md`

---

### 10.1 Package management problems
**Keywords**: apt errors, package management, package manager, dependency problems

**Commands**: `commands/package-management/check-apt-health.md`, `commands/package-management/check-third-party-repos.md`, `commands/package-management/identify-unused-packages.md`, `commands/package-management/configure-auto-updates.md`, `commands/package-management/evaluate-installed-software.md`

---

### 10.2 Docker problems
**Keywords**: Docker, container, docker compose

**Commands**: `commands/dev-tools/docker/setup-docker.md`

---

### 10.3 Python environment
**Keywords**: Python, conda, pyenv, virtual environment, pip

**Commands**: `commands/dev-tools/python/identify-python-environments.md`, `commands/dev-tools/python/pyenv/setup-pyenv.md`, `commands/dev-tools/python/conda/manage-conda-environments.md`, `commands/dev-tools/python/conda/setup-conda-data-analysis.md`, `commands/dev-tools/python/conda/setup-conda-llm-finetune.md`, `commands/dev-tools/python/conda/setup-conda-rocm.md`, `commands/dev-tools/python/conda/setup-conda-stt-finetune.md`

---

## Low-Frequency Scenarios (⭐⭐⭐)

### 11.1 RAID configuration
**Keywords**: RAID, disk array
**Commands**: `commands/storage/raid/check-raid-config.md`

### 11.2 Network mounts
**Keywords**: NFS, SMB, network share, mount
**Commands**: `commands/storage/network-mounts/setup-nfs-mounts.md`, `commands/storage/network-mounts/setup-smb-mounts.md`

### 11.3 BTRFS snapshots (Linux-only)
**Keywords**: BTRFS, snapshot, snapper
**Commands**: `commands/storage/health-checks/btrfs-snapper-health.md`

---

### 12.1 Display problems
**Keywords**: monitor, multiple monitors, resolution, display
**Commands**: `commands/display/list-connected-displays.md`, `commands/display/setup-multi-monitor.md`, `commands/display/optimize-display-scaling.md`, `commands/display/switch-display-profile.md`, `commands/display/capture-current-config.md`

### 12.2 KDE Plasma
**Keywords**: KDE, Plasma, desktop environment
**Commands**: `commands/kde/optimize-kde-performance.md`, `commands/kde/reset-plasma-config.md`, `commands/kde/backup-kde-settings.md`, `commands/kde/list-kde-shortcuts.md`

### 12.3 Audio problems
**Keywords**: audio, sound, microphone
**Commands**: `commands/audio/mic-always-100.md`, `commands/audio/set-as-default-mic.md`, `commands/system-health/optimize-pipewire.md`

### 12.4 Bluetooth problems
**Keywords**: Bluetooth, headphones will not connect
**Commands**: `commands/bluetooth/reset-bluetooth.md`, `commands/bluetooth/troubleshoot-bluetooth.md`

---

### 13.1 Virtualization check
**Keywords**: virtualization, virtual machine, VM, KVM, VirtualBox
**Commands**: `commands/virtualization/check-virtualization.md`

---

### 14.1 Hibernate / wake
**Keywords**: hibernate, sleep, suspend, wake
**Commands**: `commands/power-mgmt/hibernation.md`, `commands/hardware/evaluate-wake-devices.md`, `commands/power-mgmt/wol-setup.md`

---

### 15.1 USB devices
**Keywords**: USB, USB flash drive, USB device not recognized
**Commands**: `commands/peripherals/list-usb-devices.md`, `commands/peripherals/evtest.md`

### 15.2 Printers
**Keywords**: printer, printing problems
**Commands**: `commands/utilities/diagnose-printers.md`

---

### 16.1 IDE problems
**Keywords**: IDE, VSCode, editor
**Commands**: `commands/dev-tools/suggest-ides.md`, `commands/dev-tools/ides/optimize-vscode-installation.md`

### 16.2 Node.js environment
**Keywords**: Node, npm, Node.js
**Commands**: `commands/dev-tools/node/node-version-check.md`, `commands/dev-tools/node/npm-install.md`

### 16.3 SDK management
**Keywords**: SDK, SDKMAN, Java
**Commands**: `commands/dev-tools/sdks/sdk-check.md`, `commands/installation/clis/install-sdkman.md`

---

### 17.1 Local AI setup
**Keywords**: AI, machine learning, Ollama, ComfyUI
**Commands**: `commands/ai/local-ai/gpu-ai-ml-assessment.md`, `commands/ai/local-ai/ollama/setup-ollama.md`, `commands/ai/local-ai/ollama/suggest-ollama-models.md`, `commands/ai/local-ai/ollama/prune-ollama.md`, `commands/ai/local-ai/comfyui/setup-comfyui.md`, `commands/ai/local-ai/audit-local-ai-packages.md`

### 17.2 AI CLI tools
**Keywords**: AI CLI, command-line AI, MCP
**Commands**: `commands/ai/cli-seeders/ai-clis.md`, `commands/ai/cli-seeders/evaltools.md`, `commands/ai/mcp/manage-mcp-servers.md`

### 17.3 Speech recognition
**Keywords**: speech recognition, STT, speech to text
**Commands**: `commands/ai/stt/setup-speech-to-text.md`

---

### 18.1 File organization
**Keywords**: organize files, file categorization
**Commands**: `commands/fs-optimisation/tidy-up/desktop-tidy.md`, `commands/fs-optimisation/tidy-up/organize-loose-files.md`, `commands/fs-optimisation/separate/separate-by-filetype.md`, `commands/fs-optimisation/separate/separate-photos-and-video.md`, `commands/fs-optimisation/idate/suggest-folder-structure.md`

### 18.2 Folder operations
**Keywords**: folder, directory, merge, split
**Commands**: `commands/fs-optimisation/consolidate/consolidate-folders.md`, `commands/fs-optimisation/flatten/flatten.md`, `commands/fs-optimisation/chunk/chunk-this-dir.md`

---

### 19.1 Backup target identification
**Keywords**: backup, data backup
**Commands**: `commands/backup/identify-backup-targets.md`

---

### 20.1 Font management
**Keywords**: font, install fonts
**Commands**: `commands/fonts/list-fonts.md`, `commands/fonts/install-google-fonts.md`

### 20.2 Video codecs
**Keywords**: codec, video playback
**Commands**: `commands/media/check-codecs.md`, `commands/video/codecs.md`

### 20.3 Repository management
**Keywords**: Git repository, organize repositories, repo
**Commands**: `commands/repositories/organise-repos.md`, `commands/repositories/delete-old-repos.md`

### 20.4 Software installation
**Keywords**: install software, install, install from GitHub
**Commands**: `commands/installation/install-from-gh.md`, `commands/installation/install-this.md`, `commands/program-management/install-github-program.md`

---

## Category C: Cluster Management Scenarios (requires collaboration with the tencentcloud-infra skill)

> **Prerequisite**: enter this category when the user mentions keywords such as "cluster", "all CVMs", or "multiple servers".
> All cloud API calls are executed through the tencentcloud-infra skill.
> See `references/skill-collaboration-tencentcloud.md` for the full collaboration protocol.

---

### C1 Quick cluster health check
**Keywords**: cluster health, cluster status, status of all CVMs, all nodes, fleet check, batch check
**Path**: `references/cluster-quick-check.md` → `references/cluster-health-score.md`
**Collaborating skill**: tencentcloud-infra (DescribeInstances + GetMonitorData + TAT RunCommand)
**Duration**: about 30 seconds

---

### C2 Deep cluster diagnosis
**Keywords**: deep cluster diagnosis, slow cluster, cause of cluster anomalies, details for a given node, deep node analysis
**Path**: `references/cluster-deep-analysis.md` (executed on top of the C1 quick check)
**Collaborating skill**: tencentcloud-infra (TAT RunCommand)
**Duration**: about 60-120 seconds (depends on the number of nodes)

---

### C3 Cluster health scoring
**Keywords**: cluster score, cluster report, health score, node score
**Path**: `references/cluster-health-score.md` (needs C1 data as input)
**Collaborating skill**: — (pure computation, input comes from C1)

---

### C4 Cluster node discovery / configuration
**Keywords**: discover cluster nodes, configure the cluster, add a cluster, cluster node list, register nodes
**Path**: `references/cluster-discovery.md`
**Collaborating skill**: tencentcloud-infra (DescribeInstances + DescribeAutomationAgentStatus)

---

### C5 Cluster node remediation
**Keywords**: restart cluster nodes, recover nodes, start stopped instances, restart services, restart ins-
**Path**: `references/cluster-remediation.md`
**Collaborating skill**: tencentcloud-infra (TAT RunCommand / RebootInstances / StartInstances)
**Risk level**: 🟡~🔴 (confirmation required)

---

### C6 Cascading cluster memory alerts
**Keywords**: high memory on all nodes, cluster memory problem, multiple OOMs, cascading memory
**Path**: `references/cluster-deep-analysis.md` § Pattern 1 (Memory Cascade)
**Collaborating skill**: tencentcloud-infra (TAT RunCommand)

---

### C7 Unbalanced cluster load
**Keywords**: one node is especially busy, uneven cluster load, load skew, split-brain
**Path**: `references/cluster-deep-analysis.md` § Pattern 2 (Load Asymmetry)
**Collaborating skill**: tencentcloud-infra (CLB DescribeTargetHealth + TAT)

---

### C8 Cluster disk alerts
**Keywords**: disks full on all nodes, high cluster disk usage, disk alerts on multiple machines
**Path**: `references/cluster-deep-analysis.md` § Pattern 3 (Correlated Disk Growth)
**Collaborating skill**: tencentcloud-infra (TAT RunCommand)

---

**Version**: 2.1 (adds Category C cluster scenarios) | **Updated**: 2026-05-08
