#!/usr/bin/env python3
"""
Basic usage example for the Datadog Cost Analyzer
"""

import os
import sys
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from datadog_cost_analyzer import DatadogCostClient, CostAnalyzer, AnomalyDetector, CostVisualizer


def main():
    """Basic usage example"""
    
    print("Datadog Cost Analyzer - Basic Usage Example")
    print("=" * 50)
    
    # Check for required environment variables
    if not os.getenv('DD_API_KEY') or not os.getenv('DD_APP_KEY'):
        print("Error: Please set DD_API_KEY and DD_APP_KEY environment variables")
        print("You can copy .env.example to .env and fill in your credentials")
        return
    
    try:
        # Initialize components
        print("1. Initializing Datadog client...")
        client = DatadogCostClient()
        
        # Test connection
        print("2. Testing connection to Datadog API...")
        if not client.test_connection():
            print("   ❌ Failed to connect to Datadog API")
            return
        print("   ✅ Successfully connected to Datadog API")
        
        # Initialize analysis components
        print("3. Initializing analysis components...")
        analyzer = CostAnalyzer()
        detector = AnomalyDetector()
        visualizer = CostVisualizer()
        
        # Fetch cost data
        print("4. Fetching cost data for the last 12 weeks...")
        df = client.get_weekly_cost_data(weeks=12)
        
        if df.empty:
            print("   ⚠️  No cost data available")
            print("   This might be because:")
            print("   - Your organization doesn't have billing data yet")
            print("   - The API keys don't have sufficient permissions")
            print("   - There's a delay in data availability")
            return
        
        print(f"   ✅ Retrieved {len(df)} weeks of cost data")
        
        # Process data
        print("5. Processing cost data...")
        processed_df = analyzer.process_weekly_data(df)
        
        # Generate summary
        print("6. Generating cost summary...")
        summary = analyzer.get_cost_summary(processed_df)
        
        # Print summary
        print("\n" + "=" * 50)
        print("COST SUMMARY")
        print("=" * 50)
        
        if summary.get('total_cost'):
            total_cost = summary['total_cost']
            print(f"Current week cost: ${total_cost['current_week']:,.2f}")
            print(f"Average weekly cost: ${total_cost['average_weekly']:,.2f}")
            print(f"Total period cost: ${total_cost['total_period']:,.2f}")
            
            change_pct = ((total_cost['current_week'] - total_cost['average_weekly']) / 
                         total_cost['average_weekly'] * 100)
            print(f"Change from average: {change_pct:+.1f}%")
        
        # Identify cost drivers
        print("\n7. Identifying cost drivers...")
        cost_drivers = analyzer.identify_cost_drivers(processed_df, top_n=3)
        
        if cost_drivers:
            print("\nTop Cost Drivers:")
            for i, driver in enumerate(cost_drivers, 1):
                print(f"  {i}. {driver['category'].title()}: ${driver['current_cost']:,.2f} "
                      f"({driver['recent_change_pct']:+.1f}% change)")
        
        # Detect anomalies
        print("\n8. Detecting cost anomalies...")
        anomalies = detector.detect_anomalies(processed_df)
        
        anomaly_count = anomalies.get('summary', {}).get('total_anomalies', 0)
        print(f"   Detected {anomaly_count} anomalies")
        
        if anomaly_count > 0:
            severity = anomalies['summary']['severity_distribution']
            print(f"   - High severity: {severity['high']}")
            print(f"   - Medium severity: {severity['medium']}")
            print(f"   - Low severity: {severity['low']}")
            
            # Show recent anomalies
            recent_anomalies = anomalies['summary']['anomaly_weeks'][-3:]  # Last 3
            if recent_anomalies:
                print(f"\n   Recent anomaly weeks: {', '.join(recent_anomalies)}")
        
        # Generate forecast
        print("\n9. Generating cost forecast...")
        forecast = analyzer.calculate_forecast(processed_df, weeks_ahead=4)
        
        if forecast.get('categories', {}).get('total'):
            total_forecast = forecast['categories']['total']
            forecasted_total = total_forecast['total_forecasted']
            current_4week_avg = processed_df['total_cost'].tail(4).mean() * 4
            
            print(f"   Next 4 weeks forecast: ${forecasted_total:,.2f}")
            print(f"   Recent 4 weeks actual: ${current_4week_avg:,.2f}")
            
            change = ((forecasted_total - current_4week_avg) / current_4week_avg * 100)
            print(f"   Forecast change: {change:+.1f}%")
        
        # Create a simple visualization
        print("\n10. Creating cost trend visualization...")
        try:
            trend_chart = visualizer.create_cost_trend_chart(processed_df)
            
            # Save chart as HTML
            chart_file = "cost_trend_example.html"
            trend_chart.write_html(chart_file)
            print(f"    ✅ Cost trend chart saved as {chart_file}")
            
        except Exception as e:
            print(f"    ⚠️  Could not create visualization: {e}")
        
        print("\n" + "=" * 50)
        print("ANALYSIS COMPLETE")
        print("=" * 50)
        print("Next steps:")
        print("1. Review the cost summary and trends above")
        print("2. Investigate any high-severity anomalies")
        print("3. Consider the forecast for budget planning")
        print("4. Run the web interface for interactive analysis:")
        print("   python -m datadog_cost_analyzer.cli serve")
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()