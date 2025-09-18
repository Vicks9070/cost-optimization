"""
Basic functionality tests for the Datadog Cost Analyzer
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from datadog_cost_analyzer.analysis.analyzer import CostAnalyzer
from datadog_cost_analyzer.analysis.anomaly_detector import AnomalyDetector
from datadog_cost_analyzer.visualization.charts import CostVisualizer
from datadog_cost_analyzer.utils.config import ConfigManager


class TestCostAnalyzer:
    """Test the CostAnalyzer class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.analyzer = CostAnalyzer()
        
        # Create sample data
        dates = pd.date_range(start='2024-01-01', periods=12, freq='W')
        self.sample_data = pd.DataFrame({
            'week_start': dates,
            'week_end': dates + timedelta(days=6),
            'total_cost': [1000, 1100, 950, 1200, 1050, 1300, 1150, 1400, 1250, 1100, 1350, 1200],
            'infrastructure_cost': [400, 450, 380, 480, 420, 520, 460, 560, 500, 440, 540, 480],
            'logs_cost': [300, 330, 285, 360, 315, 390, 345, 420, 375, 330, 405, 360],
            'metrics_cost': [200, 220, 190, 240, 210, 260, 230, 280, 250, 220, 270, 240],
            'traces_cost': [100, 100, 95, 120, 105, 130, 115, 140, 125, 110, 135, 120],
            'infrastructure_usage': [100, 110, 95, 120, 105, 130, 115, 140, 125, 110, 135, 120],
            'logs_usage': [50000, 55000, 47500, 60000, 52500, 65000, 57500, 70000, 62500, 55000, 67500, 60000]
        })
    
    def test_process_weekly_data(self):
        """Test processing of weekly data"""
        processed_df = self.analyzer.process_weekly_data(self.sample_data)
        
        # Check that new columns are added
        assert 'total_wow_change' in processed_df.columns
        assert 'infrastructure_wow_change' in processed_df.columns
        assert 'total_avg_4w' in processed_df.columns
        assert 'cost_per_host_hour' in processed_df.columns
        
        # Check data integrity
        assert len(processed_df) == len(self.sample_data)
        assert not processed_df['total_cost'].isna().all()
    
    def test_get_cost_summary(self):
        """Test cost summary generation"""
        processed_df = self.analyzer.process_weekly_data(self.sample_data)
        summary = self.analyzer.get_cost_summary(processed_df)
        
        # Check summary structure
        assert 'period' in summary
        assert 'total_cost' in summary
        assert 'cost_by_category' in summary
        
        # Check values
        assert summary['total_cost']['current_week'] == 1200
        assert summary['total_cost']['total_period'] == sum(self.sample_data['total_cost'])
        assert 'infrastructure' in summary['cost_by_category']
    
    def test_identify_cost_drivers(self):
        """Test cost driver identification"""
        processed_df = self.analyzer.process_weekly_data(self.sample_data)
        drivers = self.analyzer.identify_cost_drivers(processed_df, top_n=3)
        
        assert len(drivers) <= 3
        assert all('category' in driver for driver in drivers)
        assert all('current_cost' in driver for driver in drivers)
        assert all('impact_score' in driver for driver in drivers)
    
    def test_calculate_forecast(self):
        """Test cost forecasting"""
        processed_df = self.analyzer.process_weekly_data(self.sample_data)
        forecast = self.analyzer.calculate_forecast(processed_df, weeks_ahead=4)
        
        assert 'forecast_weeks' in forecast
        assert forecast['forecast_weeks'] == 4
        assert 'categories' in forecast
        assert 'total' in forecast['categories']
        
        total_forecast = forecast['categories']['total']
        assert 'forecasted_values' in total_forecast
        assert len(total_forecast['forecasted_values']) == 4


class TestAnomalyDetector:
    """Test the AnomalyDetector class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.detector = AnomalyDetector()
        
        # Create sample data with anomalies
        dates = pd.date_range(start='2024-01-01', periods=12, freq='W')
        normal_costs = [1000, 1100, 950, 1200, 1050, 1300, 1150, 1400, 1250, 1100, 1350, 1200]
        # Add some anomalies
        normal_costs[5] = 2500  # High anomaly
        normal_costs[8] = 500   # Low anomaly
        
        self.sample_data = pd.DataFrame({
            'week_start': dates,
            'week_end': dates + timedelta(days=6),
            'total_cost': normal_costs,
            'infrastructure_cost': [c * 0.4 for c in normal_costs],
            'logs_cost': [c * 0.3 for c in normal_costs],
            'metrics_cost': [c * 0.2 for c in normal_costs],
            'traces_cost': [c * 0.1 for c in normal_costs]
        })
        
        # Add week-over-week changes
        self.sample_data['total_wow_change'] = self.sample_data['total_cost'].pct_change() * 100
    
    def test_detect_anomalies(self):
        """Test anomaly detection"""
        anomalies = self.detector.detect_anomalies(self.sample_data)
        
        # Check structure
        assert 'summary' in anomalies
        assert 'methods' in anomalies
        assert 'category_analysis' in anomalies
        assert 'recommendations' in anomalies
        
        # Should detect some anomalies
        assert anomalies['summary']['total_anomalies'] > 0
        
        # Check severity distribution
        severity = anomalies['summary']['severity_distribution']
        assert 'high' in severity
        assert 'medium' in severity
        assert 'low' in severity
    
    def test_z_score_detection(self):
        """Test Z-score anomaly detection"""
        z_anomalies = self.detector._detect_z_score_anomalies(self.sample_data, ['total'])
        
        assert 'method' in z_anomalies
        assert z_anomalies['method'] == 'z_score'
        assert 'results' in z_anomalies
        
        if 'total' in z_anomalies['results']:
            assert 'anomaly_count' in z_anomalies['results']['total']
    
    def test_iqr_detection(self):
        """Test IQR anomaly detection"""
        iqr_anomalies = self.detector._detect_iqr_anomalies(self.sample_data, ['total'])
        
        assert 'method' in iqr_anomalies
        assert iqr_anomalies['method'] == 'iqr'
        assert 'results' in iqr_anomalies


class TestCostVisualizer:
    """Test the CostVisualizer class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.visualizer = CostVisualizer()
        
        # Create sample data
        dates = pd.date_range(start='2024-01-01', periods=8, freq='W')
        self.sample_data = pd.DataFrame({
            'week_start': dates,
            'week_end': dates + timedelta(days=6),
            'total_cost': [1000, 1100, 950, 1200, 1050, 1300, 1150, 1400],
            'infrastructure_cost': [400, 440, 380, 480, 420, 520, 460, 560],
            'logs_cost': [300, 330, 285, 360, 315, 390, 345, 420],
            'metrics_cost': [200, 220, 190, 240, 210, 260, 230, 280],
            'traces_cost': [100, 110, 95, 120, 105, 130, 115, 140],
            'total_wow_change': [0, 10, -13.6, 26.3, -12.5, 23.8, -11.5, 21.7]
        })
    
    def test_create_cost_trend_chart(self):
        """Test cost trend chart creation"""
        fig = self.visualizer.create_cost_trend_chart(self.sample_data)
        
        assert fig is not None
        assert hasattr(fig, 'data')
        assert len(fig.data) > 0
    
    def test_create_stacked_cost_chart(self):
        """Test stacked cost chart creation"""
        fig = self.visualizer.create_stacked_cost_chart(self.sample_data)
        
        assert fig is not None
        assert hasattr(fig, 'data')
        assert len(fig.data) > 0
    
    def test_create_cost_distribution_chart(self):
        """Test cost distribution chart creation"""
        fig = self.visualizer.create_cost_distribution_chart(self.sample_data)
        
        assert fig is not None
        assert hasattr(fig, 'data')
        assert len(fig.data) > 0
    
    def test_create_week_over_week_chart(self):
        """Test week-over-week chart creation"""
        fig = self.visualizer.create_week_over_week_chart(self.sample_data)
        
        assert fig is not None
        assert hasattr(fig, 'data')
    
    def test_empty_data_handling(self):
        """Test handling of empty data"""
        empty_df = pd.DataFrame()
        fig = self.visualizer.create_cost_trend_chart(empty_df)
        
        assert fig is not None
        # Should create an empty chart with a message


class TestConfigManager:
    """Test the ConfigManager class"""
    
    def test_default_config(self):
        """Test default configuration loading"""
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        assert 'datadog' in config
        assert 'analysis' in config
        assert 'web' in config
        assert 'logging' in config
    
    def test_get_value(self):
        """Test getting configuration values"""
        config_manager = ConfigManager()
        
        # Test existing value
        lookback = config_manager.get_value('analysis.lookback_weeks', 0)
        assert lookback > 0
        
        # Test non-existing value with default
        non_existing = config_manager.get_value('non.existing.key', 'default')
        assert non_existing == 'default'
    
    def test_set_value(self):
        """Test setting configuration values"""
        config_manager = ConfigManager()
        
        config_manager.set_value('test.key', 'test_value')
        assert config_manager.get_value('test.key') == 'test_value'
    
    def test_validate_config(self):
        """Test configuration validation"""
        config_manager = ConfigManager()
        validation = config_manager.validate_config()
        
        assert 'valid' in validation
        assert 'errors' in validation
        assert 'warnings' in validation


if __name__ == '__main__':
    pytest.main([__file__, '-v'])