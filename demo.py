#!/usr/bin/env python3
"""
Demo script for the Datadog Cost Analyzer
This script demonstrates the key features without requiring actual Datadog credentials
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from datadog_cost_analyzer.analysis.analyzer import CostAnalyzer
from datadog_cost_analyzer.analysis.anomaly_detector import AnomalyDetector
from datadog_cost_analyzer.visualization.charts import CostVisualizer


def generate_sample_data():
    """Generate realistic sample cost data for demonstration"""
    
    # Generate 16 weeks of data
    dates = pd.date_range(start='2024-01-01', periods=16, freq='W')
    
    # Base costs with some realistic variation
    base_infrastructure = 500
    base_logs = 300
    base_metrics = 200
    base_traces = 150
    base_synthetics = 100
    base_rum = 80
    base_security = 120
    base_network = 50
    
    # Generate data with trends and some anomalies
    data = []
    for i, date in enumerate(dates):
        # Add weekly growth trend
        growth_factor = 1 + (i * 0.02)  # 2% weekly growth
        
        # Add some seasonal variation (monthly cycle)
        seasonal_factor = 1 + 0.1 * np.sin(2 * np.pi * i / 4)
        
        # Add random variation
        random_factor = 1 + np.random.normal(0, 0.1)
        
        # Calculate costs
        infra_cost = base_infrastructure * growth_factor * seasonal_factor * random_factor
        logs_cost = base_logs * growth_factor * seasonal_factor * random_factor
        metrics_cost = base_metrics * growth_factor * seasonal_factor * random_factor
        traces_cost = base_traces * growth_factor * seasonal_factor * random_factor
        synthetics_cost = base_synthetics * growth_factor * seasonal_factor * random_factor
        rum_cost = base_rum * growth_factor * seasonal_factor * random_factor
        security_cost = base_security * growth_factor * seasonal_factor * random_factor
        network_cost = base_network * growth_factor * seasonal_factor * random_factor
        
        # Add some anomalies
        if i == 8:  # Week 9 - infrastructure spike
            infra_cost *= 2.5
        elif i == 12:  # Week 13 - logs spike
            logs_cost *= 3.0
        elif i == 5:  # Week 6 - overall drop
            infra_cost *= 0.3
            logs_cost *= 0.4
            metrics_cost *= 0.5
        
        total_cost = infra_cost + logs_cost + metrics_cost + traces_cost + synthetics_cost + rum_cost + security_cost + network_cost
        
        # Add usage data for efficiency calculations
        infra_usage = infra_cost / 5  # $5 per host hour
        logs_usage = logs_cost * 1000  # $0.001 per log event
        metrics_usage = metrics_cost / 0.05  # $0.05 per metric
        traces_usage = traces_cost / 3  # $3 per trace hour
        
        data.append({
            'week_start': date,
            'week_end': date + timedelta(days=6),
            'total_cost': total_cost,
            'infrastructure_cost': infra_cost,
            'logs_cost': logs_cost,
            'metrics_cost': metrics_cost,
            'traces_cost': traces_cost,
            'synthetics_cost': synthetics_cost,
            'rum_cost': rum_cost,
            'security_cost': security_cost,
            'network_cost': network_cost,
            'infrastructure_usage': infra_usage,
            'logs_usage': logs_usage,
            'metrics_usage': metrics_usage,
            'traces_usage': traces_usage
        })
    
    return pd.DataFrame(data)


def main():
    """Run the demonstration"""
    
    print("🚀 Datadog Cost Analyzer - DEMO")
    print("=" * 50)
    print("This demo shows the key features using simulated data")
    print()
    
    # Generate sample data
    print("📊 Generating sample cost data...")
    df = generate_sample_data()
    print(f"   Generated {len(df)} weeks of cost data")
    print(f"   Period: {df['week_start'].min().date()} to {df['week_end'].max().date()}")
    print(f"   Total cost range: ${df['total_cost'].min():,.0f} - ${df['total_cost'].max():,.0f}")
    print()
    
    # Initialize components
    print("🔧 Initializing analysis components...")
    analyzer = CostAnalyzer({
        'lookback_weeks': 16,
        'anomaly_detection': {
            'z_score_threshold': 2.0,
            'iqr_multiplier': 1.5,
            'min_change_percent': 15.0
        }
    })
    
    detector = AnomalyDetector({
        'z_score_threshold': 2.0,
        'iqr_multiplier': 1.5,
        'min_change_percent': 15.0,
        'seasonal_periods': 4
    })
    
    visualizer = CostVisualizer()
    print("   ✅ Components initialized")
    print()
    
    # Process data
    print("⚙️  Processing cost data...")
    processed_df = analyzer.process_weekly_data(df)
    print("   ✅ Data processed with advanced metrics")
    print()
    
    # Generate analysis
    print("📈 Generating cost analysis...")
    summary = analyzer.get_cost_summary(processed_df)
    cost_drivers = analyzer.identify_cost_drivers(processed_df, top_n=3)
    forecast = analyzer.calculate_forecast(processed_df, weeks_ahead=4)
    print("   ✅ Analysis complete")
    print()
    
    # Detect anomalies
    print("🚨 Detecting cost anomalies...")
    anomalies = detector.detect_anomalies(processed_df)
    print("   ✅ Anomaly detection complete")
    print()
    
    # Display results
    print("📋 ANALYSIS RESULTS")
    print("=" * 50)
    
    # Cost summary
    if summary.get('total_cost'):
        total_cost = summary['total_cost']
        print(f"💰 COST OVERVIEW")
        print(f"   Current week: ${total_cost['current_week']:,.0f}")
        print(f"   Average weekly: ${total_cost['average_weekly']:,.0f}")
        print(f"   Total period: ${total_cost['total_period']:,.0f}")
        
        change_pct = ((total_cost['current_week'] - total_cost['average_weekly']) / 
                     total_cost['average_weekly'] * 100)
        change_icon = "📈" if change_pct > 0 else "📉"
        print(f"   Change from average: {change_icon} {change_pct:+.1f}%")
        print()
    
    # Cost drivers
    if cost_drivers:
        print(f"🎯 TOP COST DRIVERS")
        for i, driver in enumerate(cost_drivers, 1):
            status_icon = "📈" if driver['status'] == 'increasing' else "📉" if driver['status'] == 'decreasing' else "➡️"
            print(f"   {i}. {driver['category'].title()} {status_icon}")
            print(f"      Current: ${driver['current_cost']:,.0f} ({driver['cost_percentage']:.1f}% of total)")
            print(f"      Recent change: {driver['recent_change_pct']:+.1f}%")
        print()
    
    # Anomaly results
    anomaly_count = anomalies.get('summary', {}).get('total_anomalies', 0)
    print(f"🚨 ANOMALY DETECTION")
    print(f"   Total anomalies: {anomaly_count}")
    
    if anomaly_count > 0:
        severity = anomalies['summary']['severity_distribution']
        print(f"   🔴 High severity: {severity['high']}")
        print(f"   🟡 Medium severity: {severity['medium']}")
        print(f"   🟢 Low severity: {severity['low']}")
        
        # Show anomaly weeks
        anomaly_weeks = anomalies['summary']['anomaly_weeks']
        print(f"   📅 Anomaly weeks: {', '.join(anomaly_weeks[:5])}")  # Show first 5
        
        # Show detection methods
        methods_used = []
        for method_name, method_data in anomalies.get('methods', {}).items():
            if method_data.get('results'):
                total_detections = sum(
                    result.get('anomaly_count', 0) 
                    for result in method_data['results'].values()
                )
                if total_detections > 0:
                    methods_used.append(f"{method_name.replace('_', ' ').title()}: {total_detections}")
        
        if methods_used:
            print(f"   🔍 Detection methods: {', '.join(methods_used)}")
    else:
        print("   ✅ No significant anomalies detected")
    print()
    
    # Forecast
    if forecast.get('categories', {}).get('total'):
        print(f"🔮 COST FORECAST (Next 4 weeks)")
        total_forecast = forecast['categories']['total']
        print(f"   Forecasted total: ${total_forecast['total_forecasted']:,.0f}")
        print(f"   Confidence: {total_forecast['confidence']:.1%}")
        
        trend_direction = "📈 Increasing" if total_forecast['trend_slope'] > 0 else "📉 Decreasing"
        print(f"   Trend: {trend_direction}")
        print()
    
    # Generate visualizations
    print("📊 Generating visualizations...")
    try:
        # Create charts
        charts = {
            'Cost Trend': visualizer.create_cost_trend_chart(processed_df),
            'Cost Distribution': visualizer.create_cost_distribution_chart(processed_df),
            'Anomaly Detection': visualizer.create_anomaly_chart(processed_df, anomalies),
            'Week-over-Week Changes': visualizer.create_week_over_week_chart(processed_df),
            'Cost Forecast': visualizer.create_forecast_chart(processed_df, forecast)
        }
        
        # Export to HTML
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        html_file = f'demo_cost_analysis_{timestamp}.html'
        visualizer.export_charts_to_html(charts, html_file)
        
        print(f"   ✅ Interactive charts saved as: {html_file}")
        print(f"   🌐 Open this file in your browser to view the charts")
        
    except Exception as e:
        print(f"   ⚠️  Could not generate visualizations: {e}")
    
    print()
    print("🎉 DEMO COMPLETE!")
    print("=" * 50)
    print("Key Features Demonstrated:")
    print("✅ Cost data processing and aggregation")
    print("✅ Multiple anomaly detection algorithms")
    print("✅ Cost trend analysis and forecasting")
    print("✅ Cost driver identification")
    print("✅ Interactive visualizations")
    print("✅ Comprehensive reporting")
    print()
    print("To use with real Datadog data:")
    print("1. Set DD_API_KEY and DD_APP_KEY environment variables")
    print("2. Run: python -m datadog_cost_analyzer.cli analyze")
    print("3. Or start web interface: python -m datadog_cost_analyzer.cli serve")
    print()
    print("For more information, see the README.md file")


if __name__ == '__main__':
    # Set random seed for reproducible demo
    np.random.seed(42)
    main()