"""
Tests for the Datadog Notebook Creator functionality
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from src.datadog_cost_analyzer.integrations.notebook_creator import DatadogNotebookCreator


class TestDatadogNotebookCreator:
    """Test the DatadogNotebookCreator class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.api_key = "test_api_key"
        self.app_key = "test_app_key"
        self.site = "datadoghq.com"
        
        # Mock the Datadog API client
        with patch('src.datadog_cost_analyzer.integrations.notebook_creator.ApiClient'), \
             patch('src.datadog_cost_analyzer.integrations.notebook_creator.NotebooksApi'):
            self.notebook_creator = DatadogNotebookCreator(
                api_key=self.api_key,
                app_key=self.app_key,
                site=self.site
            )
        
        # Sample anomaly results
        self.sample_anomaly_results = {
            'summary': {
                'total_anomalies': 3,
                'anomaly_weeks': ['2024-01-01', '2024-01-08', '2024-01-15'],
                'severity_distribution': {'low': 1, 'medium': 1, 'high': 1}
            },
            'methods': {
                'z_score': {
                    'method': 'z_score',
                    'threshold': 2.5,
                    'results': {
                        'logs': {
                            'anomaly_count': 2,
                            'anomaly_weeks': ['2024-01-01', '2024-01-08'],
                            'anomaly_values': [1000.0, 1200.0],
                            'z_scores': [3.2, 2.8],
                            'severity': {'low': 0, 'medium': 1, 'high': 1}
                        }
                    }
                },
                'iqr': {
                    'method': 'iqr',
                    'multiplier': 1.5,
                    'results': {
                        'infrastructure': {
                            'anomaly_count': 1,
                            'anomaly_weeks': ['2024-01-15'],
                            'anomaly_values': [800.0],
                            'bounds': {'lower': 100.0, 'upper': 600.0},
                            'severity': {'low': 1, 'medium': 0, 'high': 0}
                        }
                    }
                }
            },
            'category_analysis': {
                'logs': {
                    'anomaly_frequency': 2,
                    'avg_severity': 2.5,
                    'most_common_methods': ['z_score', 'iqr']
                },
                'infrastructure': {
                    'anomaly_frequency': 1,
                    'avg_severity': 1.0,
                    'most_common_methods': ['iqr']
                }
            },
            'recommendations': [
                {
                    'type': 'alert',
                    'priority': 'high',
                    'title': 'Recent Cost Anomalies',
                    'description': 'Detected 2 anomalies in the last 2 weeks.',
                    'action': 'Investigate recent changes in infrastructure or usage patterns.'
                }
            ]
        }
        
        # Sample cost data
        self.sample_cost_data = {
            'total_cost': 5000.0,
            'period': 'Last 12 weeks',
            'trend': 'increasing',
            'categories': {
                'logs': 2500.0,
                'infrastructure': 1500.0,
                'apm': 1000.0
            },
            'forecast': {
                'next_week': 450.0,
                'next_month': 1800.0
            }
        }
    
    def test_initialization(self):
        """Test notebook creator initialization"""
        assert self.notebook_creator.configuration.api_key["apiKeyAuth"] == self.api_key
        assert self.notebook_creator.configuration.api_key["appKeyAuth"] == self.app_key
        assert self.notebook_creator.configuration.server_variables["site"] == self.site
    
    @patch('src.datadog_cost_analyzer.integrations.notebook_creator.NotebooksApi.create_notebook')
    def test_create_cost_anomaly_notebook_success(self, mock_create_notebook):
        """Test successful notebook creation"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.data.id = "test-notebook-id"
        mock_create_notebook.return_value = mock_response
        
        result = self.notebook_creator.create_cost_anomaly_notebook(
            self.sample_anomaly_results,
            self.sample_cost_data,
            title="Test Notebook",
            tags=["test", "cost-analysis"]
        )
        
        assert result['success'] is True
        assert result['notebook_id'] == "test-notebook-id"
        assert "notebook_url" in result
        assert result['title'] == "Test Notebook"
        assert "created_at" in result
        assert result['cell_count'] > 0
        assert "test" in result['tags']
        assert "cost-analysis" in result['tags']
        
        # Verify API was called
        mock_create_notebook.assert_called_once()
    
    @patch('src.datadog_cost_analyzer.integrations.notebook_creator.NotebooksApi.create_notebook')
    def test_create_cost_anomaly_notebook_failure(self, mock_create_notebook):
        """Test notebook creation failure"""
        # Mock API failure
        mock_create_notebook.side_effect = Exception("API Error")
        
        result = self.notebook_creator.create_cost_anomaly_notebook(
            self.sample_anomaly_results,
            self.sample_cost_data
        )
        
        assert result['success'] is False
        assert "error" in result
        assert "API Error" in result['error']
    
    def test_create_notebook_cells(self):
        """Test notebook cell creation"""
        cells = self.notebook_creator._create_notebook_cells(
            self.sample_anomaly_results,
            self.sample_cost_data
        )
        
        assert len(cells) == 8  # Expected number of cells
        
        # Verify all cells have proper structure
        for cell in cells:
            assert "attributes" in cell
            assert "type" in cell
            assert "definition" in cell["attributes"]
    
    def test_executive_summary_cell(self):
        """Test executive summary cell creation"""
        cell = self.notebook_creator._create_executive_summary_cell(
            self.sample_anomaly_results,
            self.sample_cost_data
        )
        
        assert str(cell["type"]) == "notebook_cells"
        definition = cell["attributes"]["definition"]
        assert str(definition.type) == "markdown"
        assert "Executive Summary" in definition.text
        assert "3" in definition.text  # Total anomalies
        assert "$5,000.00" in definition.text  # Total cost
    
    def test_anomaly_overview_cell(self):
        """Test anomaly overview cell creation"""
        cell = self.notebook_creator._create_anomaly_overview_cell(
            self.sample_anomaly_results
        )
        
        definition = cell["attributes"]["definition"]
        assert "Anomaly Detection Overview" in definition.text
        assert "Z-Score Analysis" in definition.text
        assert "IQR" in definition.text
        assert "Isolation Forest" in definition.text
        assert "Seasonal Decomposition" in definition.text
        assert "Week-over-Week" in definition.text
    
    def test_cost_trend_cell(self):
        """Test cost trend analysis cell creation"""
        cell = self.notebook_creator._create_cost_trend_cell(
            self.sample_cost_data
        )
        
        definition = cell["attributes"]["definition"]
        assert "Cost Trend Analysis" in definition.text
        assert "Increasing Trend" in definition.text  # Based on sample data
        assert "$5,000.00" in definition.text
    
    def test_methods_analysis_cell(self):
        """Test methods analysis cell creation"""
        cell = self.notebook_creator._create_methods_analysis_cell(
            self.sample_anomaly_results
        )
        
        definition = cell["attributes"]["definition"]
        assert "Detailed Anomaly Detection Results" in definition.text
        assert "Z Score Results" in definition.text
        assert "Iqr Results" in definition.text
    
    def test_category_analysis_cell(self):
        """Test category analysis cell creation"""
        cell = self.notebook_creator._create_category_analysis_cell(
            self.sample_anomaly_results
        )
        
        definition = cell["attributes"]["definition"]
        assert "Category-wise Anomaly Analysis" in definition.text
        assert "logs" in definition.text.lower()
        assert "infrastructure" in definition.text.lower()
    
    def test_recommendations_cell_with_recommendations(self):
        """Test recommendations cell with actual recommendations"""
        cell = self.notebook_creator._create_recommendations_cell(
            self.sample_anomaly_results
        )
        
        definition = cell["attributes"]["definition"]
        assert "Recommendations & Action Items" in definition.text
        assert "Recent Cost Anomalies" in definition.text
        assert "high" in definition.text.lower()
    
    def test_recommendations_cell_no_recommendations(self):
        """Test recommendations cell with no recommendations"""
        empty_results = {'recommendations': []}
        
        cell = self.notebook_creator._create_recommendations_cell(empty_results)
        
        definition = cell["attributes"]["definition"]
        assert "No Critical Issues Found" in definition.text
        assert "Proactive Monitoring Suggestions" in definition.text
    
    def test_investigation_queries_cell(self):
        """Test investigation queries cell creation"""
        cell = self.notebook_creator._create_investigation_queries_cell(
            self.sample_anomaly_results
        )
        
        definition = cell["attributes"]["definition"]
        assert "Investigation Queries & Next Steps" in definition.text
        assert "sum:datadog.estimated_usage" in definition.text
        assert "Investigation Checklist" in definition.text
        assert "Next Review Schedule" in definition.text
    
    def test_timeseries_cell(self):
        """Test timeseries visualization cell creation"""
        cell = self.notebook_creator._create_timeseries_cell(
            self.sample_cost_data
        )
        
        definition = cell["attributes"]["definition"]
        assert str(definition.type) == "markdown"
        assert "Cost Usage Visualization" in definition.text
        assert "sum:datadog.estimated_usage.billable_ingested_bytes" in definition.text
        assert "Usage Attribution Dashboard" in definition.text
    
    def test_generate_impact_assessment(self):
        """Test impact assessment generation"""
        # Test no anomalies
        no_anomalies = {'summary': {'total_anomalies': 0}}
        impact = self.notebook_creator._generate_impact_assessment(no_anomalies, self.sample_cost_data)
        assert "Low Impact" in impact
        
        # Test few anomalies
        few_anomalies = {'summary': {'total_anomalies': 2}}
        impact = self.notebook_creator._generate_impact_assessment(few_anomalies, self.sample_cost_data)
        assert "Medium Impact" in impact
        
        # Test many anomalies
        many_anomalies = {'summary': {'total_anomalies': 5}}
        impact = self.notebook_creator._generate_impact_assessment(many_anomalies, self.sample_cost_data)
        assert "High Impact" in impact
    
    def test_format_anomaly_weeks(self):
        """Test anomaly weeks formatting"""
        weeks = ['2024-01-01', '2024-01-08', '2024-01-15']
        formatted = self.notebook_creator._format_anomaly_weeks(weeks)
        
        assert "2024-01-01" in formatted
        assert "2024-01-08" in formatted
        assert "2024-01-15" in formatted
        
        # Test empty weeks
        empty_formatted = self.notebook_creator._format_anomaly_weeks([])
        assert "No anomalous weeks detected" in empty_formatted
        
        # Test many weeks (should truncate)
        many_weeks = [f"2024-01-{i:02d}" for i in range(1, 20)]
        many_formatted = self.notebook_creator._format_anomaly_weeks(many_weeks)
        assert "and 8 more weeks" in many_formatted
    
    def test_generate_method_performance_summary(self):
        """Test method performance summary generation"""
        summary = self.notebook_creator._generate_method_performance_summary(
            self.sample_anomaly_results
        )
        
        assert "Z Score" in summary
        assert "Iqr" in summary
        assert "anomalies detected" in summary
    
    def test_generate_cost_trend_analysis(self):
        """Test cost trend analysis generation"""
        # Test increasing trend
        increasing_data = {'trend': 'increasing', 'total_cost': 5000.0}
        analysis = self.notebook_creator._generate_cost_trend_analysis(increasing_data)
        assert "Increasing Trend" in analysis
        assert "$5,000.00" in analysis
        
        # Test stable trend
        stable_data = {'trend': 'stable', 'total_cost': 3000.0}
        analysis = self.notebook_creator._generate_cost_trend_analysis(stable_data)
        assert "Stable Trend" in analysis
        assert "$3,000.00" in analysis
    
    def test_generate_category_performance(self):
        """Test category performance generation"""
        performance = self.notebook_creator._generate_category_performance(
            self.sample_cost_data
        )
        
        assert "Logs: $2,500.00" in performance
        assert "Infrastructure: $1,500.00" in performance
        assert "Apm: $1,000.00" in performance
    
    def test_generate_forecasting_insights(self):
        """Test forecasting insights generation"""
        insights = self.notebook_creator._generate_forecasting_insights(
            self.sample_cost_data
        )
        
        assert "Next Week Estimate: $450.00" in insights
        assert "Next Month Estimate: $1,800.00" in insights
        assert "historical patterns" in insights
    
    @patch('src.datadog_cost_analyzer.integrations.notebook_creator.NotebooksApi.get_notebook')
    @patch('src.datadog_cost_analyzer.integrations.notebook_creator.NotebooksApi.update_notebook')
    def test_update_notebook_success(self, mock_update_notebook, mock_get_notebook):
        """Test successful notebook update"""
        # Mock existing notebook
        mock_existing = Mock()
        mock_existing.data.attributes.metadata = {"update_count": 1}
        mock_get_notebook.return_value = mock_existing
        
        # Mock update response
        mock_update_response = Mock()
        mock_update_notebook.return_value = mock_update_response
        
        result = self.notebook_creator.update_notebook(
            "test-notebook-id",
            self.sample_anomaly_results,
            self.sample_cost_data
        )
        
        assert result['success'] is True
        assert result['notebook_id'] == "test-notebook-id"
        assert "updated_at" in result
        
        # Verify API calls
        mock_get_notebook.assert_called_once_with("test-notebook-id")
        mock_update_notebook.assert_called_once()
    
    @patch('src.datadog_cost_analyzer.integrations.notebook_creator.NotebooksApi.get_notebook')
    def test_update_notebook_failure(self, mock_get_notebook):
        """Test notebook update failure"""
        # Mock API failure
        mock_get_notebook.side_effect = Exception("Notebook not found")
        
        result = self.notebook_creator.update_notebook(
            "invalid-notebook-id",
            self.sample_anomaly_results,
            self.sample_cost_data
        )
        
        assert result['success'] is False
        assert "error" in result
        assert "Notebook not found" in result['error']
    
    @patch('src.datadog_cost_analyzer.integrations.notebook_creator.NotebooksApi.list_notebooks')
    def test_list_cost_analysis_notebooks_success(self, mock_list_notebooks):
        """Test successful notebook listing"""
        # Mock API response
        mock_notebook1 = Mock()
        mock_notebook1.id = "notebook-1"
        mock_notebook1.attributes.name = "Cost Analysis 1"
        mock_notebook1.attributes.created_at = datetime.now()
        mock_notebook1.attributes.modified_at = datetime.now()
        mock_notebook1.attributes.tags = ["cost-analysis", "test"]
        
        mock_notebook2 = Mock()
        mock_notebook2.id = "notebook-2"
        mock_notebook2.attributes.name = "Cost Analysis 2"
        mock_notebook2.attributes.created_at = datetime.now()
        mock_notebook2.attributes.modified_at = datetime.now()
        mock_notebook2.attributes.tags = ["cost-analysis"]
        
        mock_response = Mock()
        mock_response.data = [mock_notebook1, mock_notebook2]
        mock_list_notebooks.return_value = mock_response
        
        notebooks = self.notebook_creator.list_cost_analysis_notebooks()
        
        assert len(notebooks) == 2
        assert notebooks[0]['id'] == "notebook-1"
        assert notebooks[0]['name'] == "Cost Analysis 1"
        assert notebooks[1]['id'] == "notebook-2"
        assert notebooks[1]['name'] == "Cost Analysis 2"
        
        # Verify API call
        mock_list_notebooks.assert_called_once_with(tags=["cost-analysis"])
    
    @patch('src.datadog_cost_analyzer.integrations.notebook_creator.NotebooksApi.list_notebooks')
    def test_list_cost_analysis_notebooks_failure(self, mock_list_notebooks):
        """Test notebook listing failure"""
        # Mock API failure
        mock_list_notebooks.side_effect = Exception("API Error")
        
        notebooks = self.notebook_creator.list_cost_analysis_notebooks()
        
        assert notebooks == []
    
    def test_format_method_results(self):
        """Test method results formatting"""
        method_results = {
            'results': {
                'logs': {'anomaly_count': 2},
                'infrastructure': {'anomaly_count': 1},
                'empty_category': {'anomaly_count': 0}
            }
        }
        
        formatted = self.notebook_creator._format_method_results('z_score', method_results)
        
        assert "Logs: 2 anomalies" in formatted
        assert "Infrastructure: 1 anomalies" in formatted
        assert "empty_category" not in formatted  # Should skip zero counts
    
    def test_format_category_analysis(self):
        """Test category analysis formatting"""
        category_analysis = {
            'logs': {
                'anomaly_frequency': 3,
                'most_common_methods': ['z_score', 'iqr', 'isolation_forest']
            },
            'infrastructure': {
                'anomaly_frequency': 1,
                'most_common_methods': ['seasonal_decomposition']
            },
            'no_anomalies': {
                'anomaly_frequency': 0,
                'most_common_methods': []
            }
        }
        
        formatted = self.notebook_creator._format_category_analysis(category_analysis)
        
        assert "Logs: 3 anomalies" in formatted
        assert "z_score, iqr, isolation_forest" in formatted
        assert "Infrastructure: 1 anomalies" in formatted
        assert "seasonal_decomposition" in formatted
        assert "no_anomalies" not in formatted  # Should skip zero frequency
    
    def test_generate_category_risk_assessment(self):
        """Test category risk assessment generation"""
        category_analysis = {
            'high_risk': {'anomaly_frequency': 5},
            'medium_risk': {'anomaly_frequency': 2},
            'low_risk': {'anomaly_frequency': 0}
        }
        
        assessment = self.notebook_creator._generate_category_risk_assessment(category_analysis)
        
        assert "High Risk Categories: high_risk" in assessment
        assert "Medium Risk Categories: medium_risk" in assessment
        assert "low_risk" not in assessment  # Should not appear in risk categories


if __name__ == '__main__':
    pytest.main([__file__, '-v'])