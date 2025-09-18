#!/usr/bin/env python3
"""
Advanced analysis example with custom configuration and detailed reporting
"""

import os
import sys
import json
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from datadog_cost_analyzer import DatadogCostClient, CostAnalyzer, AnomalyDetector, CostVisualizer


def main():
    """Advanced analysis example with custom configuration"""
    
    print("Datadog Cost Analyzer - Advanced Analysis Example")
    print("=" * 60)
    
    # Check for required environment variables
    if not os.getenv('DD_API_KEY') or not os.getenv('DD_APP_KEY'):
        print("Error: Please set DD_API_KEY and DD_APP_KEY environment variables")
        return
    
    try:
        # Custom configuration for more sensitive anomaly detection
        analysis_config = {
            'lookback_weeks': 16,
            'anomaly_detection': {
                'z_score_threshold': 2.0,  # More sensitive
                'iqr_multiplier': 1.2,     # More sensitive
                'min_change_percent': 5.0,  # Lower threshold
                'seasonal_periods': 4
            },
            'cost_categories': [
                'infrastructure', 'logs', 'metrics', 'traces',
                'synthetics', 'rum', 'security', 'network'
            ]
        }
        
        # Initialize components with custom config
        print("1. Initializing components with custom configuration...")
        client = DatadogCostClient()
        analyzer = CostAnalyzer(analysis_config)
        detector = AnomalyDetector(analysis_config['anomaly_detection'])
        visualizer = CostVisualizer()
        
        # Test connection
        if not client.test_connection():
            print("   ❌ Failed to connect to Datadog API")
            return
        print("   ✅ Connected to Datadog API")
        
        # Fetch extended cost data
        print("2. Fetching extended cost data (16 weeks)...")
        df = client.get_weekly_cost_data(weeks=16)
        
        if df.empty:
            print("   ⚠️  No cost data available")
            return
        
        print(f"   ✅ Retrieved {len(df)} weeks of cost data")
        print(f"   📅 Period: {df['week_start'].min().date()} to {df['week_end'].max().date()}")
        
        # Process data with advanced metrics
        print("3. Processing data with advanced metrics...")
        processed_df = analyzer.process_weekly_data(df)
        
        # Generate comprehensive analysis
        print("4. Generating comprehensive analysis...")
        summary = analyzer.get_cost_summary(processed_df)
        cost_drivers = analyzer.identify_cost_drivers(processed_df, top_n=5)
        forecast = analyzer.calculate_forecast(processed_df, weeks_ahead=6)
        
        # Advanced anomaly detection
        print("5. Running advanced anomaly detection...")
        anomalies = detector.detect_anomalies(processed_df)
        
        # Create comprehensive report
        report = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'analysis_config': analysis_config,
                'data_period': {
                    'weeks_analyzed': len(processed_df),
                    'start_date': processed_df['week_start'].min().strftime('%Y-%m-%d'),
                    'end_date': processed_df['week_end'].max().strftime('%Y-%m-%d')
                }
            },
            'summary': summary,
            'cost_drivers': cost_drivers,
            'forecast': forecast,
            'anomalies': anomalies
        }
        
        # Save detailed report
        report_file = f"advanced_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"   ✅ Detailed report saved as {report_file}")
        
        # Print detailed analysis
        print("\n" + "=" * 60)
        print("DETAILED ANALYSIS RESULTS")
        print("=" * 60)
        
        # Cost trends
        if summary.get('total_cost'):
            total_cost = summary['total_cost']
            print(f"\n📊 COST OVERVIEW")
            print(f"Current week: ${total_cost['current_week']:,.2f}")
            print(f"Previous week: ${total_cost['previous_week']:,.2f}")
            print(f"Average weekly: ${total_cost['average_weekly']:,.2f}")
            print(f"Standard deviation: ${total_cost['std_dev']:,.2f}")
            print(f"Min/Max weekly: ${total_cost['min_weekly']:,.2f} / ${total_cost['max_weekly']:,.2f}")
        
        # Cost drivers analysis
        if cost_drivers:
            print(f"\n🎯 TOP COST DRIVERS")
            for i, driver in enumerate(cost_drivers, 1):
                status_icon = "📈" if driver['status'] == 'increasing' else "📉" if driver['status'] == 'decreasing' else "➡️"
                print(f"{i}. {driver['category'].title()} {status_icon}")
                print(f"   Current: ${driver['current_cost']:,.2f} ({driver['cost_percentage']:.1f}% of total)")
                print(f"   Change: {driver['recent_change_pct']:+.1f}%")
                print(f"   Impact Score: {driver['impact_score']:.1f}")
        
        # Anomaly analysis
        anomaly_count = anomalies.get('summary', {}).get('total_anomalies', 0)
        print(f"\n🚨 ANOMALY DETECTION RESULTS")
        print(f"Total anomalies detected: {anomaly_count}")
        
        if anomaly_count > 0:
            severity = anomalies['summary']['severity_distribution']
            print(f"Severity breakdown:")
            print(f"  🔴 High: {severity['high']}")
            print(f"  🟡 Medium: {severity['medium']}")
            print(f"  🟢 Low: {severity['low']}")
            
            # Method breakdown
            methods = anomalies.get('methods', {})
            print(f"\nDetection methods used:")
            for method_name, method_data in methods.items():
                if method_data.get('results'):
                    total_detections = sum(
                        result.get('anomaly_count', 0) 
                        for result in method_data['results'].values()
                    )
                    print(f"  • {method_name.replace('_', ' ').title()}: {total_detections} detections")
            
            # Recent anomalies
            recent_anomalies = anomalies['summary']['anomaly_weeks'][-5:]  # Last 5
            if recent_anomalies:
                print(f"\nRecent anomaly weeks:")
                for week in recent_anomalies:
                    week_data = processed_df[processed_df['week_start'] == week]
                    if not week_data.empty:
                        cost = week_data['total_cost'].iloc[0]
                        print(f"  • {week}: ${cost:,.2f}")
        
        # Forecast analysis
        if forecast.get('categories', {}).get('total'):
            print(f"\n🔮 COST FORECAST (Next 6 weeks)")
            total_forecast = forecast['categories']['total']
            print(f"Forecasted total: ${total_forecast['total_forecasted']:,.2f}")
            print(f"Confidence: {total_forecast['confidence']:.1%}")
            
            trend_direction = "📈 Increasing" if total_forecast['trend_slope'] > 0 else "📉 Decreasing"
            print(f"Trend: {trend_direction}")
            
            # Weekly breakdown
            print(f"Weekly forecast:")
            for i, weekly_cost in enumerate(total_forecast['forecasted_values'], 1):
                print(f"  Week +{i}: ${weekly_cost:,.2f}")
        
        # Recommendations
        if anomalies.get('recommendations'):
            print(f"\n💡 RECOMMENDATIONS")
            for rec in anomalies['recommendations']:
                priority_icon = "🔴" if rec['priority'] == 'high' else "🟡" if rec['priority'] == 'medium' else "🟢"
                print(f"{priority_icon} {rec['title']}")
                print(f"   {rec['description']}")
                print(f"   Action: {rec['action']}")
        
        # Generate visualizations
        print(f"\n6. Generating advanced visualizations...")
        try:
            charts = {
                'Cost Trend': visualizer.create_cost_trend_chart(processed_df),
                'Stacked Breakdown': visualizer.create_stacked_cost_chart(processed_df),
                'Anomaly Detection': visualizer.create_anomaly_chart(processed_df, anomalies),
                'Week-over-Week': visualizer.create_week_over_week_chart(processed_df),
                'Cost Forecast': visualizer.create_forecast_chart(processed_df, forecast),
                'Efficiency Metrics': visualizer.create_efficiency_chart(processed_df)
            }
            
            # Export all charts to HTML
            html_file = f"advanced_analysis_charts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            visualizer.export_charts_to_html(charts, html_file)
            print(f"   ✅ Interactive charts saved as {html_file}")
            
        except Exception as e:
            print(f"   ⚠️  Could not create visualizations: {e}")
        
        print("\n" + "=" * 60)
        print("ADVANCED ANALYSIS COMPLETE")
        print("=" * 60)
        print("Files generated:")
        print(f"  📄 {report_file} - Detailed JSON report")
        if 'html_file' in locals():
            print(f"  📊 {html_file} - Interactive charts")
        print("\nNext steps:")
        print("1. Review the detailed analysis above")
        print("2. Open the HTML file in a browser for interactive charts")
        print("3. Share the JSON report with your team")
        print("4. Set up monitoring for high-priority anomalies")
        
    except Exception as e:
        print(f"Error during advanced analysis: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()