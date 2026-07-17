#!/bin/bash
set -e

echo "=== Волонтёр+ Setup ==="

# Python dependencies
echo "[1/4] Installing Python dependencies..."
pip install -r requirements.txt --break-system-packages

# Frontend build
echo "[2/4] Building frontend..."
cd frontend && npm install && npm run build && cd ..

# Demo data
echo "[3/4] Seeding demo data..."
python demo_data.py

# Run
echo "[4/4] Starting bot + dashboard..."
echo "  Telegram bot: running"
echo "  Dashboard: http://localhost:8000"
echo "  API docs: http://localhost:8000/docs"
echo ""
python bot/main.py
