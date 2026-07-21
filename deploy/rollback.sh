#!/usr/bin/env bash
# Stops the VolunteerPlus dashboard and restores the previous nginx vhost
# (if one was backed up by deploy.sh). Does not delete the app's files or
# database.
#
# Run as: sudo bash deploy/rollback.sh

set -euo pipefail

NGINX_SITE="/etc/nginx/sites-available/volunteerplus"
NGINX_BACKUP_DIR="/etc/nginx/sites-available/backup"
SERVICE_NAME="volunteerplus.service"

if [[ $EUID -ne 0 ]]; then
  echo "Run this with sudo: sudo bash deploy/rollback.sh" >&2
  exit 1
fi

echo "==> Stopping dashboard service (files and database are kept)"
systemctl stop "$SERVICE_NAME" || true

LATEST_BACKUP=$(ls -t "$NGINX_BACKUP_DIR"/volunteerplus.*.bak 2>/dev/null | head -1 || true)
if [[ -z "$LATEST_BACKUP" ]]; then
  echo "No nginx backup found in $NGINX_BACKUP_DIR — nothing to restore, vhost left as-is." >&2
  exit 0
fi

echo "==> Restoring previous nginx vhost from $LATEST_BACKUP"
cp "$LATEST_BACKUP" "$NGINX_SITE"
nginx -t
systemctl reload nginx

echo "==> Done."
