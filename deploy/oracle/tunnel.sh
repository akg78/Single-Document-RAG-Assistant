#!/usr/bin/env bash
# Quick HTTPS tunnel via Cloudflare (free, no domain required).
# Gives a https://*.trycloudflare.com URL for your Vercel frontend.
#
# Usage: bash deploy/oracle/tunnel.sh

set -euo pipefail

if ! curl -s http://127.0.0.1:8000/health | grep -q '"status":"ok"'; then
  echo "ERROR: Backend is not healthy on http://127.0.0.1:8000"
  echo "Run setup.sh first."
  exit 1
fi

if ! command -v cloudflared >/dev/null 2>&1; then
  echo "==> Installing cloudflared..."
  ARCH="$(uname -m)"
  case "$ARCH" in
    aarch64|arm64)
      CF_ARCH="arm64"
      ;;
    x86_64|amd64)
      CF_ARCH="amd64"
      ;;
    *)
      echo "Unsupported architecture: $ARCH"
      exit 1
      ;;
  esac
  curl -fsSL "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-${CF_ARCH}" -o /tmp/cloudflared
  chmod +x /tmp/cloudflared
  sudo mv /tmp/cloudflared /usr/local/bin/cloudflared
fi

echo ""
echo "Starting Cloudflare quick tunnel → http://127.0.0.1:8000"
echo "Copy the https://....trycloudflare.com URL when it appears."
echo "Set that URL as NEXT_PUBLIC_API_URL on Vercel."
echo "Add the same URL to CORS_ORIGINS in deploy/oracle/.env, then:"
echo "  docker compose -f deploy/oracle/docker-compose.yml up -d"
echo ""
echo "Press Ctrl+C to stop the tunnel."
echo ""

cloudflared tunnel --url http://127.0.0.1:8000
