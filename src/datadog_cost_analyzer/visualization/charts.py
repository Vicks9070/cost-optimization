"""
Interactive charts and visualizations for cost analysis
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CostVisualizer:
    """Create interactive visualizations for cost analysis"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the cost visualizer
        
        Args:
            config: Configuration dictionary with visualization parameters
        """
        self.config = config or {}
        self.color_palette = self.config.get('color_palette', px.colors.qualitative.Set3)
        self.theme = self.config.get('theme', 'plotly_white')
        
        # Set default styling
        self.default_layout = {
            'template': self.theme,
            'font': {'size': 12},
            'title': {'font': {'size': 16}},
            'showlegend': True,
            'hovermode': 'x unified'
        }
        
        logger.info("Initialized CostVisualizer")
    
    def create_cost_trend_chart(self, df: pd.DataFrame, categories: Optional[List[str]] = None) -> go.Figure:
        """
        Create an interactive cost trend chart
        
        Args:
            df: Cost data DataFrame
            categories: List of cost categories to include
            
        Returns:
            Plotly figure object
        """
        if df.empty:
            return self._create_empty_chart("No data available for cost trend chart")
        
        if categories is None:
            categories = [col.replace('_cost', '') for col in df.columns if col.endswith('_cost') and col != 'total_cost']
        
        fig = go.Figure()
        
        # Add total cost line
        fig.add_trace(go.Scatter(
            x=df['week_start'],
            y=df['total_cost'],
            mode='lines+markers',
            name='Total Cost',
            line=dict(width=3, color='#1f77b4'),
            marker=dict(size=8),
            hovertemplate='<b>Total Cost</b><br>Week: %{x}<br>Cost: $%{y:,.2f}<extra></extra>'
        ))
        
        # Add category breakdown as stacked area chart
        fig_stacked = self.create_stacked_cost_chart(df, categories)
        
        # Update layout
        layout_config = self.default_layout.copy()
        layout_config.update({
            'title': 'Weekly Cost Trends',
            'xaxis_title': 'Week',
            'yaxis_title': 'Cost ($)'
        })
        fig.update_layout(**layout_config)
        
        return fig
    
    def create_stacked_cost_chart(self, df: pd.DataFrame, categories: Optional[List[str]] = None) -> go.Figure:
        """
        Create a stacked area chart showing cost breakdown by category
        
        Args:
            df: Cost data DataFrame
            categories: List of cost categories to include
            
        Returns:
            Plotly figure object
        """
        if df.empty:
            return self._create_empty_chart("No data available for stacked cost chart")
        
        if categories is None:
            categories = [col.replace('_cost', '') for col in df.columns if col.endswith('_cost') and col != 'total_cost']
        
        fig = go.Figure()
        
        # Add each category as a stacked area
        for i, category in enumerate(categories):
            cost_col = f'{category}_cost'
            if cost_col in df.columns:
                fig.add_trace(go.Scatter(
                    x=df['week_start'],
                    y=df[cost_col],
                    mode='lines',
                    stackgroup='one',
                    name=category.title(),
                    line=dict(width=0),
                    fillcolor=self.color_palette[i % len(self.color_palette)],
                    hovertemplate=f'<b>{category.title()}</b><br>Week: %{{x}}<br>Cost: $%{{y:,.2f}}<extra></extra>'
                ))
        
        layout_config = self.default_layout.copy()
        layout_config.update({
            'title': 'Cost Breakdown by Category (Stacked)',
            'xaxis_title': 'Week',
            'yaxis_title': 'Cost ($)'
        })
        fig.update_layout(**layout_config)
        
        return fig
    
    def create_anomaly_chart(self, df: pd.DataFrame, anomaly_results: Dict[str, Any]) -> go.Figure:
        """
        Create a chart highlighting cost anomalies
        
        Args:
            df: Cost data DataFrame
            anomaly_results: Results from anomaly detection
            
        Returns:
            Plotly figure object
        """
        if df.empty:
            return self._create_empty_chart("No data available for anomaly chart")
        
        fig = go.Figure()
        
        # Add total cost line
        fig.add_trace(go.Scatter(
            x=df['week_start'],
            y=df['total_cost'],
            mode='lines+markers',
            name='Total Cost',
            line=dict(width=2, color='#1f77b4'),
            marker=dict(size=6),
            hovertemplate='<b>Total Cost</b><br>Week: %{x}<br>Cost: $%{y:,.2f}<extra></extra>'
        ))
        
        # Highlight anomaly weeks
        if 'summary' in anomaly_results and 'anomaly_weeks' in anomaly_results['summary']:
            anomaly_weeks = anomaly_results['summary']['anomaly_weeks']
            
            for week_str in anomaly_weeks:
                week_date = pd.to_datetime(week_str)
                week_data = df[df['week_start'] == week_date]
                
                if not week_data.empty:
                    severity = self._get_week_severity(week_str, anomaly_results)
                    color = self._get_severity_color(severity)
                    
                    fig.add_trace(go.Scatter(
                        x=[week_date],
                        y=[week_data['total_cost'].iloc[0]],
                        mode='markers',
                        name=f'Anomaly ({severity})',
                        marker=dict(
                            size=15,
                            color=color,
                            symbol='diamond',
                            line=dict(width=2, color='white')
                        ),
                        hovertemplate=f'<b>Anomaly Detected</b><br>Week: %{{x}}<br>Cost: $%{{y:,.2f}}<br>Severity: {severity}<extra></extra>',
                        showlegend=False
                    ))
        
        # Add confidence bands (mean ± 2 std dev)
        mean_cost = df['total_cost'].mean()
        std_cost = df['total_cost'].std()
        
        fig.add_hline(
            y=mean_cost + 2 * std_cost,
            line_dash="dash",
            line_color="red",
            annotation_text="Upper Threshold (+2σ)",
            annotation_position="top right"
        )
        
        fig.add_hline(
            y=mean_cost - 2 * std_cost,
            line_dash="dash",
            line_color="red",
            annotation_text="Lower Threshold (-2σ)",
            annotation_position="bottom right"
        )
        
        layout_config = self.default_layout.copy()
        layout_config.update({
            'title': 'Cost Anomaly Detection',
            'xaxis_title': 'Week',
            'yaxis_title': 'Cost ($)'
        })
        fig.update_layout(**layout_config)
        
        return fig
    
    def create_cost_distribution_chart(self, df: pd.DataFrame, categories: Optional[List[str]] = None) -> go.Figure:
        """
        Create a pie chart showing current cost distribution
        
        Args:
            df: Cost data DataFrame
            categories: List of cost categories to include
            
        Returns:
            Plotly figure object
        """
        if df.empty:
            return self._create_empty_chart("No data available for cost distribution chart")
        
        if categories is None:
            categories = [col.replace('_cost', '') for col in df.columns if col.endswith('_cost') and col != 'total_cost']
        
        # Get latest week data
        latest_week = df.iloc[-1]
        
        # Prepare data for pie chart
        labels = []
        values = []
        colors = []
        
        for i, category in enumerate(categories):
            cost_col = f'{category}_cost'
            if cost_col in df.columns and latest_week[cost_col] > 0:
                labels.append(category.title())
                values.append(latest_week[cost_col])
                colors.append(self.color_palette[i % len(self.color_palette)])
        
        if not values:
            return self._create_empty_chart("No cost data available for distribution chart")
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            marker_colors=colors,
            hovertemplate='<b>%{label}</b><br>Cost: $%{value:,.2f}<br>Percentage: %{percent}<extra></extra>',
            textinfo='label+percent',
            textposition='auto'
        )])
        
        layout_config = self.default_layout.copy()
        layout_config.update({
            'title': f'Cost Distribution - Week of {latest_week["week_start"].strftime("%Y-%m-%d")}'
        })
        fig.update_layout(**layout_config)
        
        return fig
    
    def create_week_over_week_chart(self, df: pd.DataFrame, categories: Optional[List[str]] = None) -> go.Figure:
        """
        Create a chart showing week-over-week changes
        
        Args:
            df: Cost data DataFrame
            categories: List of cost categories to include
            
        Returns:
            Plotly figure object
        """
        if df.empty or len(df) < 2:
            return self._create_empty_chart("Insufficient data for week-over-week chart")
        
        if categories is None:
            categories = [col.replace('_wow_change', '') for col in df.columns if col.endswith('_wow_change') and col != 'total_wow_change']
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Total Cost Week-over-Week Change (%)', 'Category Breakdown'),
            vertical_spacing=0.1,
            row_heights=[0.4, 0.6]
        )
        
        # Total cost change
        fig.add_trace(
            go.Scatter(
                x=df['week_start'],
                y=df['total_wow_change'],
                mode='lines+markers',
                name='Total Change %',
                line=dict(width=3, color='#1f77b4'),
                marker=dict(size=8),
                hovertemplate='<b>Total Change</b><br>Week: %{x}<br>Change: %{y:.1f}%<extra></extra>'
            ),
            row=1, col=1
        )
        
        # Add zero line
        fig.add_hline(y=0, line_dash="dash", line_color="gray", row=1, col=1)
        
        # Category changes
        for i, category in enumerate(categories):
            change_col = f'{category}_wow_change'
            if change_col in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df['week_start'],
                        y=df[change_col],
                        mode='lines+markers',
                        name=category.title(),
                        line=dict(width=2),
                        marker=dict(size=6),
                        hovertemplate=f'<b>{category.title()}</b><br>Week: %{{x}}<br>Change: %{{y:.1f}}%<extra></extra>'
                    ),
                    row=2, col=1
                )
        
        # Add zero line for categories
        fig.add_hline(y=0, line_dash="dash", line_color="gray", row=2, col=1)
        
        layout_config = self.default_layout.copy()
        layout_config.update({
            'title': 'Week-over-Week Cost Changes'
        })
        fig.update_layout(**layout_config)
        
        fig.update_xaxes(title_text="Week", row=2, col=1)
        fig.update_yaxes(title_text="Change (%)", row=1, col=1)
        fig.update_yaxes(title_text="Change (%)", row=2, col=1)
        
        return fig
    
    def create_forecast_chart(self, df: pd.DataFrame, forecast_data: Dict[str, Any]) -> go.Figure:
        """
        Create a chart showing cost forecasts
        
        Args:
            df: Historical cost data DataFrame
            forecast_data: Forecast results from analyzer
            
        Returns:
            Plotly figure object
        """
        if df.empty or not forecast_data:
            return self._create_empty_chart("No data available for forecast chart")
        
        fig = go.Figure()
        
        # Historical total cost
        fig.add_trace(go.Scatter(
            x=df['week_start'],
            y=df['total_cost'],
            mode='lines+markers',
            name='Historical Cost',
            line=dict(width=3, color='#1f77b4'),
            marker=dict(size=8),
            hovertemplate='<b>Historical</b><br>Week: %{x}<br>Cost: $%{y:,.2f}<extra></extra>'
        ))
        
        # Forecast
        if 'categories' in forecast_data and 'total' in forecast_data['categories']:
            forecast_weeks = forecast_data.get('forecast_weeks', 4)
            last_date = df['week_start'].max()
            
            # Generate future dates
            future_dates = [last_date + timedelta(weeks=i+1) for i in range(forecast_weeks)]
            forecast_values = forecast_data['categories']['total']['forecasted_values']
            
            # Add forecast line
            fig.add_trace(go.Scatter(
                x=future_dates,
                y=forecast_values,
                mode='lines+markers',
                name='Forecast',
                line=dict(width=3, color='#ff7f0e', dash='dash'),
                marker=dict(size=8, symbol='diamond'),
                hovertemplate='<b>Forecast</b><br>Week: %{x}<br>Cost: $%{y:,.2f}<extra></extra>'
            ))
            
            # Add confidence interval (simple approach using trend confidence)
            confidence = forecast_data['categories']['total'].get('confidence', 0.5)
            error_margin = [(1 - confidence) * val * 0.5 for val in forecast_values]
            
            upper_bound = [val + err for val, err in zip(forecast_values, error_margin)]
            lower_bound = [val - err for val, err in zip(forecast_values, error_margin)]
            
            fig.add_trace(go.Scatter(
                x=future_dates + future_dates[::-1],
                y=upper_bound + lower_bound[::-1],
                fill='toself',
                fillcolor='rgba(255, 127, 14, 0.2)',
                line=dict(color='rgba(255,255,255,0)'),
                name='Confidence Interval',
                hoverinfo='skip',
                showlegend=True
            ))
        
        layout_config = self.default_layout.copy()
        layout_config.update({
            'title': 'Cost Forecast',
            'xaxis_title': 'Week',
            'yaxis_title': 'Cost ($)'
        })
        fig.update_layout(**layout_config)
        
        return fig
    
    def create_efficiency_chart(self, df: pd.DataFrame) -> go.Figure:
        """
        Create a chart showing cost efficiency metrics
        
        Args:
            df: Cost data DataFrame with efficiency metrics
            
        Returns:
            Plotly figure object
        """
        efficiency_cols = [col for col in df.columns if col.startswith('cost_per_')]
        
        if not efficiency_cols:
            return self._create_empty_chart("No efficiency metrics available")
        
        fig = make_subplots(
            rows=len(efficiency_cols), cols=1,
            subplot_titles=[col.replace('cost_per_', '').replace('_', ' ').title() for col in efficiency_cols],
            vertical_spacing=0.05
        )
        
        for i, col in enumerate(efficiency_cols):
            metric_name = col.replace('cost_per_', '').replace('_', ' ').title()
            
            fig.add_trace(
                go.Scatter(
                    x=df['week_start'],
                    y=df[col],
                    mode='lines+markers',
                    name=metric_name,
                    line=dict(width=2),
                    marker=dict(size=6),
                    hovertemplate=f'<b>{metric_name}</b><br>Week: %{{x}}<br>Cost: $%{{y:.4f}}<extra></extra>'
                ),
                row=i+1, col=1
            )
            
            # Add trend line
            if len(df) > 2:
                z = np.polyfit(range(len(df)), df[col], 1)
                trend_line = np.poly1d(z)(range(len(df)))
                
                fig.add_trace(
                    go.Scatter(
                        x=df['week_start'],
                        y=trend_line,
                        mode='lines',
                        name=f'{metric_name} Trend',
                        line=dict(width=1, dash='dash'),
                        hoverinfo='skip',
                        showlegend=False
                    ),
                    row=i+1, col=1
                )
        
        layout_config = self.default_layout.copy()
        layout_config.update({
            'title': 'Cost Efficiency Metrics'
        })
        fig.update_layout(**layout_config)
        
        return fig
    
    def create_dashboard_summary(self, df: pd.DataFrame, summary: Dict[str, Any], 
                                anomaly_results: Dict[str, Any]) -> go.Figure:
        """
        Create a comprehensive dashboard summary
        
        Args:
            df: Cost data DataFrame
            summary: Cost summary statistics
            anomaly_results: Anomaly detection results
            
        Returns:
            Plotly figure object
        """
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Weekly Cost Trend',
                'Cost Distribution',
                'Recent Anomalies',
                'Top Cost Drivers'
            ),
            specs=[[{"secondary_y": False}, {"type": "pie"}],
                   [{"secondary_y": False}, {"type": "bar"}]],
            vertical_spacing=0.1,
            horizontal_spacing=0.1
        )
        
        # 1. Weekly trend (simplified)
        fig.add_trace(
            go.Scatter(
                x=df['week_start'].tail(8),
                y=df['total_cost'].tail(8),
                mode='lines+markers',
                name='Total Cost',
                line=dict(width=2, color='#1f77b4'),
                showlegend=False
            ),
            row=1, col=1
        )
        
        # 2. Cost distribution (latest week)
        if 'cost_by_category' in summary:
            categories = list(summary['cost_by_category'].keys())[:6]  # Top 6
            values = [summary['cost_by_category'][cat]['current_week'] for cat in categories]
            
            fig.add_trace(
                go.Pie(
                    labels=[cat.title() for cat in categories],
                    values=values,
                    showlegend=False,
                    textinfo='label+percent',
                    textposition='auto'
                ),
                row=1, col=2
            )
        
        # 3. Recent anomalies count
        if 'summary' in anomaly_results:
            recent_weeks = df['week_start'].tail(4)
            anomaly_weeks = anomaly_results['summary'].get('anomaly_weeks', [])
            recent_anomalies = [w for w in anomaly_weeks if pd.to_datetime(w) in recent_weeks.values]
            
            anomaly_counts = []
            for week in recent_weeks:
                week_str = week.strftime('%Y-%m-%d')
                count = 1 if week_str in recent_anomalies else 0
                anomaly_counts.append(count)
            
            fig.add_trace(
                go.Bar(
                    x=recent_weeks,
                    y=anomaly_counts,
                    name='Anomalies',
                    marker_color=['red' if c > 0 else 'green' for c in anomaly_counts],
                    showlegend=False
                ),
                row=2, col=1
            )
        
        # 4. Top cost drivers
        if 'cost_by_category' in summary:
            top_categories = sorted(
                summary['cost_by_category'].items(),
                key=lambda x: x[1]['current_week'],
                reverse=True
            )[:5]
            
            fig.add_trace(
                go.Bar(
                    x=[cat[1]['current_week'] for cat in top_categories],
                    y=[cat[0].title() for cat in top_categories],
                    orientation='h',
                    name='Cost Drivers',
                    showlegend=False
                ),
                row=2, col=2
            )
        
        layout_config = self.default_layout.copy()
        layout_config.update({
            'title': 'Cost Analysis Dashboard'
        })
        fig.update_layout(**layout_config)
        
        return fig
    
    def _create_empty_chart(self, message: str) -> go.Figure:
        """Create an empty chart with a message"""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16)
        )
        fig.update_layout(**self.default_layout)
        return fig
    
    def _get_week_severity(self, week_str: str, anomaly_results: Dict[str, Any]) -> str:
        """Get severity level for a specific week"""
        if 'week_details' in anomaly_results and week_str in anomaly_results['week_details']:
            severity_score = anomaly_results['week_details'][week_str]['overall_severity']
            if severity_score >= 5:
                return 'high'
            elif severity_score >= 3:
                return 'medium'
            else:
                return 'low'
        return 'low'
    
    def _get_severity_color(self, severity: str) -> str:
        """Get color for severity level"""
        colors = {
            'high': '#ff4444',
            'medium': '#ffaa00',
            'low': '#ffdd00'
        }
        return colors.get(severity, '#ffdd00')
    
    def export_charts_to_html(self, charts: Dict[str, go.Figure], output_path: str) -> None:
        """
        Export multiple charts to a single HTML file
        
        Args:
            charts: Dictionary of chart names and figure objects
            output_path: Path to save the HTML file
        """
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Datadog Cost Analysis Report</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .chart-container { margin-bottom: 40px; }
                h1 { color: #333; text-align: center; }
                h2 { color: #666; border-bottom: 2px solid #ddd; padding-bottom: 10px; }
            </style>
        </head>
        <body>
            <h1>Datadog Cost Analysis Report</h1>
            <p>Generated on: {}</p>
        """.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        for chart_name, fig in charts.items():
            html_content += f"""
            <div class="chart-container">
                <h2>{chart_name}</h2>
                <div id="{chart_name.lower().replace(' ', '_')}">{fig.to_html(include_plotlyjs=False, div_id=chart_name.lower().replace(' ', '_'))}</div>
            </div>
            """
        
        html_content += """
        </body>
        </html>
        """
        
        with open(output_path, 'w') as f:
            f.write(html_content)
        
        logger.info(f"Charts exported to {output_path}")