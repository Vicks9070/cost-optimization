import os
import requests
import datetime
import openai

# Set your Datadog API and APP keys here or use environment variables
DATADOG_API_KEY = os.getenv('DATADOG_API_KEY', 'YOUR_DATADOG_API_KEY')
DATADOG_APP_KEY = os.getenv('DATADOG_APP_KEY', 'YOUR_DATADOG_APP_KEY')

# Set your OpenAI API key here or use environment variable
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'YOUR_OPENAI_API_KEY')
openai.api_key = OPENAI_API_KEY

# Datadog API endpoint for usage/cost (example: usage summary)
DATADOG_USAGE_URL = "https://api.datadoghq.com/api/v1/usage/summary"

# Fetch usage/cost data from Datadog
def fetch_datadog_usage(start_date, end_date):
    headers = {
        'DD-API-KEY': DATADOG_API_KEY,
        'DD-APPLICATION-KEY': DATADOG_APP_KEY
    }
    params = {
        'start_date': start_date,
        'end_date': end_date
    }
    response = requests.get(DATADOG_USAGE_URL, headers=headers, params=params)
    response.raise_for_status()
    return response.json()

# Use LLM to detect anomalies in the usage data
def detect_anomalies_with_llm(usage_data):
    prompt = f"""
You are an expert in cost optimization. Analyze the following Datadog usage/cost data and identify any sudden spikes or anomalies in product usage or cost. Be specific about which product and the time period.\n\nData:\n{usage_data}\n\nRespond with a summary of any anomalies found, or 'No anomalies detected.' if none are found.
"""
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "You are a helpful assistant."},
                  {"role": "user", "content": prompt}]
    )
    return response['choices'][0]['message']['content']

if __name__ == "__main__":
    # Analyze the last 7 days
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=7)
    print(f"Fetching Datadog usage from {start_date} to {end_date}...")
    usage_data = fetch_datadog_usage(str(start_date), str(end_date))
    print("Analyzing for anomalies using LLM...")
    anomalies = detect_anomalies_with_llm(usage_data)
    print("\nAnomaly Detection Result:")
    print(anomalies)
