#!/usr/bin/env bash
# Oracle Cloud ARM VM — install Docker and start the RAG backend.
# Usage (on the VM, after cloning the repo):
#   cd Single-Document-RAG-Assistant
#   bash deploy/oracle/setup.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DEPLOY_DIR="$REPO_ROOT/deploy/oracle"

echo "==> Installing Docker (Ubuntu/Debian)..."
if ! command -v docker >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y ca-certificates curl gnupg
  sudo install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  sudo chmod a+r /etc/apt/keyrings/docker.gpg
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
    $(. /etc/os-release && echo "$VERSION_CODENAME") stable" |
    sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
  sudo apt-get update
  sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
  sudo usermod -aG docker "$USER" || true
  echo "Docker installed. You may need to log out and back in for group changes."
fi

if [[ ! -f "$DEPLOY_DIR/.env" ]]; then
  cp "$DEPLOY_DIR/.env.example" "$DEPLOY_DIR/.env"
  echo ""
  echo "Created $DEPLOY_DIR/.env — edit OPENAI_API_KEY before continuing."
  echo "Then re-run: bash deploy/oracle/setup.sh"
  exit 0
fi

if grep -q "your-key-here" "$DEPLOY_DIR/.env"; then
  echo "ERROR: Set a real OPENAI_API_KEY in $DEPLOY_DIR/.env first."
  exit 1
fi

echo "==> Building and starting backend (first build may take 20–40 min)..."
cd "$REPO_ROOT"
sudo docker compose -f deploy/oracle/docker-compose.yml up -d --build

echo ""
echo "Backend started on port 8000."
echo "Health check: curl http://127.0.0.1:8000/health"
echo ""
echo "Next: expose HTTPS for Vercel (mixed content blocks plain HTTP)."
echo "  bash deploy/oracle/tunnel.sh"
