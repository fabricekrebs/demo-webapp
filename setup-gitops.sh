#!/bin/bash

# GitOps Setup Script for demo-webapp
# This script helps set up the semantic versioning workflow

set -e

echo "🚀 Setting up GitOps workflow for demo-webapp"
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check prerequisites
echo "Checking prerequisites..."

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    print_error "Please run this script from the demo-webapp root directory"
    exit 1
fi

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    print_warning "kubectl not found. Please install kubectl to manage AKS clusters"
else
    print_status "kubectl found"
fi

# Check if flux is installed
if ! command -v flux &> /dev/null; then
    print_warning "flux CLI not found. Please install flux CLI to manage GitOps"
else
    print_status "flux CLI found"
fi

# Check if az CLI is installed
if ! command -v az &> /dev/null; then
    print_warning "Azure CLI not found. Please install Azure CLI"
else
    print_status "Azure CLI found"
fi

echo ""
echo "📋 Setup Checklist"
echo "=================="

# GitHub Secrets
echo ""
print_info "1. GitHub Repository Secrets"
echo "   Add these secrets to your GitHub repository:"
echo "   - AZURE_CLIENT_ID"
echo "   - AZURE_TENANT_ID" 
echo "   - AZURE_SUBSCRIPTION_ID"
echo "   - GITHUB_TOKEN"

# Azure permissions
echo ""
print_info "2. Azure Service Principal Permissions"
echo "   Ensure your service principal has:"
echo "   - AcrPush role on container registry"
echo "   - Contributor role on resource groups"

# Flux setup
echo ""
print_info "3. Flux Installation"
echo "   Install Flux configuration on your AKS cluster:"
echo ""
echo "   kubectl apply -f flux/aks-demo-webapp.yaml"
echo ""
echo "   This creates both development and production environments."

# Branch setup
echo ""
print_info "4. Branch Configuration"
echo "   Create and push develop branch:"
echo "   git checkout -b develop"
echo "   git push -u origin develop"

# Test the workflow
echo ""
print_info "5. Test the Workflow"
echo "   Create a test commit:"
echo "   git commit --allow-empty -m \"feat: test semantic versioning\""
echo "   git push"

echo ""
echo "🔧 Quick Commands"
echo "================="
echo ""
echo "# Test Kustomize overlays locally:"
echo "kustomize build manifests/overlays/development"
echo "kustomize build manifests/overlays/production"
echo ""
echo "# Check semantic release (dry run):"
echo "npx semantic-release --dry-run"
echo ""
echo "# Monitor Flux deployments:"
echo "flux get sources git"
echo "flux get kustomizations"
echo ""
echo "# Check application status:"
echo "kubectl get pods -n demo-webapp-dev    # Development"
echo "kubectl get pods -n demo-webapp        # Production"

echo ""
print_status "Setup guide completed! 🎉"
print_info "Read DEPLOYMENT.md for detailed documentation"

# Optional: Create develop branch if it doesn't exist
read -p "Do you want to create and push the develop branch now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if git show-ref --verify --quiet refs/heads/develop; then
        print_warning "develop branch already exists"
    else
        print_info "Creating develop branch..."
        git checkout -b develop
        git push -u origin develop
        print_status "develop branch created and pushed"
    fi
fi

echo ""
echo "Happy deploying! 🚀"
