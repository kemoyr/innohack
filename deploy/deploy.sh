#!/usr/bin/env bash
# Deploys the Beeline Volunteer+ dashboard onto auroraclient.fun.
#
# What it does:
#   1. Builds the frontend and copies it to /var/www/beeline.
#   2. Backs up the current nginx vhost for auroraclient.fun (the store site)
#      and replaces it with the dashboard vhost. Store files under
#      /var/www/aurora and the aurora-core service/api.auroraclient.fun are
#      left untouched.
#   3. Installs and starts the beeline-dashboard systemd service on 127.0.0.1:8000.
#
# Run as: sudo bash deploy/deploy.sh
# Rollback: sudo bash deploy/rollback.sh

set -euo pipefail

PROJECT_DIR="/home/mmggaas3/beeline_project"
WEB_ROOT="/var/www/beeline"
NGINX_SITE="/etc/nginx/sites-available/aurora-site"
NGINX_BACKUP_DIR="/etc/nginx/sites-available/backup"
SERVICE_NAME="beeline-dashboard.service"

if [[ $EUID -ne 0 ]]; then
  echo "Run this with sudo: sudo bash deploy/deploy.sh" >&2
  exit 1
fi

echo "==> Building frontend"
sudo -u mmggaas3 bash -c "cd '$PROJECT_DIR/frontend' && npm ci && npm run build"

echo "==> Publishing frontend to $WEB_ROOT"
mkdir -p "$WEB_ROOT"
rsync -a --delete "$PROJECT_DIR/frontend/dist/" "$WEB_ROOT/"
chown -R root:root "$WEB_ROOT"
find "$WEB_ROOT" -type d -exec chmod 755 {} \;
find "$WEB_ROOT" -type f -exec chmod 644 {} \;

echo "==> Backing up current nginx vhost for auroraclient.fun (the store site)"
mkdir -p "$NGINX_BACKUP_DIR"
cp "$NGINX_SITE" "$NGINX_BACKUP_DIR/aurora-site.$(date +%Y%m%d-%H%M%S).bak"

echo "==> Installing dashboard nginx vhost"
cp "$PROJECT_DIR/deploy/nginx-auroraclient.conf" "$NGINX_SITE"
nginx -t

echo "==> Installing systemd service"
cp "$PROJECT_DIR/deploy/beeline-dashboard.service" "/etc/systemd/system/$SERVICE_NAME"
systemctl daemon-reload
systemctl enable --now "$SERVICE_NAME"

echo "==> Reloading nginx"
systemctl reload nginx

echo "==> Done. Status:"
systemctl --no-pager status "$SERVICE_NAME" | head -10
echo
echo "Dashboard: https://auroraclient.fun"
echo "Store site backup saved in: $NGINX_BACKUP_DIR"
echo "To roll back to the store site: sudo bash deploy/rollback.sh"
