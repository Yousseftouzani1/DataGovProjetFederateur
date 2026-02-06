#!/usr/bin/env python3
"""
Quick Test Runner Script
Runs tests and generates reports
"""
import subprocess
import sys
import os
from datetime import datetime

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, shell=True)
    return result.returncode == 0

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("📋 DataGov Testing Suite")
    print("="*60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Check if pytest is installed
    try:
        subprocess.run(["pytest", "--version"], check=True, capture_output=True)
    except:
        print("\n❌ pytest not installed!")
        print("Install with: pip install pytest pytest-asyncio pytest-cov requests")
        return False

    # Create results directory
    os.makedirs("tests/results", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    tests_to_run = [
        {
            "cmd": "pytest tests/integration/test_services_health.py -v -s",
            "desc": "Integration Tests: Services Health Check",
            "report": f"tests/results/health_check_{timestamp}.html"
        },
        # Add more test suites here
    ]

    all_passed = True
    for test in tests_to_run:
        cmd_with_report = f"{test['cmd']} --html={test['report']} --self-contained-html"
        success = run_command(cmd_with_report, test['desc'])
        if not success:
            all_passed = False
            print(f"❌ {test['desc']} FAILED")
        else:
            print(f"✅ {test['desc']} PASSED")

    print("\n" + "="*60)
    if all_passed:
        print("✅ ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Reports saved in: tests/results/")
    print("="*60)

    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
