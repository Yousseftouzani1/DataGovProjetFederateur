# 🐳 HDP Docker Migration Guide

## Overview
This guide documents the migration from VMware HDP Sandbox to Docker-based HDP deployment to solve the dynamic IP address problem.

## ✅ Problem Solved
- **Before**: VMware IP changed between `192.168.110.132` and `192.168.110.133`, breaking Atlas/Ranger connections
- **After**: All services run on `localhost` with fixed ports - no more IP changes!

## 📋 Migration Checklist

### Phase 1: Configuration Updates ✅ COMPLETED
- [x] Moved Airflow from port 8080 → 8081 (resolved port conflict)
- [x] Updated `.env` with localhost URLs
- [x] Updated `PROJECT_SERVICES_MAP.md` documentation
- [x] Fixed 17 Python scripts with hardcoded IPs
- [x] Created `.wslconfig` for WSL2 resource allocation
- [x] Created deployment script `deploy-hdp-docker.sh`

### Phase 2: Docker Deployment (Manual Steps Required)

#### Step 1: Apply WSL2 Configuration
```bash
# Shutdown WSL to apply .wslconfig changes
wsl --shutdown

# Restart Docker Desktop from Windows
# (Right-click Docker icon in system tray → Restart)
```

#### Step 2: Deploy HDP Container
```bash
# Run the deployment script
cd c:\Users\ibnou\Desktop\DataGovProjetFederateur
bash deploy-hdp-docker.sh
```

This will:
- Pull HDP 3.0.1 image (~21GB download)
- Create container with all necessary port mappings
- Start all HDP services (Ambari 2.7.0, Atlas 1.0.0, Ranger 1.1.0, etc.)

#### Step 3: Verify Services
After 2-3 minutes, verify all services are accessible:

| Service | URL | Credentials |
|---------|-----|-------------|
| Ambari | http://localhost:8080 | raj_ops / raj_ops |
| Atlas | http://localhost:21000 | admin / ensias2025 |
| Ranger | http://localhost:6080 | admin / hortonworks1 |
| NameNode | http://localhost:50070 | N/A |
| Web Shell | http://localhost:4200 | root / hadoop |

#### Step 4: Test Integration
```bash
# Test Atlas connectivity
python check_atlas_api.py

# Test Ranger connectivity
python diagnose_integrations.py
```

#### Step 5: Shutdown VMware HDP
Once Docker HDP is working:
```bash
# In VMware:
# 1. Stop the HDP VM
# 2. Optionally remove the VM to free disk space
```

## 🔌 Service Port Mappings

### Critical Ports
- `8080` - Ambari Web UI
- `21000` - Apache Atlas
- `6080` - Apache Ranger
- `50070` - HDFS NameNode
- `4200` - Shell-in-a-box (Web Terminal)
- `2222` - SSH Access

### Full Port List
See `deploy-hdp-docker.sh` for complete port mapping configuration.

## 🚀 Daily Usage

### Start HDP
```bash
docker start sandbox-hdp

# Wait 2-3 minutes for services to start
# Check status:
docker logs -f sandbox-hdp
```

### Stop HDP
```bash
docker stop sandbox-hdp
```

### Access Container Shell
```bash
# Via SSH
ssh root@localhost -p 2222

# Via Docker exec
docker exec -it sandbox-hdp bash

# Via Web Shell
# Visit http://localhost:4200
```

### Transfer Files
```bash
# Host → Container
docker cp "/path/to/file.txt" "sandbox-hdp:/"

# Container → Host
docker cp "sandbox-hdp:/path/to/file.txt" "/local/path/"
```

## ⚠️ Important Warnings

1. **DO NOT delete the container** - All data will be lost and you'll need to reinstall
2. **Container must be running** before executing `docker cp` commands
3. **First SSH login** will require password change from default `hadoop`
4. **Services take time** - Wait 2-3 minutes after container start before accessing UIs

## 🔧 Troubleshooting

### Port Already in Use
```bash
# Check what's using a port
netstat -ano | findstr :8080

# Stop the conflicting process or change port mapping
```

### Container Won't Start
```bash
# Check logs
docker logs sandbox-hdp

# Restart Docker Desktop
wsl --shutdown
# Restart Docker Desktop from system tray
```

### Services Not Responding
```bash
# Give it more time (up to 5 minutes)
docker logs -f sandbox-hdp

# If still failing, restart container
docker restart sandbox-hdp
```

### Out of Memory
```bash
# Increase memory in .wslconfig
# Edit C:\Users\ibnou\.wslconfig
# Change memory=4GB to memory=8GB
# Run: wsl --shutdown
# Restart Docker Desktop
```

## 📊 Resource Requirements

- **Disk Space**: ~25GB (21GB image + 4GB runtime)
- **Memory**: 8GB minimum (10GB recommended for HDP 3.0.1)
- **CPU**: 4 cores recommended
- **Network**: Internet connection for initial download

## 📌 HDP 3.0.1 Component Versions (Verified)

- **Apache Atlas**: 1.0.0.3.0.1.0-187
- **Apache Ranger**: 1.1.0
- **Apache Ambari**: 2.7.0
- **Apache Hadoop**: 3.1.1
- **Apache Hive**: 3.1.0
- **Apache HBase**: 2.0.2
- **Apache Spark**: 2.3.2

## 🔄 Rollback Plan

If Docker deployment fails:
1. Keep VMware HDP running
2. Set `MOCK_GOVERNANCE=true` in `.env` to use mock mode
3. Services will work without real Atlas/Ranger

## 📚 References

- [HDP Docker Guide](https://hackmd.io/@firasj/BkSQJQ8eh)
- [Hortonworks Sandbox Documentation](https://www.cloudera.com/downloads/hortonworks-sandbox.html)
- [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)

## ✨ Benefits of Docker Migration

✅ **Fixed IP Addresses** - No more changing IPs!
✅ **Easy Start/Stop** - Simple docker commands
✅ **Better Integration** - All services in same Docker network
✅ **Portable** - Can run on any machine with Docker
✅ **Consistent** - Same environment every time
✅ **Easier Backup** - Export/import container images

---

**Migration Date**: 2026-02-05
**Project**: DataGov (DataSentinel)
**Status**: Configuration Complete ✅ | Deployment Pending ⏳
