"""
Flask web application for the Datadog cost analyzer
"""

import os
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd

from ..api.client import DatadogCostClient
from ..analysis.analyzer import CostAnalyzer
from ..analysis.anomaly_detector import AnomalyDetector
from ..visualization.charts import CostVisualizer
from ..utils.config import ConfigManager

logger = logging.getLogger(__name__)


def create_app(config: Optional[Dict[str, Any]] = None) -> Flask:
    """
    Create and configure the Flask application
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        Configured Flask application
    """
    app = Flask(__name__)
    CORS(app)
    
    # Load configuration
    config_manager = ConfigManager()
    app_config = config or config_manager.get_config()
    
    # Configure Flask
    app.config['SECRET_KEY'] = os.urandom(24)
    app.config['DEBUG'] = app_config.get('web', {}).get('debug', False)
    
    # Initialize components
    try:
        datadog_client = DatadogCostClient()
        cost_analyzer = CostAnalyzer(app_config.get('analysis', {}))
        anomaly_detector = AnomalyDetector(app_config.get('analysis', {}).get('anomaly_detection', {}))
        visualizer = CostVisualizer()
        
        # Test connection
        if not datadog_client.test_connection():
            logger.warning("Failed to connect to Datadog API - some features may not work")
        
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        datadog_client = None
        cost_analyzer = None
        anomaly_detector = None
        visualizer = None
    
    @app.route('/')
    def index():
        """Main dashboard page"""
        return render_template('dashboard.html')
    
    @app.route('/api/health')
    def health_check():
        """Health check endpoint"""
        status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'components': {
                'datadog_client': datadog_client is not None,
                'cost_analyzer': cost_analyzer is not None,
                'anomaly_detector': anomaly_detector is not None,
                'visualizer': visualizer is not None
            }
        }
        
        if datadog_client:
            status['components']['datadog_connection'] = datadog_client.test_connection()
        
        return jsonify(status)
    
    @app.route('/api/cost-data')
    def get_cost_data():
        """Get cost data for analysis"""
        if not datadog_client:
            return jsonify({'error': 'Datadog client not initialized'}), 500
        
        try:
            weeks_back = request.args.get('weeks', 12, type=int)
            
            # Fetch cost data
            df = datadog_client.get_weekly_cost_data(weeks_back)
            
            if df.empty:
                return jsonify({'error': 'No cost data available'}), 404
            
            # Process data
            processed_df = cost_analyzer.process_weekly_data(df)
            
            # Convert to JSON-serializable format
            data = {
                'weeks': processed_df['week_start'].dt.strftime('%Y-%m-%d').tolist(),
                'total_cost': processed_df['total_cost'].tolist(),
                'categories': {}
            }
            
            # Add category data
            categories = [col.replace('_cost', '') for col in processed_df.columns if col.endswith('_cost') and col != 'total_cost']
            for category in categories:
                cost_col = f'{category}_cost'
                if cost_col in processed_df.columns:
                    data['categories'][category] = processed_df[cost_col].tolist()
            
            return jsonify(data)
            
        except Exception as e:
            logger.error(f"Error fetching cost data: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/analysis')
    def get_analysis():
        """Get comprehensive cost analysis"""
        if not all([datadog_client, cost_analyzer, anomaly_detector]):
            return jsonify({'error': 'Components not initialized'}), 500
        
        try:
            weeks_back = request.args.get('weeks', 12, type=int)
            
            # Fetch and process data
            df = datadog_client.get_weekly_cost_data(weeks_back)
            if df.empty:
                return jsonify({'error': 'No cost data available'}), 404
            
            processed_df = cost_analyzer.process_weekly_data(df)
            
            # Generate analysis
            summary = cost_analyzer.get_cost_summary(processed_df)
            cost_drivers = cost_analyzer.identify_cost_drivers(processed_df)
            forecast = cost_analyzer.calculate_forecast(processed_df)
            anomalies = anomaly_detector.detect_anomalies(processed_df)
            
            analysis = {
                'summary': summary,
                'cost_drivers': cost_drivers,
                'forecast': forecast,
                'anomalies': anomalies,
                'data_period': {
                    'weeks_analyzed': len(processed_df),
                    'start_date': processed_df['week_start'].min().strftime('%Y-%m-%d'),
                    'end_date': processed_df['week_end'].max().strftime('%Y-%m-%d')
                }
            }
            
            return jsonify(analysis)
            
        except Exception as e:
            logger.error(f"Error generating analysis: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/charts/<chart_type>')
    def get_chart(chart_type):
        """Get specific chart data"""
        if not all([datadog_client, cost_analyzer, visualizer]):
            return jsonify({'error': 'Components not initialized'}), 500
        
        try:
            weeks_back = request.args.get('weeks', 12, type=int)
            
            # Fetch and process data
            df = datadog_client.get_weekly_cost_data(weeks_back)
            if df.empty:
                return jsonify({'error': 'No cost data available'}), 404
            
            processed_df = cost_analyzer.process_weekly_data(df)
            
            # Generate requested chart
            if chart_type == 'trend':
                fig = visualizer.create_cost_trend_chart(processed_df)
            elif chart_type == 'stacked':
                fig = visualizer.create_stacked_cost_chart(processed_df)
            elif chart_type == 'distribution':
                fig = visualizer.create_cost_distribution_chart(processed_df)
            elif chart_type == 'wow':
                fig = visualizer.create_week_over_week_chart(processed_df)
            elif chart_type == 'efficiency':
                fig = visualizer.create_efficiency_chart(processed_df)
            elif chart_type == 'forecast':
                forecast = cost_analyzer.calculate_forecast(processed_df)
                fig = visualizer.create_forecast_chart(processed_df, forecast)
            elif chart_type == 'anomalies':
                anomalies = anomaly_detector.detect_anomalies(processed_df)
                fig = visualizer.create_anomaly_chart(processed_df, anomalies)
            elif chart_type == 'dashboard':
                summary = cost_analyzer.get_cost_summary(processed_df)
                anomalies = anomaly_detector.detect_anomalies(processed_df)
                fig = visualizer.create_dashboard_summary(processed_df, summary, anomalies)
            else:
                return jsonify({'error': f'Unknown chart type: {chart_type}'}), 400
            
            # Return chart as JSON
            return jsonify(fig.to_dict())
            
        except Exception as e:
            logger.error(f"Error generating chart {chart_type}: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/export/report')
    def export_report():
        """Export comprehensive analysis report"""
        if not all([datadog_client, cost_analyzer, anomaly_detector, visualizer]):
            return jsonify({'error': 'Components not initialized'}), 500
        
        try:
            weeks_back = request.args.get('weeks', 12, type=int)
            format_type = request.args.get('format', 'html')
            
            # Fetch and process data
            df = datadog_client.get_weekly_cost_data(weeks_back)
            if df.empty:
                return jsonify({'error': 'No cost data available'}), 404
            
            processed_df = cost_analyzer.process_weekly_data(df)
            
            # Generate analysis
            summary = cost_analyzer.get_cost_summary(processed_df)
            anomalies = anomaly_detector.detect_anomalies(processed_df)
            forecast = cost_analyzer.calculate_forecast(processed_df)
            
            if format_type == 'html':
                # Generate charts
                charts = {
                    'Cost Trend': visualizer.create_cost_trend_chart(processed_df),
                    'Cost Distribution': visualizer.create_cost_distribution_chart(processed_df),
                    'Anomaly Detection': visualizer.create_anomaly_chart(processed_df, anomalies),
                    'Week-over-Week Changes': visualizer.create_week_over_week_chart(processed_df),
                    'Cost Forecast': visualizer.create_forecast_chart(processed_df, forecast)
                }
                
                # Export to HTML
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'cost_analysis_report_{timestamp}.html'
                filepath = os.path.join('/tmp', filename)
                
                visualizer.export_charts_to_html(charts, filepath)
                
                return send_file(filepath, as_attachment=True, download_name=filename)
            
            elif format_type == 'json':
                report = {
                    'metadata': {
                        'generated_at': datetime.now().isoformat(),
                        'weeks_analyzed': len(processed_df),
                        'period': {
                            'start': processed_df['week_start'].min().strftime('%Y-%m-%d'),
                            'end': processed_df['week_end'].max().strftime('%Y-%m-%d')
                        }
                    },
                    'summary': summary,
                    'anomalies': anomalies,
                    'forecast': forecast,
                    'raw_data': processed_df.to_dict('records')
                }
                
                return jsonify(report)
            
            else:
                return jsonify({'error': f'Unsupported format: {format_type}'}), 400
                
        except Exception as e:
            logger.error(f"Error exporting report: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/config')
    def get_config():
        """Get current configuration"""
        return jsonify({
            'analysis': app_config.get('analysis', {}),
            'web': app_config.get('web', {}),
            'datadog': {
                'site': app_config.get('datadog', {}).get('site', 'datadoghq.com'),
                'api_key_configured': bool(os.getenv('DD_API_KEY')),
                'app_key_configured': bool(os.getenv('DD_APP_KEY'))
            }
        })
    
    @app.route('/api/config', methods=['POST'])
    def update_config():
        """Update configuration"""
        try:
            new_config = request.get_json()
            
            # Validate configuration
            if 'analysis' in new_config:
                # Update analysis configuration
                app_config['analysis'].update(new_config['analysis'])
                
                # Reinitialize components with new config
                nonlocal cost_analyzer, anomaly_detector
                cost_analyzer = CostAnalyzer(app_config.get('analysis', {}))
                anomaly_detector = AnomalyDetector(app_config.get('analysis', {}).get('anomaly_detection', {}))
            
            return jsonify({'status': 'success', 'message': 'Configuration updated'})
            
        except Exception as e:
            logger.error(f"Error updating configuration: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=12000, debug=True)