# GitOps Deployment Guide

This repository uses semantic versioning with GitOps for automated deployments to AKS clusters.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Development   │    │   GitHub Actions │    │   Production    │
│   Environment   │    │   CI/CD Pipeline │    │   Environment   │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │    AKS      │◄┼────┤ │  Semantic   │ ├────┤►│    AKS      │ │
│ │  Cluster    │ │    │ │  Versioning │ │    │ │  Cluster    │ │
│ │   (Dev)     │ │    │ │   + Build   │ │    │ │  (Prod)     │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
│                 │    │                 │    │                 │
│ Flux watches    │    │ Builds & Tags   │    │ Flux watches    │
│ 'develop'       │    │ Container       │    │ 'main' branch   │
│ branch          │    │ Images          │    │ for releases    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Workflow

### Development Flow
1. **Feature Development**: Create feature branches from `develop`
2. **Pull Request**: Create PR to `develop` branch
3. **CI Testing**: Automated tests run on PR
4. **Merge to Develop**: After PR approval, merge to `develop`
5. **Auto Deploy**: Flux automatically deploys `develop` to dev environment

### Production Release Flow
1. **Release Preparation**: When ready for production, create PR from `develop` to `main`
2. **Semantic Release**: On merge to `main`, semantic-release creates version tag (e.g., `v1.2.3`)
3. **Container Build**: GitHub Actions builds and tags container image
4. **Manifest Update**: Manifests updated with new version tag
5. **Production Deploy**: Flux detects manifest changes and deploys to production

## 📋 Prerequisites

### 1. GitHub Secrets Configuration
Add these secrets to your GitHub repository:

```bash
# Azure Authentication
AZURE_CLIENT_ID=<your-azure-client-id>
AZURE_TENANT_ID=<your-azure-tenant-id>
AZURE_SUBSCRIPTION_ID=<your-azure-subscription-id>

# GitHub Token (for semantic-release)
GITHUB_TOKEN=<your-github-token>
```

### 2. Azure Container Registry
Ensure your GitHub Actions service principal has:
- `AcrPush` role on the container registry
- `Contributor` role on the resource group

### 3. AKS Clusters Setup
You need two AKS clusters (or namespaces):
- **Development**: For testing and validation
- **Production**: For stable releases

## 🔧 Flux Configuration

### Dual Environment Setup
Apply to your AKS cluster (this creates both dev and production environments):
```bash
kubectl apply -f flux/aks-demo-webapp.yaml
```

This single file configures both:
- **Development environment** (watches `develop` branch → `demo-webapp-dev` namespace)
- **Production environment** (watches `main` branch → `demo-webapp` namespace)

## 📦 Semantic Versioning

This project uses [Conventional Commits](https://conventionalcommits.org/) for automatic version determination:

### Commit Message Format
```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Examples
```bash
# Patch version bump (1.0.0 → 1.0.1)
git commit -m "fix: resolve authentication issue"

# Minor version bump (1.0.0 → 1.1.0)
git commit -m "feat: add user profile endpoint"

# Major version bump (1.0.0 → 2.0.0)
git commit -m "feat!: redesign API authentication

BREAKING CHANGE: API now requires JWT tokens instead of API keys"
```

### Version Tags
- **Development builds**: `develop-{commit-sha}`
- **Release candidates**: `v1.2.3-rc.1`
- **Production releases**: `v1.2.3`

## 🗂️ Directory Structure

```
manifests/
├── base/                    # Base Kubernetes manifests
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── configmap.yaml
│   ├── namespace.yaml
│   ├── secretproviderclass.yaml
│   └── kustomization.yaml
└── overlays/
    ├── development/         # Development-specific configurations
    │   ├── kustomization.yaml
    │   ├── deployment-patch.yaml
    │   └── ingress-patch.yaml
    └── production/          # Production-specific configurations
        ├── kustomization.yaml
        └── deployment-patch.yaml

flux/
└── aks-demo-webapp.yaml     # Complete Flux config for both environments
```

## 🔍 Environment Differences

| Aspect | Development | Production |
|--------|-------------|------------|
| **Namespace** | `demo-webapp-dev` | `demo-webapp` |
| **Replicas** | 2 | 4 |
| **Resources** | 128Mi/100m CPU | 256Mi/250m CPU |
| **Debug Mode** | Enabled | Disabled |
| **Image Tag** | `develop-latest` | Semantic version |
| **Flux Interval** | 1 minute | 10 minutes |

## 🚦 Deployment Process

### Manual Release (if needed)
```bash
# Create and push a tag manually
git tag v1.0.0
git push origin v1.0.0

# This will trigger the release workflow
```

### Rollback Process
```bash
# Find the previous version
git tag -l | sort -V

# Update manifests to previous version
sed -i 's/newTag: v1.2.3/newTag: v1.2.2/' manifests/base/kustomization.yaml
git add manifests/
git commit -m "chore: rollback to v1.2.2"
git push
```

## 🔍 Monitoring Deployments

### Check GitHub Actions
1. Go to Actions tab in GitHub
2. Monitor "Semantic Release" workflow
3. Check deployment summary

### Monitor Flux
```bash
# Check Flux status
flux get sources git
flux get kustomizations

# Watch deployment
kubectl get deployments -n demo-webapp-dev --watch
kubectl get deployments -n demo-webapp --watch
```

### Check Application Health
```bash
# Development
kubectl get pods -n demo-webapp-dev
curl http://dev.demo-webapp.local/health/

# Production  
kubectl get pods -n demo-webapp
curl http://demo-webapp.com/health/
```

## 🐛 Troubleshooting

### Common Issues

1. **Semantic release fails**
   - Ensure conventional commit format
   - Check GitHub token permissions

2. **Container build fails**
   - Verify Azure credentials
   - Check ACR permissions

3. **Flux not deploying**
   - Check Flux logs: `flux logs`
   - Verify GitRepository and Kustomization status

4. **Application not starting**
   - Check pod logs: `kubectl logs -n <namespace> -l app=demo-webapp`
   - Verify environment variables and secrets

### Useful Commands
```bash
# View semantic-release dry run
npx semantic-release --dry-run

# Test Kustomize locally
kustomize build manifests/overlays/development
kustomize build manifests/overlays/production

# Check image versions
docker images | grep demo-webapp
az acr repository show-tags --name acritalynorth01 --repository demo-webapp
```

## 🔒 Security Best Practices

1. **Use specific version tags** in production (never `latest`)
2. **Enable Pod Security Standards** in AKS
3. **Scan container images** for vulnerabilities
4. **Rotate secrets regularly**
5. **Use Azure Key Vault** for sensitive data
6. **Enable Azure Policy** for compliance

## 📈 Next Steps

- [ ] Add automated security scanning
- [ ] Implement blue-green deployments
- [ ] Add performance testing
- [ ] Set up monitoring and alerting
- [ ] Create disaster recovery procedures
