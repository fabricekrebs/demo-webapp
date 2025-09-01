#!/bin/bash

# Quick Quality Check Script
# A faster version of pre-commit checks for quick validation during development
# Run this for rapid feedback, use pre-commit-check.sh for full CI simulation

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m' 
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

echo "⚡ Quick Quality Check"
echo "====================="

# Check if in project root
if [[ ! -f "manage.py" ]]; then
    print_error "Run this script from the project root directory"
    exit 1
fi

# Activate venv if needed
if [[ "$VIRTUAL_ENV" == "" && -f ".venv/bin/activate" ]]; then
    print_warning "Activating virtual environment..."
    source .venv/bin/activate
fi

FAILED=0

# Quick format check (don't show diff for speed)
print_status "Checking code formatting..."
if black --check --quiet --line-length=127 --exclude='.venv|static' .; then
    print_success "Code formatting is correct"
else
    print_error "Code needs formatting. Run: black . --line-length=127 --exclude='.venv|static'"
    FAILED=1
fi

# Quick import check
print_status "Checking import sorting..."
if isort --check-only --quiet --skip=.venv --skip=static .; then
    print_success "Import sorting is correct"
else
    print_error "Imports need sorting. Run: isort ."
    FAILED=1
fi

# Critical linting errors only
print_status "Checking for critical code issues..."
if flake8 . --select=E9,F63,F7,F82 --exclude=.venv,static --quiet; then
    print_success "No critical code issues found"
else
    print_error "Critical code issues found. Check output above."
    FAILED=1
fi

# Django system check
print_status "Checking Django configuration..."
export DJANGO_SETTINGS_MODULE=demowebapp.test_settings
if python manage.py check --settings=demowebapp.test_settings > /dev/null 2>&1; then
    print_success "Django configuration is valid"
else
    print_error "Django configuration issues found"
    FAILED=1
fi

# Quick security scan (exclude non-critical)
print_status "Quick security check..."
if bandit -r . -x tests/,venv/,.venv/,static/ -ll -q > /dev/null 2>&1; then
    print_success "No high-severity security issues found"
else
    print_warning "Security issues found. Run full check for details."
fi

echo ""
if [[ $FAILED -eq 0 ]]; then
    print_success "🎉 Quick checks passed! Consider running './pre-commit-check.sh' for full validation."
else
    print_error "💥 Issues found. Fix them and run again, or use './pre-commit-check.sh' for detailed output."
    exit 1
fi
