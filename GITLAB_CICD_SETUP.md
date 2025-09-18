# GitLab CI/CD Setup Guide

## Overview

This document provides comprehensive instructions for setting up GitLab CI/CD for the Datadog Cost Analyzer project. The pipeline automatically validates, tests, builds, and can deploy the application whenever new commits are pushed.

## Pipeline Stages

### 1. **Validate** 🔍
- **validate_config**: Validates YAML configuration files and application settings
- **validate_imports**: Ensures all Python imports work correctly

### 2. **Test** 🧪
- **unit_tests**: Runs comprehensive unit test suite with coverage reporting
- **integration_tests**: Tests API connectivity and runs demo (with mock data if no real credentials)
- **code_quality**: Runs code formatting, linting, and type checking

### 3. **Build** 🏗️
- **build_package**: Creates Python package distribution
- **build_docker**: Builds and pushes Docker image to GitLab Container Registry

### 4. **Security** 🔒
- **security_scan**: Scans for security vulnerabilities in dependencies and code

### 5. **Deploy** 🚀
- **deploy_staging**: Manual deployment to staging environment
- **deploy_production**: Manual deployment to production environment

## Required GitLab CI/CD Variables

You need to configure the following variables in your GitLab project settings under **Settings > CI/CD > Variables**:

### 🔑 **Datadog API Credentials**

#### For Testing/Development (Optional but Recommended)
```
DD_API_KEY_TEST
Type: Variable
Protected: ✅ Yes
Masked: ✅ Yes
Description: Datadog API Key for testing environment
Value: your_test_api_key_here
```

```
DD_APP_KEY_TEST
Type: Variable
Protected: ✅ Yes
Masked: ✅ Yes
Description: Datadog Application Key for testing environment
Value: your_test_app_key_here
```

#### For Staging Environment
```
DD_API_KEY_STAGING
Type: Variable
Protected: ✅ Yes
Masked: ✅ Yes
Environment Scope: staging
Description: Datadog API Key for staging environment
Value: your_staging_api_key_here
```

```
DD_APP_KEY_STAGING
Type: Variable
Protected: ✅ Yes
Masked: ✅ Yes
Environment Scope: staging
Description: Datadog Application Key for staging environment
Value: your_staging_app_key_here
```

#### For Production Environment
```
DD_API_KEY_PRODUCTION
Type: Variable
Protected: ✅ Yes
Masked: ✅ Yes
Environment Scope: production
Description: Datadog API Key for production environment
Value: your_production_api_key_here
```

```
DD_APP_KEY_PRODUCTION
Type: Variable
Protected: ✅ Yes
Masked: ✅ Yes
Environment Scope: production
Description: Datadog Application Key for production environment
Value: your_production_app_key_here
```

### 📋 **Variable Configuration Summary**

| Variable Name | Required | Protected | Masked | Environment | Description |
|---------------|----------|-----------|--------|-------------|-------------|
| `DD_API_KEY_TEST` | Optional | ✅ | ✅ | All | Test environment API key |
| `DD_APP_KEY_TEST` | Optional | ✅ | ✅ | All | Test environment App key |
| `DD_API_KEY_STAGING` | Required* | ✅ | ✅ | staging | Staging environment API key |
| `DD_APP_KEY_STAGING` | Required* | ✅ | ✅ | staging | Staging environment App key |
| `DD_API_KEY_PRODUCTION` | Required* | ✅ | ✅ | production | Production environment API key |
| `DD_APP_KEY_PRODUCTION` | Required* | ✅ | ✅ | production | Production environment App key |

*Required only if you plan to use the deployment stages

## Setting Up Variables in GitLab

### Step-by-Step Instructions:

1. **Navigate to your GitLab project**
2. **Go to Settings > CI/CD**
3. **Expand the "Variables" section**
4. **Click "Add Variable" for each required variable**

### For each variable:
- **Key**: Use the exact variable name from the table above
- **Value**: Your actual Datadog API/App key
- **Type**: Variable
- **Environment scope**: Set appropriately (staging/production) or leave as "All environments" for test keys
- **Protect variable**: ✅ **Enable** (ensures variable is only available to protected branches/tags)
- **Mask variable**: ✅ **Enable** (hides the value in job logs)

## Pipeline Behavior

### 🔄 **Automatic Triggers**
The pipeline runs automatically on:
- **All branch pushes** (runs validate, test, build, security stages)
- **Merge requests** (runs validate, test, build, security stages)
- **Main branch pushes** (includes deployment options)

### 🚫 **What Happens Without API Keys**
- **Validation and unit tests**: ✅ Run normally (don't require API keys)
- **Integration tests**: ⚠️ Skip API connection tests, run demo with mock data
- **Build stages**: ✅ Run normally
- **Security scans**: ✅ Run normally
- **Deployment**: ❌ Fail if API keys not configured

### 📊 **Artifacts and Reports**
The pipeline generates:
- **Test coverage reports** (HTML and XML)
- **Security scan reports** (JSON format)
- **Built packages** (Python wheel and source distribution)
- **Docker images** (pushed to GitLab Container Registry)
- **Pipeline execution reports** (Markdown summary)

## Security Best Practices

### 🔒 **API Key Security**
1. **Never commit API keys** to the repository
2. **Use different keys** for different environments
3. **Enable "Protected" and "Masked"** for all API key variables
4. **Rotate keys regularly** and update in GitLab variables
5. **Use minimal permissions** for API keys (read-only for cost data)

### 🛡️ **Pipeline Security**
1. **Protected branches**: Configure main branch as protected
2. **Approval rules**: Require approvals for production deployments
3. **Environment protection**: Protect production environment in GitLab
4. **Audit logs**: Monitor variable access and pipeline executions

## Troubleshooting

### ❌ **Common Issues**

#### "DD_API_KEY not found" Error
**Solution**: Ensure variables are properly configured with correct names and scopes

#### Integration Tests Failing
**Solution**: This is expected without real API keys. Check that unit tests pass.

#### Docker Build Failing
**Solution**: Ensure GitLab Container Registry is enabled for your project

#### Deployment Jobs Not Appearing
**Solution**: Deployment jobs only appear on the main branch and are manual

### 🔍 **Debugging Steps**
1. **Check variable configuration** in Settings > CI/CD > Variables
2. **Verify branch protection** settings
3. **Review job logs** for specific error messages
4. **Test locally** using the same commands as in the pipeline

## Local Development

### Running Pipeline Commands Locally
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
export PYTHONPATH=src
python -m pytest tests/ -v

# Validate configuration
python -m datadog_cost_analyzer.cli validate-config

# Run demo
python demo.py

# Code quality checks
black --check src/ tests/
flake8 src/ tests/ --max-line-length=100
```

## Customization

### 🎛️ **Modifying the Pipeline**
The `.gitlab-ci.yml` file can be customized for your specific needs:

- **Add new test stages** for additional validation
- **Modify deployment targets** for your infrastructure
- **Add notification steps** (Slack, email, etc.)
- **Integrate with external tools** (Jira, monitoring systems)

### 📝 **Environment-Specific Configuration**
Create environment-specific configuration files:
- `config/staging.yaml`
- `config/production.yaml`

Update the pipeline to use appropriate configs per environment.

## Monitoring and Alerts

### 📈 **Pipeline Monitoring**
- **Pipeline success/failure rates**
- **Test coverage trends**
- **Security scan results**
- **Deployment frequency**

### 🚨 **Recommended Alerts**
- **Pipeline failures** on main branch
- **Security vulnerabilities** detected
- **Test coverage** drops below threshold
- **Deployment failures**

## Next Steps

1. **Configure the required variables** in GitLab
2. **Test the pipeline** by pushing a commit
3. **Review the generated reports** and artifacts
4. **Set up environment protection** for production
5. **Configure notifications** for pipeline events
6. **Monitor pipeline performance** and optimize as needed

## Support

For issues with the CI/CD pipeline:
1. Check the troubleshooting section above
2. Review GitLab CI/CD documentation
3. Check project-specific logs and artifacts
4. Contact the development team for assistance