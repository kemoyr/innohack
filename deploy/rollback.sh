#!/usr/bin/env bash
# Reverts auroraclient.fun back to the store website and stops the dashboard
# service. Does not delete the dashboard's files or database.
#
# Run as: sudo bash deploy/rollback.sh

set -euo pipefail

NGINX_SITE="/etc/nginx/sites-available/aurora-site"
NGINX_BACKUP_DIR="/etc/nginx/sites-available/backup"
SERVICE_NAME="beeline-dashboard.service"

if [[ $EUID -ne 0 ]]; then
  echo "Run this with sudo: sudo bash deploy/rollback.sh" >&2
  exit 1
fi

LATEST_BACKUP=$(ls -t "$NGINX_BACKUP_DIR"/aurora-site.*.bak 2>/dev/null | head -1 || true)
if [[ -z "$LATEST_BACKUP" ]]; then
  echo "No backup found in $NGINX_BACKUP_DIR — nothing to roll back to." >&2
  exit 1
fi

echo "==> Restoring store vhost from $LATEST_BACKUP"
cp "$LATEST_BACKUP" "$NGINX_SITE"
nginx -t
systemctl reload nginx

echo "==> Stopping dashboard service (files and database are kept)"
systemctl stop "$SERVICE_NAME" || true

echo "==> Done. auroraclient.fun now serves the store site again."
