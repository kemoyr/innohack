#!/usr/bin/env bash
# Deploys the VolunteerPlus dashboard onto auroraclient.fun.
#
# What it does:
#   1. Creates a dedicated "innohack" system user (first run only).
#   2. Installs Python deps into a venv and builds the React frontend.
#   3. Installs the nginx vhost for auroraclient.fun (backing up any file it
#      overwrites) and the systemd service, then (re)starts everything.
#
# Run as: sudo bash deploy/deploy.sh
# Rollback: sudo bash deploy/rollback.sh

set -euo pipefail

PROJECT_DIR="/opt/innohack"
NGINX_SITE="/etc/nginx/sites-available/volunteerplus"
NGINX_BACKUP_DIR="/etc/nginx/sites-available/backup"
SERVICE_NAME="volunteerplus.service"
SERVICE_USER="innohack"

if [[ $EUID -ne 0 ]]; then
  echo "Run this with sudo: sudo bash deploy/deploy.sh" >&2
  exit 1
fi

if ! id "$SERVICE_USER" &>/dev/null; then
  echo "==> Creating system user $SERVICE_USER"
  useradd --system --home-dir "$PROJECT_DIR" --shell /usr/sbin/nologin "$SERVICE_USER"
fi

echo "==> Syncing project files"
if [[ "$PROJECT_DIR" != "$(pwd)" ]]; then
  mkdir -p "$PROJECT_DIR"
  rsync -a --delete --exclude .git --exclude .venv --exclude data --exclude frontend/node_modules --exclude frontend/dist "$(pwd)/" "$PROJECT_DIR/"
fi
chown -R "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR"

echo "==> Installing Python deps"
if [[ ! -d "$PROJECT_DIR/.venv" ]]; then
  sudo -u "$SERVICE_USER" python3 -m venv "$PROJECT_DIR/.venv"
fi
sudo -u "$SERVICE_USER" "$PROJECT_DIR/.venv/bin/pip" install --no-cache-dir -q -r "$PROJECT_DIR/requirements.txt"

echo "==> Building frontend"
sudo -u "$SERVICE_USER" bash -c "cd '$PROJECT_DIR/frontend' && npm ci && npm run build"

echo "==> Installing nginx vhost"
mkdir -p "$NGINX_BACKUP_DIR"
if [[ -f "$NGINX_SITE" ]]; then
  cp "$NGINX_SITE" "$NGINX_BACKUP_DIR/volunteerplus.$(date +%Y%m%d-%H%M%S).bak"
fi
cp "$PROJECT_DIR/deploy/nginx-auroraclient.conf" "$NGINX_SITE"
ln -sf "$NGINX_SITE" /etc/nginx/sites-enabled/volunteerplus
nginx -t

echo "==> Installing systemd service"
cp "$PROJECT_DIR/deploy/volunteerplus.service" "/etc/systemd/system/$SERVICE_NAME"
systemctl daemon-reload
systemctl enable --now "$SERVICE_NAME"
systemctl restart "$SERVICE_NAME"

echo "==> Reloading nginx"
systemctl reload nginx

echo "==> Done. Status:"
systemctl --no-pager status "$SERVICE_NAME" | head -10
echo
echo "Dashboard: https://auroraclient.fun"
echo "To roll back: sudo bash deploy/rollback.sh"
