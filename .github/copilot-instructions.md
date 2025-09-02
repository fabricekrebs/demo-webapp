# Copilot Coding Agent Instructions

## Repository Overview

This is **demo-webapp**, a Django web application demonstrating application modernization and Azure service integrations. The project showcases task management functionality with chatbot integration using Azure AI Foundry, Application Insights monitoring, and comprehensive CI/CD pipelines.

**Key Details:**
- **Language:** Python 3.12
- **Framework:** Django 5.2.5 with Django REST Framework
- **Database:** PostgreSQL (production), SQLite (local testing)
- **Size:** ~42 Python files, 103 comprehensive tests
- **Target Runtime:** Azure Container Apps, AKS, Docker containers

## Critical Build & Test Instructions

### Environment Setup (ALWAYS REQUIRED)
```bash
# ALWAYS run these commands first in this exact order:
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install --upgrade pip
pip install --timeout 300 -r requirements.txt
pip install --timeout 300 -r requirements-dev.txt  # For development work
```

**Note:** If pip install times out, retry the command. Network connectivity can be intermittent.

### Running Tests (Choose Method Based on Environment)
**For local development (RECOMMENDED):**
```bash
# ALWAYS unset CI environment variables for local testing
unset CI GITHUB_ACTIONS
export DJANGO_SETTINGS_MODULE=demowebapp.test_settings
python manage.py test tests --verbosity=2
```

**For CI simulation (requires PostgreSQL):**
```bash
export DJANGO_SETTINGS_MODULE=demowebapp.test_settings
export CI=true
python manage.py test tests --verbosity=2
```

**IMPORTANT:** Tests require `DJANGO_SETTINGS_MODULE=demowebapp.test_settings`. Never run tests without this setting.

### Code Quality Checks
```bash
# Quick validation (fast feedback during development):
./quick-check.sh

# Full pre-commit validation (run before pushing):
./pre-commit-check.sh
```

### Database Operations
```bash
# ALWAYS run migrations after model changes:
export DJANGO_SETTINGS_MODULE=demowebapp.test_settings
python manage.py makemigrations tasks
python manage.py migrate
```

### Local Development Server
```bash
# For local development with PostgreSQL:
docker run -p 5432:5432 --name postgres -e POSTGRES_PASSWORD=mypassword -d postgres:16.8
python manage.py runserver

# Server runs on http://127.0.0.1:8000/
```

## Project Architecture & Key Locations

### Main Components
- **`demowebapp/`** - Django project configuration, settings, URLs
  - `settings.py` - Main configuration file
  - `test_settings.py` - Test-specific settings (SQLite vs PostgreSQL)
  - `urls.py` - Root URL configuration
- **`tasks/`** - Primary Django app for task management
  - `models.py` - Task, Project, Chat models
  - `views.py` - Business logic and view controllers
  - `serializers.py` - DRF API serialization
- **`api/`** - REST API endpoints and chat functionality
- **`tests/`** - Comprehensive test suite (103 tests covering all major functionality)

### Configuration Files
- **`pyproject.toml`** - Black (line-length=127), isort, coverage configuration
- **`requirements.txt`** - Production dependencies (Django, Azure SDKs, PostgreSQL)
- **`requirements-dev.txt`** - Development tools (pytest, black, flake8, bandit)
- **`Dockerfile`** - Production container definition (Python 3.12-slim)

### CI/CD & GitOps
- **`.github/workflows/`**:
  - `ci-tests.yml` - Runs on all branches (tests, linting, security, Docker build)
  - `development-build.yml` - Builds containers for develop branch
  - `production-release.yml` - Semantic versioning and production builds
- **`manifests/`** - Kubernetes deployment manifests
- **`flux/`** - GitOps Flux configurations for automated deployments

## Validation Pipelines

### GitHub Actions Workflow (Automatic)
1. **CI Tests** (runs on all pushes/PRs):
   - Unit tests with PostgreSQL service container
   - Black code formatting check (`black --check --line-length=127`)
   - Import sorting check (`isort --check-only`)
   - Flake8 linting (critical errors: E9,F63,F7,F82)
   - Security scanning (`pip-audit`, `bandit`)
   - Docker build verification

2. **Development Build** (develop branch):
   - Creates `develop-latest` and `develop-{sha}` container images

3. **Production Release** (main branch):
   - Semantic versioning with conventional commits
   - Production container tags (`v1.2.3`, `latest`)

### Local Validation Scripts
- **`./quick-check.sh`** - Fast quality checks (30-60 seconds)
- **`./pre-commit-check.sh`** - Full CI simulation (2-5 minutes)
- **`./auto-fix.sh`** - Automatic code formatting fixes

## Common Issues & Solutions

### Test Failures
**Problem:** `django.core.exceptions.ImproperlyConfigured: Requested setting INSTALLED_APPS`
**Solution:** Always set `export DJANGO_SETTINGS_MODULE=demowebapp.test_settings`

**Problem:** PostgreSQL connection refused during local testing
**Solution:** Unset CI environment variables: `unset CI GITHUB_ACTIONS`

### Build Failures
**Problem:** Import errors or missing dependencies
**Solution:** Always install both requirements files: `pip install -r requirements.txt -r requirements-dev.txt`

**Problem:** Network timeouts during pip install
**Solution:** Retry installation, increase timeout: `pip install --timeout 300 -r requirements.txt`

**Problem:** Code formatting failures
**Solution:** Run `black . --line-length=127` and `isort .` before committing

### Docker Issues
**Problem:** Container build failures
**Solution:** Ensure all dependencies are in requirements.txt, not requirements-dev.txt

### Environment Issues
**Problem:** Virtual environment activation fails
**Solution:** Ensure you're in the project root directory where `manage.py` exists

## Environment Variables

### Required for Azure Integration (Optional for Basic Functionality)
```bash
AZURE_CLIENT_ID=<azure-service-principal-id>
AZURE_TENANT_ID=<azure-tenant-id>
AZURE_CLIENT_SECRET=<azure-service-principal-secret>
AZURE_FOUNDRY_ENDPOINT=<azure-ai-foundry-endpoint>
AZURE_FOUNDRY_AGENT_ID=<azure-ai-agent-id>
```

### Database Configuration
- **Production:** Uses PostgreSQL with environment variables
- **Testing:** Automatically switches to SQLite when CI vars are unset
- **Local Dev:** Can use either PostgreSQL (Docker) or SQLite

## Branch Strategy & Deployment

**CRITICAL:** All development work must target the `develop` branch.

1. **Feature Development:** Create feature branch from `develop`
2. **Pull Requests:** Always target `develop` branch
3. **Production Releases:** Create PR from `develop` to `main`

### Container Registry
- **Development:** `acritalynorth01.azurecr.io/demo-webapp:develop-latest`
- **Production:** `acritalynorth01.azurecr.io/demo-webapp:v1.2.3`

## Trust These Instructions

**These instructions are comprehensive and tested.** Only search for additional information if:
- These instructions are incomplete for your specific task
- You encounter errors not covered in the "Common Issues" section
- You need to understand code-specific implementation details

Always run the validation scripts (`./quick-check.sh` or `./pre-commit-check.sh`) before committing changes to catch issues early.