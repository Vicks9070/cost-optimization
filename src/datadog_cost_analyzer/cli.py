"""
Command-line interface for the Datadog cost analyzer
"""

import os
import sys
import logging
import click
import json
from datetime import datetime
from typing import Optional

from .api.client import DatadogCostClient
from .analysis.analyzer import CostAnalyzer
from .analysis.anomaly_detector import AnomalyDetector
from .visualization.charts import CostVisualizer
from .web.app import create_app
from .utils.config import ConfigManager
from .integrations.notebook_creator import DatadogNotebookCreator

logger = logging.getLogger(__name__)


@click.group()
@click.option('--config', '-c', help='Path to configuration file')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, config, verbose):
    """Datadog Cost Analyzer - Analyze and detect anomalies in Datadog costs"""
    
    # Initialize context
    ctx.ensure_object(dict)
    
    # Load configuration
    config_manager = ConfigManager(config)
    ctx.obj['config_manager'] = config_manager
    ctx.obj['config'] = config_manager.get_config()
    
    # Setup logging
    if verbose:
        config_manager.set_value('logging.level', 'DEBUG')
    config_manager.setup_logging()
    
    # Validate configuration
    validation = config_manager.validate_config()
    if not validation['valid']:
        for error in validation['errors']:
            click.echo(f"Error: {error}", err=True)
        sys.exit(1)
    
    if validation['warnings']:
        for warning in validation['warnings']:
            click.echo(f"Warning: {warning}", err=True)


@cli.command()
@click.option('--weeks', '-w', default=12, help='Number of weeks to analyze')
@click.option('--output', '-o', help='Output file path')
@click.option('--format', 'output_format', default='json', 
              type=click.Choice(['json', 'csv', 'html']), help='Output format')
@click.pass_context
def analyze(ctx, weeks, output, output_format):
    """Run cost analysis and anomaly detection"""
    
    config = ctx.obj['config']
    
    try:
        # Initialize components
        click.echo("Initializing Datadog client...")
        client = DatadogCostClient()
        
        if not client.test_connection():
            click.echo("Error: Failed to connect to Datadog API", err=True)
            sys.exit(1)
        
        analyzer = CostAnalyzer(config.get('analysis', {}))
        anomaly_detector = AnomalyDetector(config.get('analysis', {}).get('anomaly_detection', {}))
        
        # Fetch data
        click.echo(f"Fetching cost data for the last {weeks} weeks...")
        df = client.get_weekly_cost_data(weeks)
        
        if df.empty:
            click.echo("Error: No cost data available", err=True)
            sys.exit(1)
        
        # Process data
        click.echo("Processing cost data...")
        processed_df = analyzer.process_weekly_data(df)
        
        # Generate analysis
        click.echo("Generating cost analysis...")
        summary = analyzer.get_cost_summary(processed_df)
        cost_drivers = analyzer.identify_cost_drivers(processed_df)
        forecast = analyzer.calculate_forecast(processed_df)
        
        click.echo("Detecting anomalies...")
        anomalies = anomaly_detector.detect_anomalies(processed_df)
        
        # Prepare results
        results = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'weeks_analyzed': len(processed_df),
                'period': {
                    'start': processed_df['week_start'].min().strftime('%Y-%m-%d'),
                    'end': processed_df['week_end'].max().strftime('%Y-%m-%d')
                }
            },
            'summary': summary,
            'cost_drivers': cost_drivers,
            'forecast': forecast,
            'anomalies': anomalies
        }
        
        # Output results
        if output_format == 'json':
            output_data = json.dumps(results, indent=2, default=str)
        elif output_format == 'csv':
            output_data = processed_df.to_csv(index=False)
        elif output_format == 'html':
            # Generate HTML report with charts
            visualizer = CostVisualizer()
            charts = {
                'Cost Trend': visualizer.create_cost_trend_chart(processed_df),
                'Cost Distribution': visualizer.create_cost_distribution_chart(processed_df),
                'Anomaly Detection': visualizer.create_anomaly_chart(processed_df, anomalies),
                'Week-over-Week Changes': visualizer.create_week_over_week_chart(processed_df),
                'Cost Forecast': visualizer.create_forecast_chart(processed_df, forecast)
            }
            
            if output:
                visualizer.export_charts_to_html(charts, output)
                click.echo(f"HTML report saved to {output}")
                return
            else:
                click.echo("Error: HTML format requires --output parameter", err=True)
                sys.exit(1)
        
        # Save or print results
        if output:
            with open(output, 'w') as f:
                f.write(output_data)
            click.echo(f"Analysis results saved to {output}")
        else:
            click.echo(output_data)
        
        # Print summary
        click.echo("\n" + "="*50)
        click.echo("ANALYSIS SUMMARY")
        click.echo("="*50)
        
        if summary.get('total_cost'):
            current_cost = summary['total_cost']['current_week']
            avg_cost = summary['total_cost']['average_weekly']
            click.echo(f"Current week cost: ${current_cost:,.2f}")
            click.echo(f"Average weekly cost: ${avg_cost:,.2f}")
            click.echo(f"Change from average: {((current_cost - avg_cost) / avg_cost * 100):+.1f}%")
        
        if anomalies.get('summary'):
            total_anomalies = anomalies['summary']['total_anomalies']
            click.echo(f"Anomalies detected: {total_anomalies}")
            
            if total_anomalies > 0:
                severity = anomalies['summary']['severity_distribution']
                click.echo(f"  High severity: {severity['high']}")
                click.echo(f"  Medium severity: {severity['medium']}")
                click.echo(f"  Low severity: {severity['low']}")
        
        if cost_drivers:
            click.echo(f"Top cost driver: {cost_drivers[0]['category']} (${cost_drivers[0]['current_cost']:,.2f})")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--weeks', '-w', default=12, help='Number of weeks to analyze')
@click.option('--threshold', '-t', default=2.5, help='Z-score threshold for anomaly detection')
@click.pass_context
def detect_anomalies(ctx, weeks, threshold):
    """Detect cost anomalies only"""
    
    config = ctx.obj['config']
    
    try:
        # Initialize components
        client = DatadogCostClient()
        analyzer = CostAnalyzer(config.get('analysis', {}))
        
        # Override threshold
        anomaly_config = config.get('analysis', {}).get('anomaly_detection', {})
        anomaly_config['z_score_threshold'] = threshold
        anomaly_detector = AnomalyDetector(anomaly_config)
        
        # Fetch and process data
        click.echo(f"Analyzing last {weeks} weeks for anomalies...")
        df = client.get_weekly_cost_data(weeks)
        processed_df = analyzer.process_weekly_data(df)
        
        # Detect anomalies
        anomalies = anomaly_detector.detect_anomalies(processed_df)
        
        # Display results
        if anomalies.get('summary', {}).get('total_anomalies', 0) == 0:
            click.echo("✅ No anomalies detected")
        else:
            total = anomalies['summary']['total_anomalies']
            click.echo(f"⚠️  {total} anomalies detected:")
            
            for week in anomalies['summary']['anomaly_weeks']:
                week_data = processed_df[processed_df['week_start'] == week]
                if not week_data.empty:
                    cost = week_data['total_cost'].iloc[0]
                    click.echo(f"  - Week {week}: ${cost:,.2f}")
            
            # Show recommendations
            if anomalies.get('recommendations'):
                click.echo("\nRecommendations:")
                for rec in anomalies['recommendations']:
                    priority_icon = "🔴" if rec['priority'] == 'high' else "🟡" if rec['priority'] == 'medium' else "🟢"
                    click.echo(f"  {priority_icon} {rec['title']}: {rec['description']}")
        
    except Exception as e:
        logger.error(f"Anomaly detection failed: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--host', '-h', default='0.0.0.0', help='Host to bind to')
@click.option('--port', '-p', default=12000, help='Port to bind to')
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.pass_context
def serve(ctx, host, port, debug):
    """Start the web interface"""
    
    config = ctx.obj['config']
    
    # Override web configuration
    config['web']['host'] = host
    config['web']['port'] = port
    config['web']['debug'] = debug
    
    try:
        click.echo(f"Starting web interface on http://{host}:{port}")
        app = create_app(config)
        app.run(host=host, port=port, debug=debug)
        
    except Exception as e:
        logger.error(f"Failed to start web interface: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def test_connection(ctx):
    """Test connection to Datadog API"""
    
    try:
        click.echo("Testing Datadog API connection...")
        client = DatadogCostClient()
        
        if client.test_connection():
            click.echo("✅ Successfully connected to Datadog API")
        else:
            click.echo("❌ Failed to connect to Datadog API")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        click.echo(f"❌ Connection test failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def validate_config(ctx):
    """Validate configuration"""
    
    config_manager = ctx.obj['config_manager']
    validation = config_manager.validate_config()
    
    if validation['valid']:
        click.echo("✅ Configuration is valid")
    else:
        click.echo("❌ Configuration has errors:")
        for error in validation['errors']:
            click.echo(f"  - {error}")
    
    if validation['warnings']:
        click.echo("⚠️  Configuration warnings:")
        for warning in validation['warnings']:
            click.echo(f"  - {warning}")


@cli.command()
@click.option('--api-key', help='Datadog API key')
@click.option('--app-key', help='Datadog Application key')
@click.option('--site', default='datadoghq.com', help='Datadog site')
@click.pass_context
def configure(ctx, api_key, app_key, site):
    """Configure Datadog credentials"""
    
    config_manager = ctx.obj['config_manager']
    
    if api_key:
        config_manager.set_value('datadog.api_key', api_key)
        click.echo("API key updated")
    
    if app_key:
        config_manager.set_value('datadog.app_key', app_key)
        click.echo("Application key updated")
    
    if site != 'datadoghq.com':
        config_manager.set_value('datadog.site', site)
        click.echo(f"Site updated to {site}")
    
    try:
        config_manager.save_config()
        click.echo("Configuration saved")
    except Exception as e:
        click.echo(f"Error saving configuration: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--weeks', '-w', default=12, help='Number of weeks to analyze')
@click.option('--title', '-t', help='Custom title for the notebook')
@click.option('--tags', help='Comma-separated tags for the notebook')
@click.option('--update-existing', help='Update existing notebook by ID instead of creating new')
@click.option('--include-daily-delta', is_flag=True, default=False, help='Include D-1 vs D-2 cost delta section')
@click.pass_context
def create_notebook(ctx, weeks, title, tags, update_existing, include_daily_delta):
    """Create or update a Datadog notebook with cost anomaly analysis"""
    
    try:
        config_manager = ctx.obj['config_manager']
        
        # Get API credentials
        api_key = config_manager.get_value('datadog.api_key')
        app_key = config_manager.get_value('datadog.app_key')
        site = config_manager.get_value('datadog.site', 'datadoghq.com')
        
        if not api_key or not app_key:
            click.echo("Error: Datadog API credentials not configured. Run 'configure' command first.", err=True)
            sys.exit(1)
        
        click.echo(f"Creating cost anomaly analysis notebook...")
        
        # Initialize components
        client = DatadogCostClient(api_key, app_key, site)
        analyzer = CostAnalyzer(config_manager.get_config().get('analysis', {}))
        anomaly_detector = AnomalyDetector(config_manager.get_config().get('analysis', {}))
        notebook_creator = DatadogNotebookCreator(api_key, app_key, site)
        
        # Fetch and analyze cost data
        click.echo("Fetching cost data...")
        cost_data = client.get_usage_data(weeks=weeks)
        
        if not cost_data:
            click.echo("Error: No cost data retrieved", err=True)
            sys.exit(1)
        
        click.echo("Processing cost data...")
        processed_data = analyzer.process_cost_data(cost_data)
        
        click.echo("Detecting anomalies...")
        anomaly_results = anomaly_detector.detect_anomalies(processed_data)
        
        # Prepare data for notebook
        cost_summary = {
            'total_cost': float(processed_data['total_cost'].sum()),
            'period': f'Last {weeks} weeks',
            'trend': analyzer.analyze_trends(processed_data).get('overall_trend', 'stable'),
            'categories': {
                col.replace('_cost', ''): float(processed_data[col].sum()) 
                for col in processed_data.columns 
                if col.endswith('_cost') and col != 'total_cost'
            },
            'forecast': analyzer.forecast_costs(processed_data, periods=4)
        }

        # Optionally add daily delta comparison for D-1 vs D-2
        if include_daily_delta:
            click.echo("Computing daily D-1 vs D-2 cost delta...")
            try:
                daily_delta = client.get_daily_cost_delta_by_product()
                cost_summary['daily_delta'] = daily_delta
            except Exception as e:
                click.echo(f"Warning: Failed to compute daily delta: {e}")
        
        # Parse tags
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',')]
        tag_list.extend(['cost-analysis', 'anomaly-detection', 'financial-monitoring'])
        
        # Create or update notebook
        if update_existing:
            click.echo(f"Updating existing notebook: {update_existing}")
            result = notebook_creator.update_notebook(update_existing, anomaly_results, cost_summary)
        else:
            click.echo("Creating new notebook...")
            result = notebook_creator.create_cost_anomaly_notebook(
                anomaly_results, 
                cost_summary, 
                title=title,
                tags=tag_list
            )
        
        if result.get('success'):
            click.echo(f"✅ Notebook {'updated' if update_existing else 'created'} successfully!")
            click.echo(f"📊 Notebook URL: {result.get('notebook_url', 'N/A')}")
            click.echo(f"📝 Title: {result.get('title', 'N/A')}")
            click.echo(f"📅 {'Updated' if update_existing else 'Created'} at: {result.get('created_at' if not update_existing else 'updated_at', 'N/A')}")
            click.echo(f"📋 Cell count: {result.get('cell_count', 'N/A')}")
            click.echo(f"🏷️ Tags: {', '.join(result.get('tags', []))}")
            
            # Show anomaly summary
            summary = anomaly_results.get('summary', {})
            if summary.get('total_anomalies', 0) > 0:
                click.echo(f"\n🚨 Anomalies detected: {summary['total_anomalies']}")
                severity = summary.get('severity_distribution', {})
                click.echo(f"   - High: {severity.get('high', 0)}")
                click.echo(f"   - Medium: {severity.get('medium', 0)}")
                click.echo(f"   - Low: {severity.get('low', 0)}")
            else:
                click.echo("\n✅ No significant anomalies detected")
                
        else:
            click.echo(f"❌ Failed to {'update' if update_existing else 'create'} notebook: {result.get('error', 'Unknown error')}", err=True)
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        logger.exception("Failed to create notebook")
        sys.exit(1)


@cli.command()
@click.option('--tags', help='Filter notebooks by tags (comma-separated)')
@click.pass_context
def list_notebooks(ctx, tags):
    """List existing cost analysis notebooks"""
    
    try:
        config_manager = ctx.obj['config_manager']
        
        # Get API credentials
        api_key = config_manager.get_value('datadog.api_key')
        app_key = config_manager.get_value('datadog.app_key')
        site = config_manager.get_value('datadog.site', 'datadoghq.com')
        
        if not api_key or not app_key:
            click.echo("Error: Datadog API credentials not configured. Run 'configure' command first.", err=True)
            sys.exit(1)
        
        notebook_creator = DatadogNotebookCreator(api_key, app_key, site)
        
        # Parse tags
        tag_list = None
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',')]
        
        click.echo("Fetching cost analysis notebooks...")
        notebooks = notebook_creator.list_cost_analysis_notebooks(tags=tag_list)
        
        if not notebooks:
            click.echo("No cost analysis notebooks found.")
            return
        
        click.echo(f"\nFound {len(notebooks)} cost analysis notebook(s):\n")
        
        for i, notebook in enumerate(notebooks, 1):
            click.echo(f"{i}. {notebook['name']}")
            click.echo(f"   ID: {notebook['id']}")
            click.echo(f"   URL: {notebook['url']}")
            click.echo(f"   Created: {notebook.get('created_at', 'N/A')}")
            click.echo(f"   Modified: {notebook.get('modified_at', 'N/A')}")
            click.echo(f"   Tags: {', '.join(notebook.get('tags', []))}")
            click.echo()
            
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        logger.exception("Failed to list notebooks")
        sys.exit(1)


def main():
    """Main entry point"""
    cli()


if __name__ == '__main__':
    main()