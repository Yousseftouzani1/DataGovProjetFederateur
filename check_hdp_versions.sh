#!/bin/bash

##############################################################################
# Script to check actual Atlas and Ranger versions on your VMware HDP VM
##############################################################################

echo "==========================================="
echo "Checking HDP Component Versions"
echo "==========================================="
echo ""

# Get the VMware VM IP from .env file
if [ -f ".env" ]; then
    source <(grep -E '^(ATLAS_URL|RANGER_URL|AMBARI_URL|ATLAS_PASSWORD|RANGER_PASSWORD)=' .env)
    VMWARE_IP=$(echo "$ATLAS_URL" | sed -E 's|https?://([^:]+):.*|\1|')
else
    echo "ERROR: .env file not found. Please create it first."
    echo "Copy .env.example to .env and set the correct IP."
    exit 1
fi

echo "Testing connection to VMware HDP at: $VMWARE_IP"
echo ""

# Check Atlas version
echo "1. Checking Apache Atlas version..."
ATLAS_VERSION=$(curl -s -u admin:${ATLAS_PASSWORD:-ensias2025} "${ATLAS_URL}/api/atlas/admin/version" 2>/dev/null)
if [ $? -eq 0 ] && [ -n "$ATLAS_VERSION" ]; then
    echo "✓ Atlas is reachable!"
    echo "Response: $ATLAS_VERSION"
else
    echo "✗ Atlas is NOT reachable at ${ATLAS_URL}"
fi
echo ""

# Check Ranger version
echo "2. Checking Apache Ranger version..."
RANGER_VERSION=$(curl -s -u admin:${RANGER_PASSWORD:-hortonworks1} "${RANGER_URL}/service/public/v2/api/servicedef/" 2>/dev/null | head -c 200)
if [ $? -eq 0 ] && [ -n "$RANGER_VERSION" ]; then
    echo "✓ Ranger is reachable!"
    echo "Response preview: $RANGER_VERSION"
else
    echo "✗ Ranger is NOT reachable at ${RANGER_URL}"
fi
echo ""

# Check Ambari
echo "3. Checking Ambari for version info..."
curl -s -u raj_ops:raj_ops "${AMBARI_URL}/api/v1/clusters" 2>/dev/null | head -20
echo ""

echo "==========================================="
echo "Please also check manually:"
echo "1. Visit ${AMBARI_URL} (Ambari)"
echo "2. Look at the versions displayed in the UI"
echo "==========================================="
