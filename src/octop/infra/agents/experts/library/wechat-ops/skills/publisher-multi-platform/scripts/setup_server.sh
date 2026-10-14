#!/bin/bash
# Wenyan Server one-click deployment script
# Run this script on your cloud server to deploy the wenyan server
#
# Usage:
#   curl -fsSL <script_url> | bash
#   # or
#   bash setup_server.sh

set -e

echo "╔══════════════════════════════════════════════════════╗"
echo "║   Wenyan Server One-Click Deploy                     ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PORT=${WENYAN_PORT:-7788}
LOG_FILE="/var/log/wenyan-server.log"

# Step 1: Check Node.js
echo -e "${YELLOW}[1/4] Checking Node.js...${NC}"
if command -v node &>/dev/null; then
    NODE_VER=$(node --version)
    echo -e "  ${GREEN}✅ Node.js $NODE_VER is installed${NC}"
else
    echo "  ⏳ Installing Node.js..."
    if command -v apt-get &>/dev/null; then
        curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
        apt-get install -y nodejs
    elif command -v yum &>/dev/null; then
        curl -fsSL https://rpm.nodesource.com/setup_20.x | bash -
        yum install -y nodejs
    else
        echo -e "  ${RED}❌ Cannot install Node.js automatically, please install it manually${NC}"
        exit 1
    fi
    echo -e "  ${GREEN}✅ Node.js $(node --version) installed successfully${NC}"
fi

# Step 2: Install wenyan-cli
echo -e "${YELLOW}[2/4] Installing wenyan-cli...${NC}"
if command -v wenyan &>/dev/null; then
    WENYAN_VER=$(wenyan --version 2>/dev/null || echo "unknown")
    echo -e "  ${GREEN}✅ wenyan-cli $WENYAN_VER is installed${NC}"
else
    npm install -g @wenyan-md/cli
    echo -e "  ${GREEN}✅ wenyan-cli installed successfully${NC}"
fi

# Step 3: Check env vars
echo -e "${YELLOW}[3/4] Checking environment variables...${NC}"
if [ -z "$WECHAT_APP_ID" ]; then
    echo -e "  ${RED}❌ WECHAT_APP_ID is not set${NC}"
    echo "     Please set: export WECHAT_APP_ID='your_app_id'"
    MISSING_ENV=true
fi
if [ -z "$WECHAT_APP_SECRET" ]; then
    echo -e "  ${RED}❌ WECHAT_APP_SECRET is not set${NC}"
    echo "     Please set: export WECHAT_APP_SECRET='your_app_secret'"
    MISSING_ENV=true
fi
if [ "$MISSING_ENV" = true ]; then
    echo ""
    echo "  Re-run this script after setting the environment variables."
    echo "  Persisting them in /etc/environment or ~/.bashrc is recommended."
    exit 1
fi
echo -e "  ${GREEN}✅ WECHAT_APP_ID: ${WECHAT_APP_ID:0:4}...${NC}"
echo -e "  ${GREEN}✅ WECHAT_APP_SECRET: ***set***${NC}"

# Step 4: Start server
echo -e "${YELLOW}[4/4] Starting wenyan server (port $PORT)...${NC}"

# Kill existing
pkill -f "wenyan serve" 2>/dev/null || true
sleep 1

# Start
nohup wenyan serve --port "$PORT" >> "$LOG_FILE" 2>&1 &
disown
sleep 2

# Verify
if pgrep -f "wenyan serve" > /dev/null; then
    PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || echo "unknown")
    echo -e "  ${GREEN}✅ Server started successfully${NC}"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "  📡 Server URL: http://${PUBLIC_IP}:${PORT}"
    echo "  📋 Log file:   ${LOG_FILE}"
    echo ""
    echo "  Next, complete the following steps:"
    echo ""
    echo "  1. Add this IP to the WeChat API whitelist: ${PUBLIC_IP}"
    echo "     https://developers.weixin.qq.com/console/product/mp"
    echo ""
    echo "  2. Set the environment variable locally:"
    echo "     export WENYAN_SERVER=\"http://${PUBLIC_IP}:${PORT}\""
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
else
    echo -e "  ${RED}❌ Failed to start the server, check the log: ${LOG_FILE}${NC}"
    tail -20 "$LOG_FILE" 2>/dev/null
    exit 1
fi
