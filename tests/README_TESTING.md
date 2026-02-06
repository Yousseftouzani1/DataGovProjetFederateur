# 🧪 Quick Testing Guide

## Folder Structure Created

```
DataGovProjetFederateur/
├── tests/
│   ├── __init__.py
│   ├── conftest.py                    # Global test configuration
│   ├── integration/
│   │   └── test_services_health.py    # Test all services are running
│   ├── e2e/                           # End-to-end tests (you can add more)
│   ├── performance/                   # Performance tests
│   ├── security/                      # Security tests
│   └── results/                       # Test results will be saved here
│       └── *.html                     # HTML reports
├── services/
│   ├── auth-serv/tests/              # Unit tests for auth service
│   ├── cleaning-serv/tests/          # Unit tests for cleaning service
│   └── ... (all 9 services)
├── run_tests.py                       # Python test runner
└── RUN_TESTS.bat                      # Windows quick test script
```

## 📋 Step-by-Step: How to Run Tests

### Option 1: Quick Start (Windows - EASIEST)

```bash
# 1. Start Docker services
docker-compose up -d

# 2. Wait 20 seconds for services to start
# (Wait for all containers to be healthy)

# 3. Double-click this file:
RUN_TESTS.bat

# That's it! Results will be in tests/results/
```

### Option 2: Manual Testing

```bash
# 1. Start Docker services
docker-compose up -d

# 2. Wait for services (check with)
docker-compose ps
# All should show "Up (healthy)"

# 3. Install test dependencies
pip install pytest pytest-asyncio pytest-cov requests pytest-html

# 4. Run health check test
pytest tests/integration/test_services_health.py -v -s

# 5. View results
# Console output will show ✅ or ❌ for each test
```

### Option 3: Run with Coverage and HTML Report

```bash
# Start services
docker-compose up -d

# Run tests with HTML report
pytest tests/integration/ -v -s --html=tests/results/report.html --self-contained-html

# Open report
start tests/results/report.html  # Windows
```

## ✅ What Gets Tested

### Integration Tests (tests/integration/)
- ✅ All 9 services health check
- ✅ Services respond within 5 seconds
- ✅ No services are down

### Results You'll See

```
==================== SERVICES HEALTH SUMMARY ====================
auth                 : ✅ HEALTHY
taxonomie            : ✅ HEALTHY
presidio             : ✅ HEALTHY
cleaning             : ✅ HEALTHY
classification       : ✅ HEALTHY
correction           : ✅ HEALTHY
annotation           : ✅ HEALTHY
quality              : ✅ HEALTHY
ethimask             : ✅ HEALTHY
================================================================
```

## 🐛 Troubleshooting

### "Services not running" error
```bash
# Start Docker services
docker-compose up -d

# Check status
docker-compose ps

# Check logs if any service is unhealthy
docker-compose logs [service-name]
```

### "Connection refused" error
```bash
# Services might still be starting
# Wait 20-30 seconds and try again

# Or restart services
docker-compose restart
```

### "pytest not found" error
```bash
# Install pytest
pip install pytest pytest-asyncio pytest-cov requests pytest-html
```

## 📊 Understanding Test Results

### HTML Reports (tests/results/*.html)
- Detailed test results with timings
- Stack traces for failures
- Summary statistics
- Open in any web browser

### Console Output
- ✅ = Test passed
- ❌ = Test failed
- ⏳ = Test in progress

## 🚀 Next Steps

1. **Run the basic health test first** (verifies everything is working)
2. **Add unit tests** for specific services (see TESTING_PLAN.md)
3. **Add E2E tests** for complete workflows
4. **Run before every deployment** to catch issues early

## 📝 Quick Commands Cheat Sheet

```bash
# Start services
docker-compose up -d

# Quick test (Windows)
RUN_TESTS.bat

# Manual test
pytest tests/integration/ -v -s

# Test with HTML report
pytest tests/integration/ --html=tests/results/report.html --self-contained-html

# Test specific file
pytest tests/integration/test_services_health.py -v

# Stop services
docker-compose down
```

## 💡 Tips

1. **Always start Docker services first** before running tests
2. **Wait 20-30 seconds** after starting services before testing
3. **Check HTML reports** in tests/results/ for detailed information
4. **Run tests regularly** to catch issues early
5. **Add more tests** as you develop new features

---

**Ready to test?** Just run `RUN_TESTS.bat` and see the results!
