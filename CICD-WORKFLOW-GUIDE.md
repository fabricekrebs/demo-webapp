# CI/CD Workflow Guide

This repository uses a GitOps-friendly CI/CD setup with separate workflows for development and production.

## Workflows Overview

### 1. CI Tests (`ci-tests.yml`)
- **Triggers**: All pushes and PRs to any branch
- **Purpose**: Runs unit tests, linting, and validation
- **Always runs first** before other workflows proceed

### 2. Development Build (`development-build.yml`)  
- **Triggers**: Push to `develop` branch, PRs to `develop`
- **Purpose**: Creates development container images
- **Container Tags**:
  - `develop-{short-sha}` (for regular commits)
  - `pr-{number}-{short-sha}` (for PRs)
  - `develop-latest` (always points to latest develop build)

### 3. Production Release (`production-release.yml`)
- **Triggers**: Push to `main` branch (usually from PR merge)
- **Purpose**: Creates semantic versions and production containers
- **Semantic Versioning**: Uses conventional commits to determine version bumps
- **Container Tags**:
  - `v1.2.3` (semantic version)
  - `latest` (always points to latest production release)

## Recommended Git Flow

### Development Work
1. Create feature branch from `develop`
2. Make changes using [conventional commits](https://www.conventionalcommits.org/)
3. Push to feature branch (triggers CI tests)
4. Create PR to `develop` (triggers CI + development build)
5. Merge PR (triggers development build with `develop-latest` tag)

### Production Release
1. Create PR from `develop` to `main`
2. Merge PR (triggers CI tests + semantic release + production build)
3. Semantic release creates git tag (e.g., `v1.2.3`) based on conventional commits
4. Production container image is built and tagged with semantic version

## Container Registry

All images are pushed to: `acritalynorth01.azurecr.io/demo-webapp`

### Available Tags
- `develop-latest` - Latest development build from develop branch
- `develop-{sha}` - Specific development builds
- `v{major}.{minor}.{patch}` - Production releases (semantic versions)
- `latest` - Latest production release

## GitOps Integration

### Current Setup (In This Repo)
- ❌ Manifests are currently in this repository
- ❌ Workflows update manifests in the same repo (anti-pattern)
- ❌ Flux configs point to application repository

### Recommended Setup
1. **Create separate GitOps repository** (e.g., `demo-webapp-gitops`)
2. **Move these directories to GitOps repo**:
   - `flux/` - Flux configurations
   - `manifests/` - Kubernetes manifests
3. **Update Flux to point to GitOps repo**
4. **Set up automated manifest updates**:
   - Use repository dispatch or webhook to update GitOps repo when new versions are built
   - Update `kustomization.yaml` with new image tags

### Example GitOps Repository Structure
```
demo-webapp-gitops/
├── clusters/
│   └── aks-demo/
├── apps/
│   └── demo-webapp/
│       ├── base/
│       │   ├── kustomization.yaml
│       │   ├── deployment.yaml
│       │   └── ...
│       └── overlays/
│           ├── development/
│           └── production/
└── flux-system/
```

## Environment Configuration

### Development Environment
- **Branch**: `develop`
- **Image**: `develop-latest`
- **Namespace**: `demo-webapp-dev`
- **Update Frequency**: Automatic on every develop push

### Production Environment  
- **Branch**: `main`
- **Image**: Semantic versions (e.g., `v1.2.3`)
- **Namespace**: `demo-webapp-prod`
- **Update Frequency**: Manual promotion of specific versions

## Conventional Commits

Use conventional commit format to enable automatic semantic versioning:

```bash
feat: add user authentication    # Minor version bump (1.0.0 → 1.1.0)
fix: resolve login issue         # Patch version bump (1.1.0 → 1.1.1)
feat!: redesign API             # Major version bump (1.1.1 → 2.0.0)
```

### Commit Types
- `feat:` - New feature (minor version bump)
- `fix:` - Bug fix (patch version bump)
- `perf:` - Performance improvement (patch version bump)
- `BREAKING CHANGE:` or `!` - Breaking change (major version bump)
- `chore:`, `docs:`, `style:`, `refactor:`, `test:` - No version bump

## Secrets Configuration

Ensure these secrets are configured in your GitHub repository:

```bash
DEMOWEBAPP_AZURE_CLIENT_ID      # Azure Service Principal Client ID
DEMOWEBAPP_AZURE_TENANT_ID      # Azure Tenant ID
DEMOWEBAPP_AZURE_SUBSCRIPTION_ID # Azure Subscription ID
```

## Next Steps

1. **✅ Current workflows are now properly separated**
2. **🔄 Consider creating separate GitOps repository**
3. **🔄 Set up automated GitOps manifest updates**
4. **🔄 Configure Flux to use GitOps repository**
