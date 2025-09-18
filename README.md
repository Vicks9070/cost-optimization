# cost-optimization

## Datadog Cost Anomaly Detector

This repository contains a simple Python script `datadog_cost_anomaly_detector.py` that fetches Datadog usage/cost summary data and uses an LLM (via the OpenAI API) to identify sudden spikes or cost anomalies.

### Files added
- `datadog_cost_anomaly_detector.py` - main script
- `requirements.txt` - Python dependencies
- `.github/workflows/run-anomaly-detector.yml` - GitHub Actions workflow to run the detector on a schedule or manually

### Setup
1. Add the following repository secrets in your GitHub repository (Settings → Secrets & variables → Actions → New repository secret):
	- `DATADOG_API_KEY` - your Datadog API key
	- `DATADOG_APP_KEY` - your Datadog application key
	- `OPENAI_API_KEY` - your OpenAI API key (or the key for your chosen LLM provider)

2. The workflow is configured to run daily at 02:00 UTC. You can also manually trigger it from the Actions tab.

### Running locally
1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Export your keys and run the script:

```bash
export DATADOG_API_KEY="your_datadog_api_key"
export DATADOG_APP_KEY="your_datadog_app_key"
export OPENAI_API_KEY="your_openai_api_key"
python datadog_cost_anomaly_detector.py
```

### Notes & Next steps
- Consider adding structured alerts (email/Slack) when anomalies are detected.
- For production, add error handling, rate limit/backoff, and better prompt engineering for the LLM.
# cost-optimization