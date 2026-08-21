@echo off
REM Quick HTTPS tunnel for local backend (Windows). Requires backend on port 8000.
REM Usage: deploy\oracle\tunnel.ps1

where cloudflared >nul 2>&1
if errorlevel 1 (
  echo Download cloudflared from https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
  exit /b 1
)

curl -s http://127.0.0.1:8000/health | findstr "ok" >nul
if errorlevel 1 (
  echo Backend not healthy on http://127.0.0.1:8000 — start uvicorn first.
  exit /b 1
)

echo Starting Cloudflare quick tunnel to http://127.0.0.1:8000
echo Copy the https://....trycloudflare.com URL into Vercel NEXT_PUBLIC_API_URL
cloudflared tunnel --url http://127.0.0.1:8000
