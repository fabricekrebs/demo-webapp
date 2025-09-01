#!/bin/bash

# Auto-fix Common Code Quality Issues
# This script automatically fixes common formatting and quality issues

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}🔧 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

echo "🛠️  Auto-fix Code Quality Issues"
echo "================================"

# Check if in project root
if [[ ! -f "manage.py" ]]; then
    echo "❌ Run this script from the project root directory"
    exit 1
fi

# Activate venv if needed
if [[ "$VIRTUAL_ENV" == "" && -f ".venv/bin/activate" ]]; then
    print_warning "Activating virtual environment..."
    source .venv/bin/activate
fi

# Auto-fix code formatting with Black (comprehensive)
print_status "Fixing code formatting with Black (all Python files)..."
black . --line-length=127 --exclude='.venv|venv|__pycache__|.git'
print_success "Code formatting fixed"

# Auto-fix import sorting with isort (comprehensive)
print_status "Fixing import sorting with isort (all Python files)..."
isort . --skip-glob='*.venv*' --skip-glob='*venv*' --skip-glob='*__pycache__*'
print_success "Import sorting fixed"

# Show remaining issues that need manual fixing
print_status "Checking for remaining issues..."

echo ""
echo "📋 Remaining issues to fix manually:"
echo "====================================="

# Check for remaining flake8 issues
echo "🧹 Flake8 issues:"
if ! flake8 . --max-line-length=127 --exclude=.venv,venv,__pycache__,.git --count --statistics; then
    echo ""
    echo "💡 Common fixes needed:"
    echo "   • Remove unused imports (F401): Delete import lines that aren't used"
    echo "   • Remove unused variables (F841): Delete variables that are assigned but never used"
    echo "   • Fix f-strings (F541): Remove f prefix if no {} placeholders, or add variables"
    echo "   • Fix line length (E501): Break long lines or use shorter variable names"
    echo "   • Fix import order (E402): Move imports to top of file"
    echo ""
    echo "🔧 To fix automatically where possible:"
    echo "   autoflake --remove-all-unused-imports --remove-unused-variables --in-place --recursive ."
else
    echo "   No flake8 issues found!"
fi

echo ""
echo "🔒 Security issues (review manually):"
if ! bandit -r . -x tests/,venv/,.venv/,static/ -f txt -ll; then
    echo "   Please review security issues above"
else
    echo "   No high-severity security issues found"
fi

echo ""
echo "🧪 Test your changes:"
echo "   ./quick-check.sh        # Quick validation"
echo "   ./pre-commit-check.sh   # Full validation"

print_success "Auto-fixes applied! Review any remaining issues above."
