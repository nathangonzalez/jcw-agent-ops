#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/agent-ops"
ENV_FILE="/etc/clawbot.env"

sudo cp "$APP_DIR/infra/systemd/clawbot-monitor.service" /etc/systemd/system/clawbot-monitor.service
sudo cp "$APP_DIR/infra/systemd/clawbot-monitor.timer" /etc/systemd/system/clawbot-monitor.timer
sudo cp "$APP_DIR/infra/systemd/agentops-webui.service" /etc/systemd/system/agentops-webui.service

if [ -f "$ENV_FILE" ]; then
  if ! grep -q "CLAWDBOT_MONITOR_INTERVAL_MIN" "$ENV_FILE"; then
    echo "CLAWDBOT_MONITOR_INTERVAL_MIN=15" | sudo tee -a "$ENV_FILE" >/dev/null
  fi
  if ! grep -q "AGENT_OPS_HOST" "$ENV_FILE"; then
    echo "AGENT_OPS_HOST=127.0.0.1" | sudo tee -a "$ENV_FILE" >/dev/null
  fi
  if ! grep -q "AGENT_OPS_PORT" "$ENV_FILE"; then
    echo "AGENT_OPS_PORT=8091" | sudo tee -a "$ENV_FILE" >/dev/null
  fi
fi

sudo systemctl daemon-reload
sudo systemctl enable --now clawbot-monitor.timer
sudo systemctl enable --now agentops-webui.service

sudo systemctl status clawbot-monitor.timer --no-pager
sudo systemctl status agentops-webui.service --no-pager