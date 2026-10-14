#!/bin/bash
# CVM AI Doctor scheduled patrol setup script (LightClaw Cron)

set -e

echo "🚀 Configuring the CVM AI Doctor scheduled patrol (LightClaw Cron)..."
echo ""

# Check whether jq is installed
if ! command -v jq &> /dev/null; then
    echo "❌ Error: jq must be installed"
    echo "   macOS: brew install jq"
    echo "   Ubuntu: sudo apt install jq"
    exit 1
fi

# Check whether LightClaw is available
if ! command -v lightclaw &> /dev/null; then
    echo "❌ Error: the lightclaw command is not available"
    echo "   Make sure LightClaw is installed and its PATH is configured"
    exit 1
fi

# Check whether the LightClaw service is running
if ! curl -s http://127.0.0.1:8088/health > /dev/null 2>&1; then
    echo "⚠️  Warning: the LightClaw service is not running"
    echo "   The job will be saved to jobs.json but will not take effect immediately"
    echo "   Please run: lightclaw server start"
    echo ""
    read -p "Continue with the setup? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "📋 Choose the patrol frequency:"
echo "  1. Every minute (high frequency, cost ~$4/day)"
echo "  2. Every 5 minutes (recommended, cost ~$0.9/day)"
echo "  3. Every 15 minutes (low frequency, cost ~$0.3/day)"
echo "  4. Custom"
echo ""
read -p "Choose [1-4]: " -n 1 -r choice
echo ""

case $choice in
    1)
        CRON_EXPR="*/1 * * * *"
        FREQ_DESC="every minute"
        ;;
    2)
        CRON_EXPR="*/5 * * * *"
        FREQ_DESC="every 5 minutes"
        ;;
    3)
        CRON_EXPR="*/15 * * * *"
        FREQ_DESC="every 15 minutes"
        ;;
    4)
        echo "Enter the cron expression (e.g. */10 * * * * means every 10 minutes):"
        read -r CRON_EXPR
        FREQ_DESC="custom ($CRON_EXPR)"
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "📋 Choose the output channel:"
echo "  1. dashboard (Dashboard panel)"
echo "  2. dingtalk (DingTalk)"
echo "  3. qq (QQ)"
echo ""
read -p "Choose [1-3]: " -n 1 -r channel_choice
echo ""

case $channel_choice in
    1) CHANNEL="dashboard" ;;
    2) CHANNEL="dingtalk" ;;
    3) CHANNEL="qq" ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "📋 Configuration summary:"
echo "  Frequency: $FREQ_DESC"
echo "  Cron expression: $CRON_EXPR"
echo "  Output channel: $CHANNEL"
echo ""
read -p "Confirm the configuration? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cancelled"
    exit 1
fi

echo ""
echo "🔧 Creating the scheduled jobs..."

# 1. Quick check job
echo "  → Creating the quick check job..."
JOB_ID_QUICK=$(lightclaw cron create \
  --type agent \
  --name "CVM Quick Check - $FREQ_DESC" \
  --cron "$CRON_EXPR" \
  --channel "$CHANNEL" \
  --timezone "Asia/Shanghai" \
  --text "Use the CVM AI Doctor skill to run a quick check. If all metrics are normal, return only 'System OK ✅'; if warnings or serious issues are found, return the detailed diagnosis and repair suggestions. Focus on: CPU/memory/disk/network status." \
  --mode final 2>/dev/null | jq -r '.id')

if [ -z "$JOB_ID_QUICK" ]; then
    echo "❌ Failed to create the quick check job"
    exit 1
fi

echo "  ✅ Quick check job created: $JOB_ID_QUICK"

# 2. Deep analysis job (hourly)
echo "  → Creating the deep analysis job (hourly)..."
JOB_ID_DEEP=$(lightclaw cron create \
  --type agent \
  --name "CVM Deep Analysis - Hourly" \
  --cron "0 * * * *" \
  --channel "$CHANNEL" \
  --timezone "Asia/Shanghai" \
  --text "Use the CVM AI Doctor skill to run a deep diagnosis. Analyze system performance bottlenecks, check the system logs for errors and warnings, and provide optimization advice. Key focus: resource saturation, log anomalies, process status." \
  --mode final 2>/dev/null | jq -r '.id')

if [ -z "$JOB_ID_DEEP" ]; then
    echo "❌ Failed to create the deep analysis job"
    exit 1
fi

echo "  ✅ Deep analysis job created: $JOB_ID_DEEP"

# 3. Daily full health check (3 AM)
echo "  → Creating the daily health check job (3 AM)..."
JOB_ID_DAILY=$(lightclaw cron create \
  --type agent \
  --name "CVM Daily Health Check" \
  --cron "0 3 * * *" \
  --channel "$CHANNEL" \
  --timezone "Asia/Shanghai" \
  --text "Use the CVM AI Doctor skill to run a full health check. The checks include: resource saturation, system log review, disk SMART health, hardware health status, and NTP time synchronization. Generate a detailed health report including historical trends and preventive recommendations." \
  --mode final 2>/dev/null | jq -r '.id')

if [ -z "$JOB_ID_DAILY" ]; then
    echo "❌ Failed to create the daily health check job"
    exit 1
fi

echo "  ✅ Daily health check job created: $JOB_ID_DAILY"

echo ""
echo "✅ All jobs created!"
echo ""

# Test run
echo "🧪 Test-running the quick check job..."
if curl -s http://127.0.0.1:8088/health > /dev/null 2>&1; then
    lightclaw cron run "$JOB_ID_QUICK" > /dev/null 2>&1 && echo "  ✅ Test run succeeded" || echo "  ⚠️  Test run failed (the job may need some time)"
else
    echo "  ⚠️  The LightClaw service is not running; skipping the test"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Job list"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
lightclaw cron list | jq -r '.[] | "  \(.id)  [\(.enabled | if . then "✓" else "✗" end)]  \(.name)  (\(.schedule.cron))"'

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📚 Management commands"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  List all jobs:      lightclaw cron list"
echo "  Show job details:   lightclaw cron get <JOB_ID>"
echo "  Pause a job:        lightclaw cron pause <JOB_ID>"
echo "  Resume a job:       lightclaw cron resume <JOB_ID>"
echo "  Delete a job:       lightclaw cron delete <JOB_ID>"
echo "  Run manually:       lightclaw cron run <JOB_ID>"
echo ""
echo "  Quick check job ID:    $JOB_ID_QUICK"
echo "  Deep analysis job ID:  $JOB_ID_DEEP"
echo "  Daily health job ID:   $JOB_ID_DAILY"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📁 Related files"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Job config:    ~/.lightclaw/jobs.json"
echo "  Run log:       ~/.lightclaw/logs/cron.log"
echo "  Agent log:     ~/.lightclaw/logs/agent.log"
echo ""
echo "🎉 Configuration complete! The scheduled patrol has started."
