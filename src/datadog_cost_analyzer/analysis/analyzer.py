"""
Cost data analyzer for processing and aggregating Datadog cost data
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

logger = logging.getLogger(__name__)


class CostAnalyzer:
    """Analyzer for processing and analyzing Datadog cost data"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the cost analyzer
        
        Args:
            config: Configuration dictionary with analysis parameters
        """
        self.config = config or {}
        self.lookback_weeks = self.config.get('lookback_weeks', 12)
        self.cost_categories = self.config.get('cost_categories', [
            'infrastructure', 'logs', 'metrics', 'traces', 
            'synthetics', 'rum', 'security', 'network'
        ])
        
        logger.info(f"Initialized CostAnalyzer with {self.lookback_weeks} weeks lookback")
    
    def process_weekly_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process and enrich weekly cost data
        
        Args:
            df: Raw weekly cost data DataFrame
            
        Returns:
            Processed DataFrame with additional metrics
        """
        if df.empty:
            logger.warning("Empty DataFrame provided for processing")
            return df
        
        # Ensure date columns are datetime
        df['week_start'] = pd.to_datetime(df['week_start'])
        df['week_end'] = pd.to_datetime(df['week_end'])
        
        # Sort by week start date
        df = df.sort_values('week_start').reset_index(drop=True)
        
        # Calculate week-over-week changes
        df = self._calculate_week_over_week_changes(df)
        
        # Calculate rolling averages
        df = self._calculate_rolling_averages(df)
        
        # Calculate cost efficiency metrics
        df = self._calculate_efficiency_metrics(df)
        
        # Add trend indicators
        df = self._add_trend_indicators(df)
        
        logger.info(f"Processed {len(df)} weeks of cost data")
        return df
    
    def _calculate_week_over_week_changes(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate week-over-week percentage changes for all cost categories"""
        
        for category in self.cost_categories:
            cost_col = f'{category}_cost'
            change_col = f'{category}_wow_change'
            
            if cost_col in df.columns:
                df[change_col] = df[cost_col].pct_change() * 100
        
        # Calculate total cost change
        df['total_wow_change'] = df['total_cost'].pct_change() * 100
        
        return df
    
    def _calculate_rolling_averages(self, df: pd.DataFrame, windows: List[int] = [4, 8]) -> pd.DataFrame:
        """Calculate rolling averages for cost categories"""
        
        for window in windows:
            for category in self.cost_categories:
                cost_col = f'{category}_cost'
                avg_col = f'{category}_avg_{window}w'
                
                if cost_col in df.columns:
                    df[avg_col] = df[cost_col].rolling(window=window, min_periods=1).mean()
            
            # Total cost rolling average
            df[f'total_avg_{window}w'] = df['total_cost'].rolling(window=window, min_periods=1).mean()
        
        return df
    
    def _calculate_efficiency_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate cost efficiency metrics"""
        
        # Cost per unit metrics (where usage data is available)
        usage_cost_pairs = [
            ('infrastructure_usage', 'infrastructure_cost', 'cost_per_host_hour'),
            ('logs_usage', 'logs_cost', 'cost_per_log_event'),
            ('metrics_usage', 'metrics_cost', 'cost_per_metric'),
            ('traces_usage', 'traces_cost', 'cost_per_trace_hour')
        ]
        
        for usage_col, cost_col, efficiency_col in usage_cost_pairs:
            if usage_col in df.columns and cost_col in df.columns:
                df[efficiency_col] = np.where(
                    df[usage_col] > 0,
                    df[cost_col] / df[usage_col],
                    0
                )
        
        # Cost distribution percentages
        total_cost = df['total_cost']
        for category in self.cost_categories:
            cost_col = f'{category}_cost'
            pct_col = f'{category}_pct'
            
            if cost_col in df.columns:
                df[pct_col] = np.where(
                    total_cost > 0,
                    (df[cost_col] / total_cost) * 100,
                    0
                )
        
        return df
    
    def _add_trend_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add trend indicators for cost categories"""
        
        for category in self.cost_categories + ['total']:
            cost_col = f'{category}_cost'
            trend_col = f'{category}_trend'
            
            if cost_col in df.columns:
                # Calculate trend using linear regression slope
                df[trend_col] = df[cost_col].rolling(window=4, min_periods=2).apply(
                    lambda x: self._calculate_trend_slope(x), raw=False
                )
        
        return df
    
    def _calculate_trend_slope(self, series: pd.Series) -> float:
        """Calculate trend slope using linear regression"""
        if len(series) < 2:
            return 0.0
        
        x = np.arange(len(series))
        y = series.values
        
        # Remove NaN values
        mask = ~np.isnan(y)
        if mask.sum() < 2:
            return 0.0
        
        x_clean = x[mask]
        y_clean = y[mask]
        
        try:
            slope, _, _, _, _ = stats.linregress(x_clean, y_clean)
            return slope
        except:
            return 0.0
    
    def get_cost_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate cost summary statistics
        
        Args:
            df: Processed cost data DataFrame
            
        Returns:
            Dictionary containing summary statistics
        """
        if df.empty:
            return {}
        
        summary = {
            'period': {
                'start_date': df['week_start'].min().strftime('%Y-%m-%d'),
                'end_date': df['week_end'].max().strftime('%Y-%m-%d'),
                'total_weeks': len(df)
            },
            'total_cost': {
                'current_week': float(df['total_cost'].iloc[-1]) if len(df) > 0 else 0.0,
                'previous_week': float(df['total_cost'].iloc[-2]) if len(df) > 1 else 0.0,
                'average_weekly': float(df['total_cost'].mean()),
                'total_period': float(df['total_cost'].sum()),
                'min_weekly': float(df['total_cost'].min()),
                'max_weekly': float(df['total_cost'].max()),
                'std_dev': float(df['total_cost'].std())
            },
            'cost_by_category': {},
            'trends': {},
            'efficiency_metrics': {}
        }
        
        # Cost by category
        for category in self.cost_categories:
            cost_col = f'{category}_cost'
            pct_col = f'{category}_pct'
            
            if cost_col in df.columns:
                summary['cost_by_category'][category] = {
                    'current_week': float(df[cost_col].iloc[-1]) if len(df) > 0 else 0.0,
                    'average_weekly': float(df[cost_col].mean()),
                    'total_period': float(df[cost_col].sum()),
                    'percentage_of_total': float(df[pct_col].iloc[-1]) if pct_col in df.columns and len(df) > 0 else 0.0
                }
        
        # Trend analysis
        for category in self.cost_categories + ['total']:
            trend_col = f'{category}_trend'
            if trend_col in df.columns:
                latest_trend = df[trend_col].iloc[-1] if len(df) > 0 else 0.0
                summary['trends'][category] = {
                    'slope': float(latest_trend),
                    'direction': 'increasing' if latest_trend > 0 else 'decreasing' if latest_trend < 0 else 'stable'
                }
        
        # Efficiency metrics
        efficiency_cols = [col for col in df.columns if col.startswith('cost_per_')]
        for col in efficiency_cols:
            metric_name = col.replace('cost_per_', '')
            if len(df) > 0:
                summary['efficiency_metrics'][metric_name] = {
                    'current': float(df[col].iloc[-1]),
                    'average': float(df[col].mean()),
                    'trend': 'improving' if df[col].iloc[-1] < df[col].mean() else 'degrading'
                }
        
        return summary
    
    def identify_cost_drivers(self, df: pd.DataFrame, top_n: int = 5) -> List[Dict[str, Any]]:
        """
        Identify top cost drivers and their impact
        
        Args:
            df: Processed cost data DataFrame
            top_n: Number of top drivers to return
            
        Returns:
            List of cost drivers with impact analysis
        """
        if df.empty or len(df) < 2:
            return []
        
        drivers = []
        
        # Analyze each cost category
        for category in self.cost_categories:
            cost_col = f'{category}_cost'
            change_col = f'{category}_wow_change'
            
            if cost_col in df.columns and change_col in df.columns:
                current_cost = df[cost_col].iloc[-1]
                avg_cost = df[cost_col].mean()
                recent_change = df[change_col].iloc[-1] if not pd.isna(df[change_col].iloc[-1]) else 0.0
                
                # Calculate impact score (combination of absolute cost and recent change)
                impact_score = (current_cost / df['total_cost'].iloc[-1]) * 100 + abs(recent_change) * 0.1
                
                drivers.append({
                    'category': category,
                    'current_cost': current_cost,
                    'average_cost': avg_cost,
                    'recent_change_pct': recent_change,
                    'cost_percentage': (current_cost / df['total_cost'].iloc[-1]) * 100,
                    'impact_score': impact_score,
                    'status': 'increasing' if recent_change > 5 else 'decreasing' if recent_change < -5 else 'stable'
                })
        
        # Sort by impact score and return top N
        drivers.sort(key=lambda x: x['impact_score'], reverse=True)
        return drivers[:top_n]
    
    def calculate_forecast(self, df: pd.DataFrame, weeks_ahead: int = 4) -> Dict[str, Any]:
        """
        Calculate cost forecast using trend analysis
        
        Args:
            df: Processed cost data DataFrame
            weeks_ahead: Number of weeks to forecast
            
        Returns:
            Dictionary containing forecast data
        """
        if df.empty or len(df) < 4:
            return {}
        
        forecast = {
            'forecast_weeks': weeks_ahead,
            'method': 'linear_trend',
            'categories': {},
            'total': {}
        }
        
        # Forecast for each category
        for category in self.cost_categories + ['total']:
            cost_col = f'{category}_cost'
            
            if cost_col in df.columns:
                # Use last 8 weeks for trend calculation
                recent_data = df[cost_col].tail(8)
                
                if len(recent_data) >= 2:
                    # Calculate trend
                    x = np.arange(len(recent_data))
                    y = recent_data.values
                    
                    try:
                        slope, intercept, r_value, _, _ = stats.linregress(x, y)
                        
                        # Generate forecast
                        future_x = np.arange(len(recent_data), len(recent_data) + weeks_ahead)
                        forecast_values = slope * future_x + intercept
                        
                        # Ensure non-negative values
                        forecast_values = np.maximum(forecast_values, 0)
                        
                        forecast['categories'][category] = {
                            'current_value': float(recent_data.iloc[-1]),
                            'forecasted_values': forecast_values.tolist(),
                            'trend_slope': float(slope),
                            'confidence': float(r_value ** 2),  # R-squared as confidence measure
                            'total_forecasted': float(forecast_values.sum())
                        }
                    except:
                        # Fallback to simple average if regression fails
                        avg_value = recent_data.mean()
                        forecast_values = [avg_value] * weeks_ahead
                        
                        forecast['categories'][category] = {
                            'current_value': float(recent_data.iloc[-1]),
                            'forecasted_values': forecast_values,
                            'trend_slope': 0.0,
                            'confidence': 0.5,
                            'total_forecasted': float(avg_value * weeks_ahead)
                        }
        
        return forecast