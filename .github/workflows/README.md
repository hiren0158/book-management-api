# GitHub Actions Setup Guide

## Workflows Overview

### 1. CI Workflow (ci.yml)
Runs on every push and PR to `main` or `develop` branches.

**Jobs:**
- **Lint**: Code formatting (black), linting (flake8), type checking (mypy)
- **Test**: Run all tests with PostgreSQL service
- **Security**: Security scanning with bandit

### 2. Tests Workflow (tests.yml)
Comprehensive testing suite.

**Jobs:**
- **Unit Tests**: Isolated tests with coverage reporting
- **Integration Tests**: Full stack tests with database
- **Test Report**: Summary of all test results

Coverage reports are uploaded to Codecov (requires setup).

### 3. Deploy Workflow (deploy.yml)
Automated deployment pipeline.

**Jobs:**
- **Build**: Build and push Docker image to GitHub Container Registry
- **Deploy Staging**: Deploy to staging (on `develop` branch)
- **Deploy Production**: Deploy to production (on version tags)
- **Deploy Docker Hub**: Push to Docker Hub (optional)

## Required Secrets

Add these secrets in GitHub repository settings:

### For Docker Hub deployment (optional):
- `DOCKERHUB_USERNAME`: Your Docker Hub username
- `DOCKERHUB_TOKEN`: Docker Hub access token

### For AWS deployment (example):
- `AWS_ACCESS_KEY_ID`: AWS access key
- `AWS_SECRET_ACCESS_KEY`: AWS secret key

### For SSH deployment (example):
- `SSH_PRIVATE_KEY`: SSH private key for deployment server
- `DEPLOY_HOST`: Deployment server hostname
- `DEPLOY_USER`: SSH username

## Usage

### Running tests locally
```bash
poetry run pytest tests/unit/ -v
poetry run pytest tests/integration/ -v
```

### Creating a release
```bash
git tag v1.0.0
git push origin v1.0.0
```

### Manual workflow trigger
Go to Actions tab → Select workflow → Run workflow

## Deployment Customization

Edit `.github/workflows/deploy.yml` to configure:
- Target cloud provider (AWS, GCP, Azure, etc.)
- Deployment method (ECS, Kubernetes, VM, etc.)
- Environment URLs

## Environments

Configure in GitHub Settings → Environments:
- **staging**: Requires no approval
- **production**: Recommended to require approval

## Status Badges

Add to README.md:
```markdown
![CI](https://github.com/yourusername/book-management-api/workflows/CI/badge.svg)
![Tests](https://github.com/yourusername/book-management-api/workflows/Tests/badge.svg)
![Deploy](https://github.com/yourusername/book-management-api/workflows/Deploy/badge.svg)
```
