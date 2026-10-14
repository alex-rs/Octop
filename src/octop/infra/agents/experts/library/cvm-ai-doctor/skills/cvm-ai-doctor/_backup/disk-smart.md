---
name: disk-smart-check
description: Monitor disk health through SMART attributes - predict failures before data loss
category: standalone-checks
---

# Disk SMART Status Check

**Purpose**: Monitor disk health through SMART (Self-Monitoring, Analysis and Reporting Technology) to predict failures before data loss.

**Why critical**: Disks fail predictably - SMART attributes show warning signs weeks before catastrophic failure.

**Research**: Google/Backblaze studies show SMART predicts 56-70% of disk failures 7-14 days in advance.

---

## 🎯 AI Usage Guide

### Quick/Deep Workflow

```mermaid
User Question → Quick Mode (10s) → Analyze → Deep Mode (20-30s, if warnings)
```

**When to use each mode**:

| Mode | Duration | Purpose | When to Use |
|------|----------|---------|-------------|
| **Quick** | 10s | Check overall health status only | Health check, "check the disk", daily routine |
| **Deep** | 20-30s | Detailed SMART attributes + predictive analysis | Quick shows warnings, troubleshooting |

**Decision Logic**:
```yaml
Quick Mode Results:
  - All PASSED → Stop, report healthy
  - Any FAILED → Deep Mode immediately (data loss risk)
  - Any unknown/unavailable → Deep Mode to verify
  
Deep Mode Focus:
  - Parse critical SMART attributes (ID 5, 197, 198)
  - Check temperature and power-on hours
  - Calculate failure probability
  - Generate replacement timeline
```

**Output Format**:

```yaml
# Quick Mode
status: PASSED | FAILED | UNKNOWN
disks:
  - device: /dev/sda
    health: PASSED | FAILED
    status: OK | WARNING | CRITICAL
summary: "Overall disk health"

# Deep Mode
disk: /dev/sda
health_status: PASSED | FAILED
critical_attributes:
  reallocated_sectors: {value: N, threshold: 0, status: OK/WARNING}
  pending_sectors: {value: N, threshold: 0, status: CRITICAL if >0}
  uncorrectable_errors: {value: N, threshold: 0, status: CRITICAL if >0}
temperature: {current: N°C, threshold: 60°C}
power_on_hours: N
failure_probability: low | medium | high | imminent
recommendation: "Action required"
```

---

## ⚡ Quick Mode (10s)

**Purpose**: Overall health status check - PASSED or FAILED

### Check All Disks Health Status

```bash
# Linux (requires smartmontools: apt-get install smartmontools)
# Detect all physical disks
DISKS=$(lsblk -nd -o NAME,TYPE 2>/dev/null | awk '$2=="disk" {print "/dev/"$1}')

echo "=== Quick Mode: Disk SMART Health ==="
for disk in $DISKS; do
  if command -v smartctl &>/dev/null; then
    HEALTH=$(sudo smartctl -H "$disk" 2>/dev/null | awk '/SMART overall-health/ {print $NF}')
    if [ "$HEALTH" = "PASSED" ]; then
      echo "$disk: PASSED [OK]"
    elif [ "$HEALTH" = "FAILED" ]; then
      echo "$disk: FAILED [CRITICAL] - BACKUP DATA IMMEDIATELY"
    else
      echo "$disk: UNKNOWN [CHECK] - SMART may not be supported"
    fi
  else
    echo "smartctl not installed - run: apt-get install smartmontools"
    break
  fi
done
```

```bash
# macOS
for disk in $(diskutil list | awk '/^\/dev\/disk[0-9]/ {print $1}'); do
  SMART=$(diskutil info "$disk" 2>/dev/null | grep "SMART Status" | awk '{print $3}')
  echo "$disk: $SMART"
done
```

```powershell
# Windows PowerShell
Get-PhysicalDisk | ForEach-Object {
  $disk = $_
  $health = if ($disk.HealthStatus -eq "Healthy") { "PASSED" } else { "FAILED" }
  Write-Host "$($disk.DeviceId): $health [$($disk.HealthStatus)]"
}
```

**Thresholds**:
```yaml
CRITICAL: FAILED (immediate action required)
WARNING: UNKNOWN (needs verification)
OK: PASSED
```

**AI Instructions for Quick Mode**:
1. Execute commands for all detected disks
2. Parse health status for each disk
3. Decision logic:
   - All PASSED → Report healthy, stop
   - Any FAILED → Trigger Deep Mode immediately
   - Any UNKNOWN → Trigger Deep Mode to verify

---

## 🔬 Deep Mode (20-30s)

**Purpose**: Detailed SMART attribute analysis + failure prediction

**When**: Quick shows FAILED/UNKNOWN, or user requests detailed analysis

---

### Deep Mode: Complete SMART Analysis

**Run for each disk**:

```bash
#!/bin/bash
# Deep Mode: Detailed SMART Analysis
DISK="$1"  # e.g., /dev/sda

if [ -z "$DISK" ]; then
  echo "Usage: $0 /dev/sdX"
  exit 1
fi

echo "========================================="
echo " SMART Deep Analysis: $DISK"
echo "========================================="

# 1. Overall Health
echo -e "\n[1/6] Overall Health Status"
HEALTH=$(sudo smartctl -H "$DISK" 2>/dev/null | awk '/SMART overall-health/ {print $NF}')
echo "Status: $HEALTH"

if [ "$HEALTH" = "FAILED" ]; then
  echo "🔴 CRITICAL - Disk is FAILING"
  echo "ACTION: Backup data immediately and schedule replacement"
elif [ "$HEALTH" = "PASSED" ]; then
  echo "✅ Health check passed"
else
  echo "⚠️  Unable to determine (SMART may not be enabled)"
fi

# 2. Critical SMART Attributes
echo -e "\n[2/6] Critical SMART Attributes"
SMART_DATA=$(sudo smartctl -A "$DISK" 2>/dev/null)

# Reallocated Sectors (ID 5)
REALLOCATED=$(echo "$SMART_DATA" | awk '/Reallocated_Sector/ {print $10}')
if [ -n "$REALLOCATED" ]; then
  echo "Reallocated Sectors (ID 5): $REALLOCATED"
  if [ "$REALLOCATED" -gt 0 ]; then
    echo "  ⚠️  WARNING - Disk has remapped bad blocks"
    echo "  Impact: Disk is degrading, monitor closely"
  else
    echo "  ✅ OK"
  fi
fi

# Pending Sectors (ID 197)
PENDING=$(echo "$SMART_DATA" | awk '/Current_Pending_Sector/ {print $10}')
if [ -n "$PENDING" ]; then
  echo "Pending Sectors (ID 197): $PENDING"
  if [ "$PENDING" -gt 0 ]; then
    echo "  🔴 CRITICAL - Unstable sectors waiting for reallocation"
    echo "  Impact: Data may be unreadable, imminent failure risk"
    echo "  Action: Backup immediately, replace disk"
  else
    echo "  ✅ OK"
  fi
fi

# Uncorrectable Errors (ID 198)
UNCORRECTABLE=$(echo "$SMART_DATA" | awk '/Offline_Uncorrectable/ {print $10}')
if [ -n "$UNCORRECTABLE" ]; then
  echo "Uncorrectable Errors (ID 198): $UNCORRECTABLE"
  if [ "$UNCORRECTABLE" -gt 0 ]; then
    echo "  🔴 CRITICAL - Unreadable sectors detected"
    echo "  Impact: Data loss has occurred"
    echo "  Action: Replace disk immediately"
  else
    echo "  ✅ OK"
  fi
fi

# 3. Temperature
echo -e "\n[3/6] Disk Temperature"
TEMP=$(echo "$SMART_DATA" | awk '/Temperature_Celsius/ {print $10}' | head -1)
if [ -n "$TEMP" ]; then
  echo "Current: ${TEMP}°C"
  if [ "$TEMP" -gt 60 ]; then
    echo "  🔴 CRITICAL - Disk overheating (>60°C)"
    echo "  Impact: Accelerated wear, increased failure risk"
    echo "  Action: Improve cooling, check airflow"
  elif [ "$TEMP" -gt 50 ]; then
    echo "  ⚠️  WARNING - Temperature elevated (>50°C)"
  else
    echo "  ✅ Normal operating temperature"
  fi
else
  echo "  ℹ️  Temperature data not available"
fi

# 4. Power-On Hours
echo -e "\n[4/6] Disk Age"
HOURS=$(echo "$SMART_DATA" | awk '/Power_On_Hours/ {print $10}')
if [ -n "$HOURS" ]; then
  YEARS=$(echo "scale=1; $HOURS / 8760" | bc)
  echo "Power-On Time: $HOURS hours (${YEARS} years)"
  
  if [ "$HOURS" -gt 43800 ]; then
    echo "  ⚠️  WARNING - Disk is old (>5 years)"
    echo "  Recommendation: Plan for replacement"
  elif [ "$HOURS" -gt 26280 ]; then
    echo "  ℹ️  Disk age: 3-5 years (monitor closely)"
  else
    echo "  ✅ Disk age acceptable"
  fi
else
  echo "  ℹ️  Age data not available"
fi

# 5. Read/Write Error Rates
echo -e "\n[5/6] Error Rates"
READ_ERRORS=$(echo "$SMART_DATA" | awk '/Raw_Read_Error_Rate/ {print $10}')
WRITE_ERRORS=$(echo "$SMART_DATA" | awk '/Reported_Uncorrect/ {print $10}')
COMMAND_TIMEOUT=$(echo "$SMART_DATA" | awk '/Command_Timeout/ {print $10}')

[ -n "$READ_ERRORS" ] && echo "Read Errors: $READ_ERRORS"
[ -n "$WRITE_ERRORS" ] && echo "Write Errors: $WRITE_ERRORS"
[ -n "$COMMAND_TIMEOUT" ] && echo "Command Timeouts: $COMMAND_TIMEOUT"

if [ -n "$COMMAND_TIMEOUT" ] && [ "$COMMAND_TIMEOUT" -gt 0 ]; then
  echo "  ⚠️  WARNING - Disk not responding in time"
fi

# 6. Self-Test Results
echo -e "\n[6/6] Self-Test Results"
SELF_TEST=$(sudo smartctl -l selftest "$DISK" 2>/dev/null | grep "# 1" | head -1)
if [ -n "$SELF_TEST" ]; then
  echo "$SELF_TEST"
else
  echo "  ℹ️  No self-test results (run: smartctl -t short $DISK)"
fi

echo ""
echo "========================================="
echo " Failure Probability Assessment"
echo "========================================="

# Calculate failure probability
FAILURE_SCORE=0
[ -n "$REALLOCATED" ] && [ "$REALLOCATED" -gt 0 ] && ((FAILURE_SCORE+=2))
[ -n "$PENDING" ] && [ "$PENDING" -gt 0 ] && ((FAILURE_SCORE+=5))
[ -n "$UNCORRECTABLE" ] && [ "$UNCORRECTABLE" -gt 0 ] && ((FAILURE_SCORE+=5))
[ -n "$TEMP" ] && [ "$TEMP" -gt 60 ] && ((FAILURE_SCORE+=2))
[ -n "$HOURS" ] && [ "$HOURS" -gt 43800 ] && ((FAILURE_SCORE+=1))

if [ "$FAILURE_SCORE" -ge 5 ]; then
  echo "Risk: IMMINENT FAILURE (score: $FAILURE_SCORE/15)"
  echo "Timeline: Days to weeks"
  echo "Action: Backup and replace IMMEDIATELY"
elif [ "$FAILURE_SCORE" -ge 3 ]; then
  echo "Risk: HIGH (score: $FAILURE_SCORE/15)"
  echo "Timeline: Weeks to months"
  echo "Action: Schedule replacement within 1 month"
elif [ "$FAILURE_SCORE" -ge 1 ]; then
  echo "Risk: MEDIUM (score: $FAILURE_SCORE/15)"
  echo "Timeline: Months"
  echo "Action: Monitor weekly, plan replacement"
else
  echo "Risk: LOW (score: $FAILURE_SCORE/15)"
  echo "Status: Disk appears healthy"
  echo "Action: Continue normal monitoring"
fi
```

**AI Instructions for Deep Mode**:
1. Run the script for each disk flagged in Quick Mode
2. Parse output to extract:
   - Critical attribute values (ID 5, 197, 198)
   - Temperature
   - Power-on hours
   - Failure score
3. Apply Root Cause Inference patterns (see below)
4. Generate actionable report with timeline

---

### Root Cause Inference Patterns

**Pattern 1: Imminent Failure**
```yaml
Evidence:
  - Pending Sectors > 0 OR Uncorrectable Errors > 0
  - Failure score ≥ 5
Root Cause: "Disk is actively failing, data loss imminent"
Timeline: "Days to weeks"
Recommendation:
  - "🔴 CRITICAL - Backup all data IMMEDIATELY"
  - "Order replacement disk today"
  - "Do not write new data to this disk"
  - "Monitor continuously: smartctl -a <disk>"
```

**Pattern 2: Early Degradation**
```yaml
Evidence:
  - Reallocated Sectors 1-100
  - Pending Sectors = 0
  - Temperature normal
Root Cause: "Disk has remapped bad sectors, early stage degradation"
Timeline: "Weeks to months"
Recommendation:
  - "⚠️  WARNING - Disk is degrading"
  - "Backup important data"
  - "Schedule replacement within 1-3 months"
  - "Monitor weekly: smartctl -H <disk>"
```

**Pattern 3: Overheating**
```yaml
Evidence:
  - Temperature > 60°C
  - No bad sectors yet
Root Cause: "Disk overheating, accelerated wear"
Timeline: "Reduced lifespan, unpredictable"
Recommendation:
  - "Improve cooling immediately"
  - "Check server airflow and fan status"
  - "Clean dust from vents"
  - "Monitor temperature: watch -n 60 'smartctl -A <disk> | grep Temperature'"
  - "If temp persists >60°C, replace disk"
```

**Pattern 4: Old Age**
```yaml
Evidence:
  - Power-on hours > 43800 (5 years)
  - No current errors
Root Cause: "Disk is old, increased failure risk"
Timeline: "Unknown, but risk increases with age"
Recommendation:
  - "Plan replacement within 6-12 months"
  - "Ensure backups are current"
  - "Monitor monthly for new errors"
  - "Consider proactive replacement if critical data"
```

**Pattern 5: Healthy Disk**
```yaml
Evidence:
  - Health: PASSED
  - All critical attributes = 0
  - Temperature < 50°C
  - Age < 5 years
Root Cause: "Disk is healthy"
Timeline: "Normal lifespan expected"
Recommendation:
  - "✅ No action required"
  - "Continue quarterly SMART checks"
  - "Maintain regular backups"
```

---

## 💡 Complete Usage Examples

### Example 1: User Reports "the disk may have a problem"

**Step 1: Quick Mode**
```bash
# Output:
/dev/sda: PASSED [OK]
/dev/sdb: FAILED [CRITICAL] - BACKUP DATA IMMEDIATELY
```

**AI Decision**: /dev/sdb FAILED → Deep Mode immediately

**Step 2: Deep Mode on /dev/sdb**
```
Overall Health: FAILED
Reallocated Sectors: 5
Pending Sectors: 12
Uncorrectable Errors: 3
Temperature: 45°C
Power-On Hours: 28000 (3.2 years)
Failure Score: 12/15
Risk: IMMINENT FAILURE
```

**AI Inference**: Pattern 1 (Imminent Failure)

**Final Report**:
```
🔴 URGENT: /dev/sdb disk is about to fail

Detection results:
- Health status: FAILED
- Pending reallocation sectors: 12 (severe)
- Uncorrectable errors: 3 (data already lost)
- Reallocated sectors: 5

Failure probability: extremely high (score 12/15)
Estimated time: within days to weeks

Immediate action:
1. 🔴 Back up all data immediately (extremely high risk of data loss)
2. 🔴 Order a replacement disk today
3. 🔴 Do not write new data to this disk
4. Monitor continuously: smartctl -a /dev/sdb

Technical details:
- 12 sectors are in an unstable state
- Data in 3 sectors is already unreadable
- The disk hardware is degrading rapidly
```

---

### Example 2: User Asks "check disk health"

**Step 1: Quick Mode**
```
/dev/sda: PASSED [OK]
/dev/sdb: PASSED [OK]
```

**AI Decision**: All PASSED → Could stop, but user may want details

**Optional Step 2: Quick Deep Summary** (10s extra)
```bash
# Just check critical attributes, not full analysis
for disk in /dev/sda /dev/sdb; do
  REALLOCATED=$(sudo smartctl -A "$disk" | awk '/Reallocated/ {print $10}')
  TEMP=$(sudo smartctl -A "$disk" | awk '/Temperature/ {print $10}' | head -1)
  echo "$disk: Reallocated=$REALLOCATED, Temp=${TEMP}°C"
done

# Output:
/dev/sda: Reallocated=0, Temp=42°C
/dev/sdb: Reallocated=0, Temp=38°C
```

**Final Report**:
```
Disk health check - all normal ✅

/dev/sda:
- Health status: PASSED
- Bad sectors: 0
- Temperature: 42°C (normal)

/dev/sdb:
- Health status: PASSED
- Bad sectors: 0
- Temperature: 38°C (normal)

Conclusion: all disks are healthy, no action required
Recommendation: continue periodic checks (quarterly)
```

---

### Example 3: User Reports "the disk temperature is high"

**Step 1: Quick Mode**
```
/dev/sda: PASSED [OK]
```

**AI Note**: Health PASSED but user mentioned temperature → Skip full Deep, focus on temperature

**Step 2: Temperature-Focused Check**
```bash
sudo smartctl -A /dev/sda | grep Temperature
# Output: Temperature: 68°C
```

**AI Inference**: Pattern 3 (Overheating)

**Final Report**:
```
🔴 Disk overheating warning

Current status:
- Health status: PASSED (hardware is not damaged yet)
- Current temperature: 68°C (severely overheated)
- Normal range: < 50°C

Root cause: poor heat dissipation, disk temperature is out of range

Impact:
- Accelerates disk aging
- Increases failure risk
- May cause data corruption

Immediate action:
1. Check whether the server fans are running normally
2. Clean dust from the chassis
3. Check the airflow inside the chassis
4. If the temperature stays >60°C, consider adding cooling fans
5. Monitor the temperature: watch -n 60 'smartctl -A /dev/sda | grep Temperature'

Goal: bring the temperature below 50°C
```

---

## 🎯 Key Takeaways

### SMART Predicts Failure
- **Google study**: SMART attributes predict 56% of disk failures
- **Backblaze**: Reallocated sectors (#1 predictor), pending sectors (#2)
- **Lead time**: 7-14 days advance warning

### Critical Attributes Priority
1. **Pending Sectors (197)** → IMMINENT failure (days)
2. **Uncorrectable Errors (198)** → Data ALREADY lost
3. **Reallocated Sectors (5)** → Early degradation (weeks/months)
4. **Temperature (194)** → Accelerated wear
5. **Power-On Hours** → Age risk factor

### When to Replace
- **Immediately**: Pending sectors > 0 OR Uncorrectable > 0
- **1 month**: Reallocated sectors > 100
- **6 months**: Temperature consistently > 60°C
- **12 months**: Age > 5 years

### Monitoring Frequency
- **Critical disks**: Daily
- **Degrading disks**: Weekly
- **Healthy disks**: Quarterly

---

**Integration**: This check complements `system-logs.md` (disk I/O errors) and `hardware-other.md` (RAID status).

**Tools Required**:
- Linux: `smartmontools` (apt-get install smartmontools)
- macOS: Built-in `diskutil`
- Windows: Built-in `Get-PhysicalDisk`
