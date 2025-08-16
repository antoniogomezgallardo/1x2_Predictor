#!/usr/bin/env python3
"""
Test runner script for Quiniela Predictor
Executes different test suites and generates reports
"""
import subprocess
import sys
import os
from pathlib import Path
import argparse
from datetime import datetime

def run_command(command, description):
    """Run a command and capture output"""
    print(f"\n{'='*60}")
    print(f"*** {description} ***")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        if result.returncode == 0:
            print(f"PASSED: {description}")
        else:
            print(f"FAILED: {description} (exit code: {result.returncode})")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"ERROR running {description}: {e}")
        return False

def check_dependencies():
    """Check if testing dependencies are installed"""
    print("Checking testing dependencies...")
    
    required_packages = [
        'pytest', 'pytest-cov', 'pytest-asyncio', 'httpx'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install " + " ".join(missing_packages))
        return False
    
    print("All testing dependencies are installed")
    return True

def run_unit_tests():
    """Run unit tests"""
    command = "python -m pytest tests/unit/ -v --tb=short -m unit"
    return run_command(command, "Unit Tests")

def run_integration_tests():
    """Run integration tests"""
    command = "python -m pytest tests/integration/ -v --tb=short -m integration"
    return run_command(command, "Integration Tests")

def run_critical_tests():
    """Run only critical tests"""
    command = "python -m pytest -v --tb=short -m critical"
    return run_command(command, "Critical Tests")

def run_all_tests():
    """Run all tests"""
    command = "python -m pytest tests/ -v --tb=short"
    return run_command(command, "All Tests")

def run_coverage_report():
    """Run tests with coverage reporting"""
    command = "python -m pytest tests/ --cov=backend/app --cov-report=html --cov-report=term-missing --cov-fail-under=75 -v"
    return run_command(command, "Coverage Report")

def run_performance_tests():
    """Run performance/slow tests"""
    command = "python -m pytest -v --tb=short -m slow"
    return run_command(command, "Performance Tests")

def run_specific_test(test_path):
    """Run a specific test file or function"""
    command = f"python -m pytest {test_path} -v --tb=short"
    return run_command(command, f"Specific Test: {test_path}")

def generate_test_report():
    """Generate comprehensive test report"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"test_report_{timestamp}.html"
    
    command = f"python -m pytest tests/ --html={report_file} --self-contained-html --cov=backend/app --cov-report=html:htmlcov_{timestamp}"
    success = run_command(command, "Test Report Generation")
    
    if success:
        print(f"\nTest report generated: {report_file}")
        print(f"Coverage report generated: htmlcov_{timestamp}/index.html")
    
    return success

def lint_and_format():
    """Run linting and formatting checks"""
    print("\nRunning code quality checks...")
    
    # Black formatting check
    black_success = run_command("black --check backend/app tests/", "Black Formatting Check")
    
    # Flake8 linting  
    flake8_success = run_command("flake8 backend/app tests/ --max-line-length=120 --ignore=E203,W503", "Flake8 Linting")
    
    return black_success and flake8_success

def setup_test_environment():
    """Setup test environment"""
    print("Setting up test environment...")
    
    # Create necessary directories
    os.makedirs("tests/fixtures", exist_ok=True)
    os.makedirs("tests/unit", exist_ok=True)
    os.makedirs("tests/integration", exist_ok=True)
    os.makedirs("tests/e2e", exist_ok=True)
    os.makedirs("htmlcov", exist_ok=True)
    
    # Create __init__.py files
    init_files = [
        "tests/__init__.py",
        "tests/unit/__init__.py", 
        "tests/integration/__init__.py",
        "tests/e2e/__init__.py"
    ]
    
    for init_file in init_files:
        Path(init_file).touch(exist_ok=True)
    
    print("Test environment setup complete")

def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description="Quiniela Predictor Test Runner")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--critical", action="store_true", help="Run critical tests only")
    parser.add_argument("--coverage", action="store_true", help="Run tests with coverage")
    parser.add_argument("--performance", action="store_true", help="Run performance tests")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--report", action="store_true", help="Generate HTML report")
    parser.add_argument("--lint", action="store_true", help="Run linting checks")
    parser.add_argument("--setup", action="store_true", help="Setup test environment")
    parser.add_argument("--test", type=str, help="Run specific test (file or function)")
    parser.add_argument("--install-deps", action="store_true", help="Install testing dependencies")
    
    args = parser.parse_args()
    
    print("*** Quiniela Predictor Test Suite ***")
    print("=" * 60)
    
    # Setup if requested
    if args.setup:
        setup_test_environment()
        return
    
    # Install dependencies if requested
    if args.install_deps:
        packages = [
            "pytest", "pytest-cov", "pytest-mock", "pytest-benchmark", 
            "pytest-xdist", "pytest-asyncio", "factory-boy", "freezegun",
            "responses", "coverage[toml]", "pytest-html"
        ]
        command = f"pip install {' '.join(packages)}"
        run_command(command, "Installing Testing Dependencies")
        return
    
    # Check dependencies
    if not check_dependencies():
        print("\nPlease install missing dependencies first:")
        print("python run_tests.py --install-deps")
        sys.exit(1)
    
    success_count = 0
    total_tests = 0
    
    # Run specific test
    if args.test:
        total_tests = 1
        if run_specific_test(args.test):
            success_count += 1
    
    # Run different test suites
    elif args.unit:
        total_tests = 1
        if run_unit_tests():
            success_count += 1
    
    elif args.integration:
        total_tests = 1
        if run_integration_tests():
            success_count += 1
    
    elif args.critical:
        total_tests = 1
        if run_critical_tests():
            success_count += 1
    
    elif args.coverage:
        total_tests = 1
        if run_coverage_report():
            success_count += 1
    
    elif args.performance:
        total_tests = 1
        if run_performance_tests():
            success_count += 1
    
    elif args.report:
        total_tests = 1
        if generate_test_report():
            success_count += 1
    
    elif args.lint:
        total_tests = 1
        if lint_and_format():
            success_count += 1
    
    elif args.all:
        # Run comprehensive test suite
        tests = [
            ("Unit Tests", run_unit_tests),
            ("Integration Tests", run_integration_tests),
            ("Critical Tests", run_critical_tests),
            ("Coverage Report", run_coverage_report)
        ]
        
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            if test_func():
                success_count += 1
        
        # Also run linting
        lint_and_format()
    
    else:
        # Default: run critical tests
        total_tests = 1
        if run_critical_tests():
            success_count += 1
    
    # Summary
    if total_tests > 0:
        print(f"\n{'='*60}")
        print(f"TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Passed: {success_count}/{total_tests}")
        print(f"Failed: {total_tests - success_count}/{total_tests}")
        
        success_rate = (success_count / total_tests) * 100
        print(f"Success Rate: {success_rate:.1f}%")
        
        if success_count == total_tests:
            print("All tests passed!")
            sys.exit(0)
        else:
            print("Some tests failed!")
            sys.exit(1)
    else:
        print("\nNo tests specified. Use --help for options.")
        print("Quick start: python run_tests.py --critical")

if __name__ == "__main__":
    main()