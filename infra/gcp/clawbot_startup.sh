#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="$(curl -s -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/project/project-id)"

apt-get update
apt-get install -y git curl ca-certificates gnupg python3-venv python3-pip

# Install Node.js (OpenClaw requires npm)
curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
apt-get install -y nodejs
npm install -g openclaw

# Install Google Cloud CLI for Secret Manager access
if ! command -v gcloud >/dev/null 2>&1; then
  echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" | tee /etc/apt/sources.list.d/google-cloud-sdk.list
  curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add -
  apt-get update
  apt-get install -y google-cloud-cli
fi

APP_DIR="/opt/agent-ops"
if [ ! -d "$APP_DIR/.git" ]; then
  git clone https://github.com/nathangonzalez/jcw-agent-ops.git "$APP_DIR"
else
  git -C "$APP_DIR" pull
fi

pip3 install --upgrade pip
pip3 install slack-bolt slack-sdk openai

# Fetch secrets
SLACK_BOT_TOKEN="$(gcloud secrets versions access latest --secret=slack_bot_token --project "$PROJECT_ID")"
SLACK_APP_TOKEN="$(gcloud secrets versions access latest --secret=slack_app_token --project "$PROJECT_ID")"
SLACK_SIGNING_SECRET="$(gcloud secrets versions access latest --secret=slack_signing_secret --project "$PROJECT_ID")"
ANTHROPIC_API_KEY="$(gcloud secrets versions access latest --secret=anthropic_api_key --project "$PROJECT_ID")"

cat >/etc/clawbot.env <<EOF
SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN}
SLACK_APP_TOKEN=${SLACK_APP_TOKEN}
SLACK_SIGNING_SECRET=${SLACK_SIGNING_SECRET}
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
OPENCLAW_BIN=/usr/local/bin/openclaw
CLAWDBOT_AGENT=orchestrator
CLAWDBOT_REPO_ROOT=${APP_DIR}
CLAWDBOT_LOG_DIR=${APP_DIR}/agent_outputs
CLAWDBOT_LOG_LEVEL=INFO
EOF

cat >/etc/systemd/system/clawbot.service <<'EOF'
[Unit]
Description=Clawbot Slack Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
EnvironmentFile=/etc/clawbot.env
WorkingDirectory=/opt/agent-ops
ExecStart=/usr/bin/python3 /opt/agent-ops/scripts/slack_bot.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now clawbot.service
