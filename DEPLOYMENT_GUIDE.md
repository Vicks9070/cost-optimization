# Datadog Cost Analyzer - Deployment Guide

## Overview

The Datadog Cost Analyzer is a comprehensive tool for analyzing Datadog usage costs and detecting anomalies. This guide covers deployment options and configuration.

## Prerequisites

- Python 3.8+
- Datadog API Key and Application Key
- Access to Datadog Usage API
- (Optional) Docker for containerized deployment

## Installation Options

### 1. Local Installation

```bash
# Clone the repository
git clone <repository-url>
cd cost-optimization

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### 2. Docker Deployment

```bash
# Build the Docker image
docker build -t datadog-cost-analyzer .

# Run with environment variables
docker run -d \
  -e DATADOG_API_KEY=your_api_key \
  -e DATADOG_APP_KEY=your_app_key \
  -e DATADOG_SITE=datadoghq.com \
  -p 5000:5000 \
  datadog-cost-analyzer
```

### 3. GitLab CI/CD Pipeline

The project includes a comprehensive GitLab CI/CD pipeline with:

- **Test Stage**: Unit tests, linting, security scanning
- **Build Stage**: Docker image building and registry push
- **Deploy Stage**: Staging and production deployments
- **Monitoring**: Performance and security monitoring

## Configuration

### Environment Variables

```bash
# Required
DATADOG_API_KEY=your_datadog_api_key
DATADOG_APP_KEY=your_datadog_application_key
DATADOG_SITE=datadoghq.com  # or datadoghq.eu, us3.datadoghq.com, etc.

# Optional
FLASK_ENV=production
LOG_LEVEL=INFO
CONFIG_FILE=config/config.yaml
```

### Configuration File

Create `config/config.yaml`:

```yaml
datadog:
  api_key: "${DATADOG_API_KEY}"
  app_key: "${DATADOG_APP_KEY}"
  site: "${DATADOG_SITE:-datadoghq.com}"

analysis:
  default_weeks: 8
  anomaly_threshold: 2.0
  methods:
    - z_score
    - iqr
    - isolation_forest
    - seasonal_decomposition
    - week_over_week

visualization:
  theme: plotly_white
  export_formats:
    - html
    - json
    - csv

web:
  host: "0.0.0.0"
  port: 5000
  debug: false

logging:
  level: INFO
  file: logs/cost_analyzer.log
```

## Usage

### Command Line Interface

```bash
# Test connection
python -m datadog_cost_analyzer.cli test-connection

# Run analysis
python -m datadog_cost_analyzer.cli analyze --weeks 8

# Detect anomalies only
python -m datadog_cost_analyzer.cli detect-anomalies --weeks 12

# Create Datadog notebook
python -m datadog_cost_analyzer.cli create-notebook --weeks 8 --title "Weekly Cost Review"

# List existing notebooks
python -m datadog_cost_analyzer.cli list-notebooks --tags cost-analysis

# Start web interface
python -m datadog_cost_analyzer.cli serve
```

### Web Interface

Access the web interface at `http://localhost:5000` for:

- Interactive dashboards
- Real-time cost analysis
- Anomaly detection results
- Downloadable reports

### API Endpoints

- `GET /api/health` - Health check
- `GET /api/cost-data` - Retrieve cost data
- `POST /api/analyze` - Run cost analysis
- `GET /api/anomalies` - Get anomaly detection results
- `GET /api/visualizations` - Generate charts

## Datadog Notebook Integration

### Automatic Notebook Creation

The tool can automatically create Datadog notebooks with:

- Executive summary of cost anomalies
- Detailed analysis by category and method
- Cost trend visualizations
- Investigation queries and recommendations
- Action items for cost optimization

### Notebook Features

- **8 Cell Types**: Comprehensive analysis coverage
- **Auto-updating**: Can update existing notebooks
- **Tagging**: Organize notebooks with custom tags
- **Time-based Analysis**: Configurable analysis periods

## Monitoring and Alerting

### Health Checks

The application provides health check endpoints for monitoring:

```bash
curl http://localhost:5000/api/health
```

### Logging

Structured logging with configurable levels:

- Application logs: `logs/cost_analyzer.log`
- Access logs: Console output
- Error tracking: Structured JSON format

### Performance Metrics

Monitor key metrics:

- Analysis execution time
- API response times
- Memory usage
- Anomaly detection accuracy

## Security Considerations

### API Key Management

- Store API keys in environment variables
- Use secrets management in production
- Rotate keys regularly
- Limit API key permissions

### Network Security

- Use HTTPS in production
- Implement rate limiting
- Configure CORS appropriately
- Use reverse proxy (nginx/Apache)

### Data Privacy

- Cost data is processed in memory
- No persistent storage of sensitive data
- Configurable data retention policies
- Audit logging for compliance

## Troubleshooting

### Common Issues

1. **API Connection Errors**
   ```bash
   python -m datadog_cost_analyzer.cli test-connection
   ```

2. **Configuration Issues**
   ```bash
   python -m datadog_cost_analyzer.cli validate-config
   ```

3. **Memory Issues with Large Datasets**
   - Reduce analysis period
   - Increase container memory limits
   - Use data sampling options

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
python -m datadog_cost_analyzer.cli analyze --verbose
```

## Production Deployment

### Recommended Architecture

```
[Load Balancer] -> [Reverse Proxy] -> [Cost Analyzer] -> [Datadog API]
                                   -> [Monitoring]
                                   -> [Logging]
```

### Scaling Considerations

- Horizontal scaling: Multiple instances behind load balancer
- Vertical scaling: Increase memory for large datasets
- Caching: Redis for API response caching
- Database: Optional for historical data storage

### Backup and Recovery

- Configuration files backup
- Log rotation and archival
- Container image versioning
- Disaster recovery procedures

## Support and Maintenance

### Regular Tasks

- Monitor API usage limits
- Review anomaly detection accuracy
- Update dependencies
- Performance optimization

### Updates

- Follow semantic versioning
- Test in staging environment
- Gradual rollout strategy
- Rollback procedures

## License

This project is licensed under the MIT License. See LICENSE file for details.