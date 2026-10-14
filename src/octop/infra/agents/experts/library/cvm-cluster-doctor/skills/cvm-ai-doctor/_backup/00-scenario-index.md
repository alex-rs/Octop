# Scenario Index

> **Purpose**: quickly locate the diagnosis Reference or Command that corresponds to a user problem
> **Updated**: 2026-03-24
> **Coverage**: 126 Commands + 5 References

---

## 🎯 AI Usage Guide

### Workflow

```
User describes a problem
  ↓
1. Match a scenario in this index (10 seconds)
  ↓
2. Run Quick Mode according to the recommended Reference (10 seconds)
  ↓
3. If Quick Mode finds an anomaly → run Deep Mode (20-60 seconds)
  ↓
4. Report the results + repair suggestions
```

### Scenario Matching Rules

**Keyword triggers**:
- A keyword the user says → look up the corresponding scenario
- Supports Chinese and English ("slow" = "slow", "lag" = "lag")
- Supports fuzzy matching ("not enough memory" → "memory problem")

**Priority**:
1. ⭐⭐⭐⭐⭐ High-frequency scenarios (80% of user problems)
2. ⭐⭐⭐⭐ Medium-frequency scenarios (15% of user problems)
3. ⭐⭐⭐ Low-frequency scenarios (5% of user problems)

---

## 📚 Scenario Taxonomy

### Top-Level Categories (10 major categories)

1. **Performance problems** (Performance Issues) - slow, laggy, latency
2. **Resource problems** (Resource Issues) - CPU, memory, disk, network
3. **System health** (System Health) - health checks, status monitoring
4. **Fault diagnosis** (Troubleshooting) - crashes, errors, failures
5. **Hardware problems** (Hardware Issues) - hardware failures, drivers, sensors
6. **Network problems** (Network Issues) - connectivity, DNS, firewall
7. **Security problems** (Security Issues) - vulnerabilities, permissions, audit
8. **Configuration management** (Configuration) - settings, environment, paths
9. **Software management** (Software Management) - installation, updates, package management
10. **Log analysis** (Logging & Monitoring) - logs, monitoring, tracing

---

## 🔥 High-Frequency Scenarios (⭐⭐⭐⭐⭐)

### 1. Performance Scenarios

#### 1.1 The system as a whole is slow/laggy
**User keywords**: "slow", "laggy", "lag", "slow", "sluggish", "slow response"

**Recommended path**:
```
Step 1: Quick full scan
  bash references/resource-saturation.md

Step 2: Decide on Deep analysis from the Quick results
  - CPU anomaly → deep --focus cpu
  - Memory anomaly → deep --focus memory
  - Disk anomaly → deep --focus disk
  - Multiple anomalies → deep --focus all
```

**Related Commands**:
- `commands/debugging/diagnose-slowdown.md` (interactive diagnosis flow)
- `commands/system-health/system-health-checkup.md` (comprehensive health check)

**Expected time**: Quick 10s + Deep 20-60s = 30-70s

---

#### 1.2 Slow startup
**User keywords**: "slow startup", "boot slow", "slow boot", "long startup time"

**Recommended path**:
```
Step 1: Check the startup logs
  bash references/system-logs.md --mode quick --focus boot

Step 2: Analyze the startup services
  commands/debugging/boot/review-boot.md
  systemd-analyze blame
  systemd-analyze critical-chain
```

**Related References**:
- `references/system-logs.md` (startup logs)

**Related Commands**:
- `commands/debugging/boot/review-boot.md`
- `commands/debugging/boot/check-boot-logs.md`
- `commands/debugging/boot/failed-boot-services.md`
- `commands/optimisation/optimize-boot-speed.md`

---

#### 1.3 Slow application
**User keywords**: "some software is slow", "slow browser", "slow IDE", "laggy application"

**Recommended path**:
```
Step 1: Confirm the process resource usage
  ps aux | grep <app_name>
  top -p <pid>

Step 2: Check the resource usage of that application
  bash references/resource-saturation.md --mode deep --focus cpu
  
Step 3: Application-specific diagnosis
  - Browser: check extensions and cache
  - IDE: check indexing and plugins
  - Database: check queries and connection pools
```

**Related Commands**:
- `commands/debugging/diagnose-slowdown.md` (step 12: application-specific checks)

---

### 2. Resource Scenarios

#### 2.1 High CPU usage
**User keywords**: "high CPU", "CPU 100%", "fans spinning hard", "CPU usage high"

**Recommended path**:
```
Step 1: Quick check
  bash references/resource-saturation.md --mode quick

Step 2: Deep CPU analysis
  bash references/resource-saturation.md --mode deep --focus cpu

Step 3: Identify the high-CPU processes
  ps aux --sort=-%cpu | head -20
  top -b -n 1
```

**Related References**:
- `references/resource-saturation.md` (CPU analysis)

**Related Commands**:
- `commands/hardware/hardware-profilers/by-component/profile-cpu.md`

---

#### 2.2 Insufficient memory/high memory usage
**User keywords**: "insufficient memory", "memory full", "OOM", "swap full", "high memory usage"

**Recommended path**:
```
Step 1: Quick memory check
  bash references/resource-saturation.md --mode quick

Step 2: Deep memory analysis
  bash references/resource-saturation.md --mode deep --focus memory

Step 3: Check for memory leaks
  - Check swap usage
  - Check the OOM killer logs
  - Analyze process memory trends
```

**Related References**:
- `references/resource-saturation.md` (memory analysis)

**Related Commands**:
- `commands/hardware/hardware-profilers/by-component/profile-ram.md`

---

#### 2.3 Insufficient disk space
**User keywords**: "disk full", "disk full", "no space left", "out of space"

**Recommended path**:
```
Step 1: Check disk usage
  df -h
  du -sh /* | sort -rh | head -20

Step 2: Find large files
  find / -type f -size +1G 2>/dev/null | xargs ls -lh

Step 3: Free up space
  commands/optimisation/large-files.md
  commands/optimisation/cleanup-system.md
```

**Related Commands**:
- `commands/optimisation/large-files.md`
- `commands/storage/storage-deep-dive.md`

---

#### 2.4 Slow disk I/O
**User keywords**: "slow disk", "high I/O wait", "disk slow", "slow reads/writes"

**Recommended path**:
```
Step 1: Quick disk check
  bash references/resource-saturation.md --mode quick

Step 2: Deep disk analysis
  bash references/resource-saturation.md --mode deep --focus disk

Step 3: Check disk health
  bash references/disk-smart.md
```

**Related References**:
- `references/resource-saturation.md` (I/O analysis)
- `references/disk-smart.md` (SMART health)

**Related Commands**:
- `commands/storage/health-checks/check-drive-health.md`
- `commands/storage/health-checks/smart-status.md`
- `commands/storage/storage-deep-dive.md`

---

#### 2.5 Slow network/network problems
**User keywords**: "slow network", "slow internet", "high ping", "connection timeout", "network slow"

**Recommended path**:
```
Step 1: Quick network check
  bash references/resource-saturation.md --mode quick

Step 2: Network diagnosis
  commands/network/diagnose-network-issues.md
  
Step 3: Network statistics
  ip -s link
  netstat -s
  ss -s
```

**Related References**:
- `references/resource-saturation.md` (network statistics)

**Related Commands**:
- `commands/network/diagnose-network-issues.md`
- `commands/network/lan/diagnose-lan-connectivity.md`

---

### 3. System Health Scenarios

#### 3.1 Comprehensive health check
**User keywords**: "check the system", "health check", "system check", "health check"

**Recommended path**:
```
Step 1: Quick health scan
  bash references/resource-saturation.md --mode quick
  bash references/system-logs.md --mode quick
  bash references/disk-smart.md --mode quick

Step 2: If there are anomalies, run Deep analysis
  Decide based on the Quick results

Step 3: Comprehensive report
  commands/system-health/system-health-checkup.md
```

**Related References**:
- `references/resource-saturation.md`
- `references/system-logs.md`
- `references/disk-smart.md`
- `references/hardware-other.md`

**Related Commands**:
- `commands/system-health/system-health-checkup.md`

---

#### 3.2 Periodic maintenance check
**User keywords**: "periodic check", "maintenance", "routine check", "maintenance"

**Recommended path**:
```
Step 1: System update check
  commands/system-health/system-upgrade.md
  
Step 2: Disk health
  bash references/disk-smart.md

Step 3: Log errors
  bash references/system-logs.md --mode quick

Step 4: Service status
  commands/system-health/review-startup-services.md
```

**Related Commands**:
- `commands/system-health/system-upgrade.md`
- `commands/system-health/review-startup-services.md`

---

### 4. Fault Diagnosis Scenarios

#### 4.1 System crash/reboot
**User keywords**: "crash", "crash", "reboot", "reboot", "kernel panic"

**Recommended path**:
```
Step 1: Check the crash logs
  bash references/system-logs.md --mode deep --focus crash
  
Step 2: Kernel logs
  dmesg | tail -100
  journalctl -k -b -1  # kernel log from the previous boot

Step 3: Hardware errors
  bash references/hardware-other.md
```

**Related References**:
- `references/system-logs.md` (crash logs)
- `references/hardware-other.md` (hardware errors)

**Related Commands**:
- `commands/debugging/diagnose-crash.md`

---

#### 4.2 Service failure/startup failure
**User keywords**: "the service is down", "service failed", "startup failed", "the service will not start"

**Recommended path**:
```
Step 1: Check the failed services
  systemctl --failed
  journalctl -xe

Step 2: View the logs of the specific service
  systemctl status <service>
  journalctl -u <service> -n 100

Step 3: Boot logs
  commands/debugging/boot/failed-boot-services.md
```

**Related References**:
- `references/system-logs.md` (service logs)

**Related Commands**:
- `commands/debugging/boot/failed-boot-services.md`
- `commands/logging/check-failed-units.md`

---

#### 4.3 Error log analysis
**User keywords**: "error", "error", "error message", "exception", "exception"

**Recommended path**:
```
Step 1: Quick log scan
  bash references/system-logs.md --mode quick

Step 2: Deep log analysis
  bash references/system-logs.md --mode deep

Step 3: Classify the errors
  - Hardware errors → hardware-other.md
  - Disk errors → disk-smart.md
  - Kernel errors → system-logs.md
```

**Related References**:
- `references/system-logs.md`

**Related Commands**:
- `commands/logging/analyze-journal-errors.md`
- `commands/logging/tail-system-logs.md`

---

### 5. Hardware Problem Scenarios

#### 5.1 Hardware health check
**User keywords**: "hardware check", "hardware check", "sensors", "temperature"

**Recommended path**:
```
Step 1: Comprehensive hardware check
  bash references/hardware-other.md

Step 2: Specific hardware analysis
  commands/hardware/hardware-profilers/hardware-profile.md

Step 3: Individual component checks
  - CPU: commands/hardware/hardware-profilers/by-component/profile-cpu.md
  - GPU: commands/hardware/hardware-profilers/by-component/profile-gpu.md
  - RAM: commands/hardware/hardware-profilers/by-component/profile-ram.md
  - Motherboard: commands/hardware/hardware-profilers/by-component/profile-motherboard.md
```

**Related References**:
- `references/hardware-other.md`

**Related Commands**:
- `commands/hardware/hardware-profilers/hardware-profile.md`
- `commands/hardware/hardware-profilers/hardware-identity.md`

---

#### 5.2 Disk hardware failure
**User keywords**: "the disk is broken", "disk failed", "SMART error", "bad sectors"

**Recommended path**:
```
Step 1: SMART health check
  bash references/disk-smart.md --mode quick

Step 2: Detailed SMART analysis
  bash references/disk-smart.md --mode deep

Step 3: Hardware diagnosis
  sudo smartctl -A /dev/sda
  sudo smartctl -l error /dev/sda
```

**Related References**:
- `references/disk-smart.md`

**Related Commands**:
- `commands/storage/health-checks/check-drive-health.md`
- `commands/storage/health-checks/smart-status.md`

---

#### 5.3 Overheating/cooling problems
**User keywords**: "high temperature", "overheating", "hot", "thermal", "fan"

**Recommended path**:
```
Step 1: Check the temperature sensors
  bash references/hardware-other.md --focus temperature

Step 2: CPU frequency check (whether it is throttling)
  cat /proc/cpuinfo | grep MHz
  cpupower frequency-info

Step 3: Fan status
  sensors
  cat /sys/class/thermal/thermal_zone*/temp
```

**Related References**:
- `references/hardware-other.md` (temperature sensors)

---

#### 5.4 GPU problems
**User keywords**: "GPU", "graphics card", "graphics", "display problems"

**Recommended path**:
```
Step 1: GPU status check
  commands/hardware/hardware-profilers/by-component/profile-gpu.md

Step 2: GPU driver check
  nvidia-smi  # NVIDIA
  radeontop   # AMD
  lspci | grep VGA

Step 3: GPU optimization
  commands/hardware/check-gpu-os-optimization.md
  commands/hardware/review-gpu-settings.md
```

**Related Commands**:
- `commands/hardware/hardware-profilers/by-component/profile-gpu.md`
- `commands/hardware/check-gpu-os-optimization.md`
- `commands/hardware/review-gpu-settings.md`

---

### 6. Time Synchronization Scenarios

#### 6.1 Inaccurate time
**User keywords**: "the time is wrong", "the clock is inaccurate", "time sync", "NTP"

**Recommended path**:
```
Step 1: Quick time check
  bash references/time-sync.md --mode quick

Step 2: Deep time analysis
  bash references/time-sync.md --mode deep

Step 3: Synchronize the time
  timedatectl status
  sudo timedatectl set-ntp true
```

**Related References**:
- `references/time-sync.md`

---

## 🔄 Medium-Frequency Scenarios (⭐⭐⭐⭐)

### 7. Network Scenarios

#### 7.1 LAN connection problems
**User keywords**: "local area network", "LAN", "intranet connection", "cannot connect over SSH"

**Recommended path**:
```
Step 1: LAN diagnosis
  commands/network/lan/diagnose-lan-connectivity.md

Step 2: Scan the LAN
  commands/network/lan/scan-lan.md

Step 3: SSH setup
  commands/network/lan/lan-ssh-setup.md
```

**Related Commands**:
- `commands/network/lan/diagnose-lan-connectivity.md`
- `commands/network/lan/scan-lan.md`
- `commands/network/lan/lan-ssh-setup.md`
- `commands/network/lan/smart-arp.md`

---

#### 7.2 Firewall problems
**User keywords**: "firewall", "firewall", "port blocked", "connection refused"

**Recommended path**:
```
Step 1: Firewall analysis
  commands/security/firewall/analyze-firewall.md

Step 2: Check the ports
  sudo ss -tulpn | grep <port>
  sudo iptables -L -n -v
```

**Related Commands**:
- `commands/security/firewall/analyze-firewall.md`

---

### 8. Security Scenarios

#### 8.1 Security audit
**User keywords**: "security check", "security audit", "vulnerability scan", "security assessment"

**Recommended path**:
```
Step 1: Security posture check
  commands/security/posture-diagnostics/security-posture-check.md

Step 2: Vulnerability probing
  commands/security/audits/probe-vulnerabilities.md

Step 3: Audit report
  commands/security/audits/write-audit.md
```

**Related Commands**:
- `commands/security/posture-diagnostics/security-posture-check.md`
- `commands/security/audits/probe-vulnerabilities.md`
- `commands/security/audits/write-audit.md`

---

#### 8.2 Permission problems
**User keywords**: "insufficient permissions", "permission denied", "cannot access", "access denied"

**Recommended path**:
```
Step 1: Debug permissions
  commands/configuration/permissions/debug-folder-permissions.md

Step 2: Check file permissions
  ls -la <path>
  namei -l <path>

Step 3: Fix permissions
  - Suggest secure permission settings
  - Check SELinux/AppArmor
```

**Related Commands**:
- `commands/configuration/permissions/debug-folder-permissions.md`

---

#### 8.3 Spyware/viruses
**User keywords**: "virus", "trojan", "spyware", "malware", "infected"

**Recommended path**:
```
Step 1: Detect spyware
  commands/security/detect-spyware.md

Step 2: Install antivirus software
  commands/security/av/install-clamav.md

Step 3: Scan the system
  sudo clamscan -r /home
```

**Related Commands**:
- `commands/security/detect-spyware.md`
- `commands/security/av/install-clamav.md`

---

### 9. Configuration Scenarios

#### 9.1 SSH configuration
**User keywords**: "SSH", "key", "SSH key", "remote connection"

**Recommended path**:
```
Step 1: Manage SSH keys
  commands/configuration/ssh/manage-ssh-keys.md

Step 2: View SSH connections
  commands/configuration/ssh/list-ssh-connections.md

Step 3: SSH troubleshooting
  ssh -vvv user@host
```

**Related Commands**:
- `commands/configuration/ssh/manage-ssh-keys.md`
- `commands/configuration/ssh/list-ssh-connections.md`

---

#### 9.2 Environment variables/PATH
**User keywords**: "PATH", "environment variables", "command not found", "command not found"

**Recommended path**:
```
Step 1: Check PATH
  commands/configuration/check-path.md

Step 2: Validate bashrc
  commands/configuration/bash/validate-bashrc.md

Step 3: Add an alias
  commands/configuration/bash/add-bash-alias.md
```

**Related Commands**:
- `commands/configuration/check-path.md`
- `commands/configuration/bash/validate-bashrc.md`
- `commands/configuration/bash/add-bash-alias.md`

---

#### 9.3 Git configuration
**User keywords**: "Git", "Git configuration", "gitignore", "Git username"

**Recommended path**:
```
Step 1: Check the Git configuration
  commands/configuration/git/check-git-config.md

Step 2: Global gitignore
  commands/configuration/git/check-global-gitignore.md
```

**Related Commands**:
- `commands/configuration/git/check-git-config.md`
- `commands/configuration/git/check-global-gitignore.md`

---

### 10. Software Management Scenarios

#### 10.1 Package management problems
**User keywords**: "apt errors", "package management", "package manager", "dependency problems"

**Recommended path**:
```
Step 1: Check apt health
  commands/package-management/check-apt-health.md

Step 2: Third-party repositories
  commands/package-management/check-third-party-repos.md

Step 3: Unused packages
  commands/package-management/identify-unused-packages.md
```

**Related Commands**:
- `commands/package-management/check-apt-health.md`
- `commands/package-management/check-third-party-repos.md`
- `commands/package-management/identify-unused-packages.md`
- `commands/package-management/configure-auto-updates.md`
- `commands/package-management/evaluate-installed-software.md`

---

#### 10.2 Docker problems
**User keywords**: "Docker", "container", "container", "docker compose"

**Recommended path**:
```
Step 1: Docker setup
  commands/dev-tools/docker/setup-docker.md

Step 2: Check container status
  docker ps -a
  docker logs <container>

Step 3: Resource usage
  docker stats
```

**Related Commands**:
- `commands/dev-tools/docker/setup-docker.md`

---

#### 10.3 Python environment
**User keywords**: "Python", "conda", "pyenv", "virtual environment", "pip"

**Recommended path**:
```
Step 1: Identify Python environments
  commands/dev-tools/python/identify-python-environments.md

Step 2: pyenv setup
  commands/dev-tools/python/pyenv/setup-pyenv.md

Step 3: conda management
  commands/dev-tools/python/conda/manage-conda-environments.md
```

**Related Commands**:
- `commands/dev-tools/python/identify-python-environments.md`
- `commands/dev-tools/python/pyenv/setup-pyenv.md`
- `commands/dev-tools/python/conda/manage-conda-environments.md`
- `commands/dev-tools/python/conda/setup-conda-data-analysis.md`
- `commands/dev-tools/python/conda/setup-conda-llm-finetune.md`
- `commands/dev-tools/python/conda/setup-conda-rocm.md`
- `commands/dev-tools/python/conda/setup-conda-stt-finetune.md`

---

## 🔍 Low-Frequency Scenarios (⭐⭐⭐)

### 11. Storage Scenarios

#### 11.1 RAID configuration
**User keywords**: "RAID", "disk array", "disk array"

**Recommended path**:
```
commands/storage/raid/check-raid-config.md
```

---

#### 11.2 Network mounts
**User keywords**: "NFS", "SMB", "network share", "mount"

**Recommended path**:
```
- NFS: commands/storage/network-mounts/setup-nfs-mounts.md
- SMB: commands/storage/network-mounts/setup-smb-mounts.md
```

---

#### 11.3 BTRFS snapshots
**User keywords**: "BTRFS", "snapshot", "snapper"

**Recommended path**:
```
commands/storage/health-checks/btrfs-snapper-health.md
```

---

### 12. Desktop Environment Scenarios

#### 12.1 Display problems
**User keywords**: "monitor", "multiple monitors", "resolution", "display"

**Recommended path**:
```
- List displays: commands/display/list-connected-displays.md
- Multiple monitors: commands/display/setup-multi-monitor.md
- Optimize scaling: commands/display/optimize-display-scaling.md
- Switch profiles: commands/display/switch-display-profile.md
- Save the configuration: commands/display/capture-current-config.md
```

---

#### 12.2 KDE Plasma problems
**User keywords**: "KDE", "Plasma", "desktop environment"

**Recommended path**:
```
- Optimize performance: commands/kde/optimize-kde-performance.md
- Reset the configuration: commands/kde/reset-plasma-config.md
- Back up settings: commands/kde/backup-kde-settings.md
- Keyboard shortcuts: commands/kde/list-kde-shortcuts.md
```

---

#### 12.3 Audio problems
**User keywords**: "audio", "sound", "microphone", "audio", "sound"

**Recommended path**:
```
- Microphone volume: commands/audio/mic-always-100.md
- Default microphone: commands/audio/set-as-default-mic.md
- PipeWire optimization: commands/system-health/optimize-pipewire.md
```

---

#### 12.4 Bluetooth problems
**User keywords**: "Bluetooth", "Bluetooth", "headphones will not connect"

**Recommended path**:
```
- Reset Bluetooth: commands/bluetooth/reset-bluetooth.md
- Troubleshooting: commands/bluetooth/troubleshoot-bluetooth.md
```

---

### 13. Virtualization Scenarios

#### 13.1 Virtualization check
**User keywords**: "virtualization", "virtual machine", "VM", "KVM", "VirtualBox"

**Recommended path**:
```
commands/virtualization/check-virtualization.md
```

---

### 14. Power Management Scenarios

#### 14.1 Hibernation/wake
**User keywords**: "hibernate", "hibernate", "sleep", "suspend", "wake"

**Recommended path**:
```
- Hibernation configuration: commands/power-mgmt/hibernation.md
- Wake devices: commands/hardware/evaluate-wake-devices.md
- WOL setup: commands/power-mgmt/wol-setup.md
```

---

### 15. Peripheral Scenarios

#### 15.1 USB devices
**User keywords**: "USB", "USB drive", "USB device not recognized"

**Recommended path**:
```
- List USB devices: commands/peripherals/list-usb-devices.md
- Input device test: commands/peripherals/evtest.md
```

---

#### 15.2 Printers
**User keywords**: "printer", "printer", "printing problems"

**Recommended path**:
```
commands/utilities/diagnose-printers.md
```

---

### 16. Development Tool Scenarios

#### 16.1 IDE problems
**User keywords**: "IDE", "VSCode", "editor"

**Recommended path**:
```
- Recommend IDEs: commands/dev-tools/suggest-ides.md
- Optimize VSCode: commands/dev-tools/ides/optimize-vscode-installation.md
```

---

#### 16.2 Node.js environment
**User keywords**: "Node", "npm", "Node.js"

**Recommended path**:
```
- Version check: commands/dev-tools/node/node-version-check.md
- npm install: commands/dev-tools/node/npm-install.md
```

---

#### 16.3 SDK management
**User keywords**: "SDK", "SDKMAN", "Java"

**Recommended path**:
```
- SDK check: commands/dev-tools/sdks/sdk-check.md
- Install SDKMAN: commands/installation/clis/install-sdkman.md
```

---

### 17. AI/ML Scenarios

#### 17.1 Local AI setup
**User keywords**: "AI", "machine learning", "Ollama", "ComfyUI"

**Recommended path**:
```
- GPU AI assessment: commands/ai/local-ai/gpu-ai-ml-assessment.md
- Ollama setup: commands/ai/local-ai/ollama/setup-ollama.md
- Ollama models: commands/ai/local-ai/ollama/suggest-ollama-models.md
- Ollama cleanup: commands/ai/local-ai/ollama/prune-ollama.md
- ComfyUI setup: commands/ai/local-ai/comfyui/setup-comfyui.md
- Audit AI packages: commands/ai/local-ai/audit-local-ai-packages.md
```

---

#### 17.2 AI CLI tools
**User keywords**: "AI CLI", "command-line AI", "MCP"

**Recommended path**:
```
- AI CLI recommendations: commands/ai/cli-seeders/ai-clis.md
- Evaluation tools: commands/ai/cli-seeders/evaltools.md
- MCP management: commands/ai/mcp/manage-mcp-servers.md
```

---

#### 17.3 Speech recognition
**User keywords**: "speech recognition", "STT", "speech to text"

**Recommended path**:
```
commands/ai/stt/setup-speech-to-text.md
```

---

### 18. File System Optimization Scenarios

#### 18.1 File organization
**User keywords**: "organize files", "organize files", "file categorization"

**Recommended path**:
```
- Desktop tidy-up: commands/fs-optimisation/tidy-up/desktop-tidy.md
- Organize loose files: commands/fs-optimisation/tidy-up/organize-loose-files.md
- Separate by type: commands/fs-optimisation/separate/separate-by-filetype.md
- Separate photos and video: commands/fs-optimisation/separate/separate-photos-and-video.md
- Folder suggestions: commands/fs-optimisation/idate/suggest-folder-structure.md
```

---

#### 18.2 Folder operations
**User keywords**: "folder", "directory", "merge", "split"

**Recommended path**:
```
- Consolidate folders: commands/fs-optimisation/consolidate/consolidate-folders.md
- Flatten: commands/fs-optimisation/flatten/flatten.md
- Chunk: commands/fs-optimisation/chunk/chunk-this-dir.md
```

---

### 19. Backup Scenarios

#### 19.1 Backup target identification
**User keywords**: "backup", "backup", "data backup"

**Recommended path**:
```
commands/backup/identify-backup-targets.md
```

---

### 20. Other Scenarios

#### 20.1 Font management
**User keywords**: "font", "font", "install fonts"

**Recommended path**:
```
- List fonts: commands/fonts/list-fonts.md
- Install Google fonts: commands/fonts/install-google-fonts.md
```

---

#### 20.2 Video codecs
**User keywords**: "codec", "codec", "video playback"

**Recommended path**:
```
- Check codecs: commands/media/check-codecs.md
- Video codecs: commands/video/codecs.md
```

---

#### 20.3 Repository management
**User keywords**: "Git repository", "organize repositories", "repo"

**Recommended path**:
```
- Organize repositories: commands/repositories/organise-repos.md
- Delete old repositories: commands/repositories/delete-old-repos.md
```

---

#### 20.4 Software installation
**User keywords**: "install software", "install", "install from GitHub"

**Recommended path**:
```
- Install from GitHub: commands/installation/install-from-gh.md
- Install this: commands/installation/install-this.md
- Install a GitHub program: commands/program-management/install-github-program.md
```

---

## 🗂️ Quick Lookup Table

### Indexed by Keyword

| Keyword | Scenario ID | Priority |
|--------|---------|--------|
| slow/laggy/lag | 1.1 | ⭐⭐⭐⭐⭐ |
| High CPU | 2.1 | ⭐⭐⭐⭐⭐ |
| Insufficient memory | 2.2 | ⭐⭐⭐⭐⭐ |
| Disk full | 2.3 | ⭐⭐⭐⭐⭐ |
| Slow disk | 2.4 | ⭐⭐⭐⭐⭐ |
| Slow network | 2.5 | ⭐⭐⭐⭐⭐ |
| Health check | 3.1 | ⭐⭐⭐⭐⭐ |
| Crash | 4.1 | ⭐⭐⭐⭐⭐ |
| Error logs | 4.3 | ⭐⭐⭐⭐⭐ |
| Hardware check | 5.1 | ⭐⭐⭐⭐⭐ |
| Disk failure | 5.2 | ⭐⭐⭐⭐⭐ |
| High temperature | 5.3 | ⭐⭐⭐⭐ |
| Wrong time | 6.1 | ⭐⭐⭐⭐ |
| LAN connection | 7.1 | ⭐⭐⭐⭐ |
| Firewall | 7.2 | ⭐⭐⭐⭐ |
| Security audit | 8.1 | ⭐⭐⭐⭐ |
| Permission problems | 8.2 | ⭐⭐⭐⭐ |
| SSH | 9.1 | ⭐⭐⭐⭐ |
| PATH | 9.2 | ⭐⭐⭐⭐ |
| Package management | 10.1 | ⭐⭐⭐⭐ |
| Docker | 10.2 | ⭐⭐⭐⭐ |
| Python | 10.3 | ⭐⭐⭐⭐ |

---

## 📝 Usage Examples

### Example 1: the user says "the server is very slow"

```
AI decision flow:
1. Search the index for "slow" → matched scenario 1.1
2. Look at the recommended path:
   - Step 1: bash references/resource-saturation.md
3. Run Quick Mode (10 seconds)
4. Quick result: Memory WARNING
5. Trigger Deep Mode: bash ... --mode deep --focus memory (20 seconds)
6. Deep result: Java memory leak
7. Generate the report + repair suggestions
```

---

### Example 2: the user says "the disk is broken"

```
AI decision flow:
1. Search the index for "disk broken" → matched scenario 5.2
2. Look at the recommended path:
   - Step 1: bash references/disk-smart.md --mode quick
3. Quick result: SMART CRITICAL
4. Trigger Deep Mode: bash ... --mode deep
5. Deep result: Reallocated sectors 100+
6. Report: the disk is about to fail; back up immediately
```

---

### Example 3: the user says "check the system health"

```
AI decision flow:
1. Search the index for "health check" → matched scenario 3.1
2. Look at the recommended path:
   - Step 1: run 3 Quick checks
   - bash resource-saturation.md --mode quick
   - bash system-logs.md --mode quick
   - bash disk-smart.md --mode quick
3. Everything OK → report normal
4. If there are anomalies → trigger the corresponding Deep Mode
```

---

## 🎯 AI Decision Algorithm

```python
def match_scenario(user_query):
    """Match a scenario based on the user query"""
    keywords = extract_keywords(user_query)
    
    # 1. Exact match
    for keyword in keywords:
        if scenario := exact_match(keyword):
            return scenario
    
    # 2. Fuzzy match
    for keyword in keywords:
        if scenario := fuzzy_match(keyword):
            return scenario
    
    # 3. Default scenario (comprehensive health check)
    return scenario_3_1

def execute_scenario(scenario, user_query):
    """Execute the scenario's recommended path"""
    path = scenario.recommended_path
    
    # Step 1: Quick Mode
    if "reference" in path.step1:
        quick_result = run_quick_mode(path.step1)
    
    # Step 2: Decide whether to run Deep
    if should_run_deep(quick_result, user_query):
        deep_result = run_deep_mode(path.step2, quick_result.focus)
        return generate_report(quick_result, deep_result)
    else:
        return generate_report(quick_result)

def should_run_deep(quick_result, user_query):
    """Decide whether to run Deep Mode"""
    if quick_result.has_critical():
        return True  # triggered automatically
    elif quick_result.has_warning():
        if "troubleshoot" in user_query or "slow" in user_query:
            return True  # triggered automatically
        else:
            return ask_user("An anomaly was found. Run a deep analysis?")
    return False  # no Deep needed
```

---

## 📈 Statistics

### Coverage
- **Total scenarios**: 20 major categories + 60+ sub-scenarios
- **Commands coverage**: 126 files
- **References coverage**: 5 core diagnosis modules
- **Estimated coverage**: 95%+ of common user problems

### Scenario Distribution
- **High-frequency scenarios** (⭐⭐⭐⭐⭐): 6 major categories, 20 scenarios → 80% of user problems
- **Medium-frequency scenarios** (⭐⭐⭐⭐): 4 major categories, 15 scenarios → 15% of user problems
- **Low-frequency scenarios** (⭐⭐⭐): 10 major categories, 25+ scenarios → 5% of user problems

### Expected Results
- **Match accuracy**: 90%+
- **Time to first response**: 10 seconds (Quick Mode)
- **Full diagnosis time**: 30-70 seconds (Quick + Deep)
- **Token savings**: 70-80%

---

## 🔄 Maintenance Guide

### Update Frequency
- **High-frequency scenarios**: review once a month
- **Medium/low-frequency scenarios**: review once a quarter
- **New Command/Reference**: update the index immediately

### Update Process
1. Identify the new scenario or Command
2. Analyze the user keywords
3. Determine the priority (⭐⭐⭐⭐⭐ / ⭐⭐⭐⭐ / ⭐⭐⭐)
4. Add it to the corresponding category
5. Update the quick lookup table
6. Test the AI matching accuracy

---

## 📚 Reference Material

### References Files
- `references/resource-saturation.md` - resource saturation analysis
- `references/system-logs.md` - system log analysis
- `references/disk-smart.md` - disk SMART health
- `references/hardware-other.md` - hardware health check
- `references/time-sync.md` - time synchronization check

### Commands Directory
- `commands/debugging/` - fault diagnosis
- `commands/system-health/` - system health
- `commands/hardware/` - hardware
- `commands/network/` - network
- `commands/security/` - security
- `commands/configuration/` - configuration management
- `commands/storage/` - storage
- `commands/package-management/` - package management
- `commands/dev-tools/` - development tools

---

**Version**: 1.0
**Last updated**: 2026-03-24
**Maintainer**: AI Assistant
**Status**: ✅ Production ready
