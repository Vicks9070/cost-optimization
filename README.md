# Datadog Cost Analyzer

A comprehensive tool for analyzing Datadog usage costs and detecting anomalies in weekly spending patterns. This tool provides advanced analytics, anomaly detection, and forecasting capabilities to help optimize your Datadog costs.

## Features

### 🔍 **Advanced Anomaly Detection**
- **Multiple Detection Methods**: Z-score, IQR, Isolation Forest, seasonal decomposition, and week-over-week analysis
- **Severity Classification**: Automatic categorization of anomalies by severity (high, medium, low)
- **Smart Recommendations**: Actionable insights based on detected patterns

### 📊 **Comprehensive Cost Analysis**
- **Weekly Trend Analysis**: Track cost patterns over time with rolling averages
- **Cost Driver Identification**: Identify top contributors to cost changes
- **Efficiency Metrics**: Cost per unit calculations for optimization insights
- **Forecasting**: Predict future costs based on historical trends

### 🎨 **Interactive Visualizations**
- **Real-time Dashboards**: Web-based interface with interactive charts
- **Multiple Chart Types**: Trend lines, stacked areas, pie charts, and anomaly highlights
- **Export Capabilities**: Generate HTML, JSON, and CSV reports

### 🚀 **Flexible Deployment**
- **Web Interface**: Full-featured dashboard accessible via browser
- **Command Line Interface**: Scriptable analysis and automation
- **API Endpoints**: RESTful API for integration with other tools

## Quick Start

### Prerequisites

- Python 3.8 or higher
- Datadog API and Application keys
- Access to Datadog usage and billing data

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://gitlab.com/datadog-health/cost-optimization.git
   cd cost-optimization
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your Datadog credentials
   export DD_API_KEY="your_api_key_here"
   export DD_APP_KEY="your_app_key_here"
   ```

4. **Test the connection**:
   ```bash
   python -m datadog_cost_analyzer.cli test-connection
   ```

### Usage

#### Web Interface (Recommended)

Start the web dashboard:
```bash
python -m datadog_cost_analyzer.cli serve --host 0.0.0.0 --port 12000
```

Access the dashboard at `http://localhost:12000`

#### Command Line Analysis

Run a complete analysis:
```bash
python -m datadog_cost_analyzer.cli analyze --weeks 12 --output report.json
```

Detect anomalies only:
```bash
python -m datadog_cost_analyzer.cli detect-anomalies --weeks 8 --threshold 2.5
```

Generate HTML report:
```bash
python -m datadog_cost_analyzer.cli analyze --weeks 12 --format html --output report.html
```

## Configuration

The tool uses a YAML configuration file located at `config/config.yaml`. Key settings include:

```yaml
# Analysis Configuration
analysis:
  lookback_weeks: 12
  anomaly_detection:
    z_score_threshold: 2.5
    iqr_multiplier: 1.5
    min_change_percent: 10.0
    seasonal_periods: 4

# Web Interface
web:
  host: "0.0.0.0"
  port: 12000
  debug: false
```

## API Reference

### REST Endpoints

- `GET /api/health` - Health check and component status
- `GET /api/cost-data?weeks=12` - Retrieve cost data
- `GET /api/analysis?weeks=12` - Complete cost analysis
- `GET /api/charts/{type}?weeks=12` - Generate specific charts
- `GET /api/export/report?format=html` - Export comprehensive reports

### Chart Types

- `trend` - Weekly cost trends
- `stacked` - Stacked cost breakdown
- `distribution` - Cost distribution pie chart
- `wow` - Week-over-week changes
- `anomalies` - Anomaly detection visualization
- `forecast` - Cost forecasting
- `efficiency` - Cost efficiency metrics
- `dashboard` - Combined dashboard view

## Anomaly Detection Methods

### 1. **Z-Score Analysis**
Identifies data points that deviate significantly from the mean using standard deviation.

### 2. **Interquartile Range (IQR)**
Detects outliers based on the interquartile range method.

### 3. **Isolation Forest**
Machine learning approach for detecting anomalies in multivariate data.

### 4. **Seasonal Decomposition**
Analyzes seasonal patterns and identifies deviations from expected seasonal behavior.

### 5. **Week-over-Week Analysis**
Flags significant percentage changes between consecutive weeks.

## Cost Categories Analyzed

- **Infrastructure**: Host hours, container usage
- **Logs**: Log ingestion and indexing
- **Metrics**: Custom metrics and monitoring
- **Traces**: APM and distributed tracing
- **Synthetics**: Synthetic monitoring
- **RUM**: Real User Monitoring
- **Security**: Security monitoring
- **Network**: Network monitoring

## Examples

### Basic Analysis
```python
from datadog_cost_analyzer import DatadogCostClient, CostAnalyzer, AnomalyDetector

# Initialize components
client = DatadogCostClient()
analyzer = CostAnalyzer()
detector = AnomalyDetector()

# Fetch and analyze data
df = client.get_weekly_cost_data(weeks=12)
processed_df = analyzer.process_weekly_data(df)
anomalies = detector.detect_anomalies(processed_df)

print(f"Detected {anomalies['summary']['total_anomalies']} anomalies")
```

### Custom Configuration
```python
config = {
    'analysis': {
        'anomaly_detection': {
            'z_score_threshold': 3.0,
            'min_change_percent': 15.0
        }
    }
}

analyzer = CostAnalyzer(config['analysis'])
detector = AnomalyDetector(config['analysis']['anomaly_detection'])
```

## Development

### Project Structure
```
src/datadog_cost_analyzer/
├── api/                 # Datadog API client
├── analysis/           # Cost analysis and anomaly detection
├── visualization/      # Chart generation
├── web/               # Flask web application
├── utils/             # Configuration and utilities
└── cli.py             # Command-line interface
```

### Running Tests
```bash
pytest tests/ -v --cov=src/datadog_cost_analyzer
```

### Code Quality
```bash
black src/ tests/
flake8 src/ tests/
mypy src/
```

## Troubleshooting

### Common Issues

1. **API Connection Failed**
   - Verify your Datadog API and App keys
   - Check the Datadog site configuration
   - Ensure network connectivity to Datadog

2. **No Cost Data Available**
   - Verify your organization has billing data
   - Check the date range (some data may have delays)
   - Ensure proper API permissions

3. **Anomaly Detection Issues**
   - Adjust thresholds for your specific use case
   - Ensure sufficient historical data (minimum 4 weeks)
   - Review seasonal patterns in your data

### Debug Mode
Enable verbose logging:
```bash
python -m datadog_cost_analyzer.cli --verbose analyze
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Merge Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

- **Issues**: Report bugs and request features via GitLab Issues
- **Documentation**: Comprehensive docs available in the `docs/` directory
- **Community**: Join discussions in GitLab Discussions

## Roadmap

- [ ] **Machine Learning Enhancements**: Advanced ML models for anomaly detection
- [ ] **Cost Optimization Recommendations**: Automated suggestions for cost reduction
- [ ] **Multi-Organization Support**: Analyze costs across multiple Datadog orgs
- [ ] **Slack/Teams Integration**: Real-time anomaly notifications
- [ ] **Historical Data Export**: Bulk export capabilities for long-term analysis
- [ ] **Custom Dashboards**: User-configurable dashboard layouts

## Authors

- **OpenHands** - Initial development and architecture

## Acknowledgments

- Datadog for providing comprehensive APIs
- The open-source community for excellent libraries (Plotly, Pandas, Scikit-learn)
- Contributors and users providing feedback and improvements
