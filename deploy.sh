#!/bin/bash
# ============================================
# DataGov Platform - VPS Deployment Script
# ============================================
# Usage:
#   1. Get a VPS (8GB RAM, 4 vCPU recommended)
#   2. SSH into VPS: ssh root@YOUR_VPS_IP
#   3. Run: curl -sSL https://raw.githubusercontent.com/YOUR_REPO/deploy.sh | bash
#   OR clone repo first and run: bash deploy.sh
# ============================================

set -e

echo "============================================"
echo "  DataGov Platform - Deployment"
echo "============================================"

# Step 1: Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "[1/6] Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
    echo "  Docker installed successfully"
else
    echo "[1/6] Docker already installed"
fi

# Step 2: Install Docker Compose plugin if not present
if ! docker compose version &> /dev/null; then
    echo "[2/6] Installing Docker Compose..."
    apt-get update -qq && apt-get install -y -qq docker-compose-plugin
    echo "  Docker Compose installed"
else
    echo "[2/6] Docker Compose already installed"
fi

# Step 3: Setup environment
echo "[3/6] Setting up environment..."
if [ ! -f .env ]; then
    if [ -f .env.production ]; then
        cp .env.production .env
        echo "  Copied .env.production -> .env"
        echo "  IMPORTANT: Edit .env and replace YOUR_VPS_IP with your actual VPS IP!"
    else
        echo "  ERROR: No .env.production found. Create it first."
        exit 1
    fi
else
    echo "  .env already exists"
fi

# Step 4: Use production nginx config
echo "[4/6] Setting up production nginx..."
if [ -f gateway-nginx/nginx.prod.conf ]; then
    cp gateway-nginx/nginx.prod.conf gateway-nginx/nginx.conf
    echo "  Production nginx config applied"
fi

# Step 5: Build and start all services
echo "[5/6] Building and starting all services..."
echo "  This will take 10-20 minutes on first run (downloading ML models)..."
docker compose up -d --build

# Step 6: Wait for services to be ready
echo "[6/6] Waiting for services to start..."
echo "  Atlas takes ~2-3 minutes to initialize..."

# Wait for MongoDB first
echo -n "  MongoDB: "
for i in $(seq 1 30); do
    if docker exec datagov-mongo mongosh --eval "db.adminCommand('ping')" &> /dev/null; then
        echo "OK"
        break
    fi
    echo -n "."
    sleep 2
done

# Wait for auth service
echo -n "  Auth Service: "
for i in $(seq 1 30); do
    if curl -sf http://localhost:8001/health &> /dev/null; then
        echo "OK"
        break
    fi
    echo -n "."
    sleep 2
done

# Wait for Atlas (takes longer)
echo -n "  Apache Atlas: "
for i in $(seq 1 60); do
    if curl -sf http://localhost:21000/api/atlas/v2/types/typedefs -u admin:admin &> /dev/null; then
        echo "OK"
        break
    fi
    echo -n "."
    sleep 5
done

# Print status
echo ""
echo "============================================"
echo "  Deployment Complete!"
echo "============================================"
echo ""

# Get VPS IP
VPS_IP=$(curl -s ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}')

echo "  Services:"
echo "  -----------------------------------------"
echo "  Frontend:        http://${VPS_IP}:8000"
echo "  Auth API:        http://${VPS_IP}:8001/docs"
echo "  Apache Atlas:    http://${VPS_IP}:21000  (admin/admin)"
echo "  Apache Ranger:   http://${VPS_IP}:6080   (admin/rangerR0cks!)"
echo "  Airflow:         http://${VPS_IP}:8081   (admin/DataGov2025!)"
echo "  -----------------------------------------"
echo ""
echo "  Health checks:"
docker ps --format "  {{.Names}}: {{.Status}}" | sort
echo ""
echo "  Next steps:"
echo "  1. Update ALLOWED_ORIGINS in .env with http://${VPS_IP}:8000"
echo "  2. Restart: docker compose up -d"
echo "  3. (Optional) Setup domain + HTTPS with Caddy or Certbot"
