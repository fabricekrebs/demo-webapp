#!/bin/bash

# Pre-commit Quality and Security Check Script
# This script runs the same checks as the GitHub Actions CI pipeline locally
# Run this script before committing to ensure your code will pass CI

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print status messages
print_status() {
    echo -e "${BLUE}🔍 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if we're in a virtual environment
check_venv() {
    if [[ "$VIRTUAL_ENV" == "" ]]; then
        print_warning "Not in a virtual environment. Activating project venv..."
        if [[ -f ".venv/bin/activate" ]]; then
            source .venv/bin/activate
            print_success "Virtual environment activated"
        else
            print_error "Virtual environment not found. Please create and activate a virtual environment."
            exit 1
        fi
    else
        print_success "Virtual environment is active: $VIRTUAL_ENV"
    fi
}

# Initialize counters
TESTS_PASSED=0
TESTS_FAILED=0
TOTAL_TESTS=0

# Function to run a test and track results
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    print_status "$test_name"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    if eval "$test_command"; then
        print_success "$test_name passed"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        print_error "$test_name failed"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

echo "🚀 Pre-commit Quality and Security Check Script"
echo "=============================================="
echo ""

# Check if we're in the project root
if [[ ! -f "manage.py" ]]; then
    print_error "This script must be run from the project root directory (where manage.py is located)"
    exit 1
fi

# Check virtual environment
check_venv

# Install/update development dependencies
print_status "Installing/updating development dependencies..."
pip install -r requirements-dev.txt > /dev/null 2>&1
print_success "Development dependencies updated"

echo ""
echo "🔧 DEPENDENCY & ENVIRONMENT CHECKS"
echo "=================================="

# Check required tools
REQUIRED_TOOLS=("python" "pip" "black" "isort" "flake8" "bandit" "pip-audit")
for tool in "${REQUIRED_TOOLS[@]}"; do
    if command_exists "$tool"; then
        print_success "$tool is available"
    else
        print_error "$tool is not available. Please install development dependencies."
        exit 1
    fi
done

echo ""
echo "🎨 CODE FORMATTING CHECKS"
echo "========================="

# Black formatting check
run_test "Black code formatting check" "black --check --diff --line-length=127 ."

# isort import sorting check  
run_test "Import sorting check (isort)" "isort --check-only --diff ."

echo ""
echo "🧹 CODE QUALITY CHECKS"  
echo "======================"

# Flake8 linting - critical errors first
run_test "Flake8 critical errors check" "flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics --exclude=.venv,static"

# Flake8 full linting with warnings
run_test "Flake8 full linting check" "flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics --exclude=.venv,static"

echo ""
echo "🔒 SECURITY CHECKS"
echo "=================="

# pip-audit for dependency vulnerabilities
# Ignore GHSA-4xh5-x5gv-qwph for pip itself - Python 3.12 has PEP 706 protection
run_test "Dependency vulnerability check (pip-audit)" "pip-audit --ignore-vuln GHSA-4xh5-x5gv-qwph"

# Bandit security linting
run_test "Security linting check (bandit)" "bandit -r . -x tests/,venv/,.venv/,static/ -f txt"

echo ""
echo "🧪 UNIT TESTS"
echo "============="

# Set environment variables for testing
export DJANGO_SETTINGS_MODULE=demowebapp.test_settings
export CI=true
export DEBUG=False

# Django system check
run_test "Django system check" "python manage.py check --settings=demowebapp.test_settings"

# Run database migrations (SQLite for local testing)
print_status "Running database migrations..."
python manage.py migrate --settings=demowebapp.test_settings > /dev/null 2>&1
print_success "Database migrations completed"

# Run unit tests with coverage
run_test "Unit tests with coverage" "coverage run --source='.' manage.py test tests --verbosity=1 --settings=demowebapp.test_settings --keepdb --failfast"

# Generate coverage report
print_status "Generating coverage report..."
coverage report --skip-covered
coverage xml > /dev/null 2>&1
print_success "Coverage report generated"

echo ""
echo "🐳 DOCKER BUILD TEST"
echo "==================="

# Docker build test (optional - only if Docker is available)
if command_exists "docker"; then
    run_test "Docker image build test" "docker build -t demo-webapp-test:latest . > /dev/null 2>&1"
    
    # Test Docker image
    run_test "Docker image functionality test" "docker run --rm -e DJANGO_SETTINGS_MODULE=demowebapp.test_settings demo-webapp-test:latest python manage.py check --settings=demowebapp.test_settings"
    
    # Cleanup Docker image
    print_status "Cleaning up Docker test image..."
    docker rmi demo-webapp-test:latest > /dev/null 2>&1
    print_success "Docker test image cleaned up"
else
    print_warning "Docker not available - skipping Docker build test"
    print_warning "This test will run in GitHub Actions with Docker"
fi

echo ""
echo "📊 SUMMARY"
echo "=========="
echo "Total tests run: $TOTAL_TESTS"
echo "Tests passed: $TESTS_PASSED"
echo "Tests failed: $TESTS_FAILED"

if [[ $TESTS_FAILED -eq 0 ]]; then
    print_success "🎉 All checks passed! Your code is ready to commit."
    echo ""
    echo "💡 Next steps:"
    echo "   git add ."
    echo "   git commit -m 'Your commit message'"
    echo "   git push"
    exit 0
else
    print_error "💥 $TESTS_FAILED check(s) failed. Please fix the issues before committing."
    echo ""
    echo "💡 Common fixes:"
    echo "   • Run 'black . --line-length=127' to fix formatting issues"
    echo "   • Run 'isort .' to fix import sorting"
    echo "   • Check flake8 output above for code quality issues"
    echo "   • Review security issues reported by bandit and pip-audit"
    echo "   • Fix failing unit tests"
    exit 1
fi
