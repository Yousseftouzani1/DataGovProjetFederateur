#!/bin/bash

##############################################################################
# Script to check actual Atlas and Ranger versions on your VMware HDP VM
##############################################################################

echo "==========================================="
echo "Checking HDP Component Versions"
echo "==========================================="
echo ""

# Get the VMware VM IP from .env
VMWARE_IP="192.168.110.133"  # Or try 192.168.110.132

echo "Testing connection to VMware HDP at: $VMWARE_IP"
echo ""

# Check Atlas version
echo "1. Checking Apache Atlas version..."
ATLAS_VERSION=$(curl -s -u admin:ensias2025 "http://$VMWARE_IP:21000/api/atlas/admin/version" 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "✓ Atlas is reachable!"
    echo "Response: $ATLAS_VERSION"
else
    echo "✗ Atlas is NOT reachable at http://$VMWARE_IP:21000"
    echo "Try the other IP: 192.168.110.132"
fi
echo ""

# Check Ranger version
echo "2. Checking Apache Ranger version..."
RANGER_VERSION=$(curl -s -u admin:hortonworks1 "http://$VMWARE_IP:6080/service/public/v2/api/servicedef/" 2>/dev/null | head -c 200)
if [ $? -eq 0 ]; then
    echo "✓ Ranger is reachable!"
    echo "Response preview: $RANGER_VERSION"
else
    echo "✗ Ranger is NOT reachable at http://$VMWARE_IP:6080"
fi
echo ""

# Check Ambari
echo "3. Checking Ambari for version info..."
curl -s -u raj_ops:raj_ops "http://$VMWARE_IP:8080/api/v1/clusters" 2>/dev/null | head -20
echo ""

echo "==========================================="
echo "Please also check manually:"
echo "1. Visit http://$VMWARE_IP:8080 (Ambari)"
echo "2. Look at the versions displayed in the UI"
echo "3. Take a screenshot and share it"
echo "==========================================="
