"""
Anomaly detection algorithms for identifying unusual cost patterns
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np
from scipy import stats
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import adfuller

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """Advanced anomaly detection for cost data analysis"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the anomaly detector
        
        Args:
            config: Configuration dictionary with detection parameters
        """
        self.config = config or {}
        self.z_score_threshold = self.config.get('z_score_threshold', 2.5)
        self.iqr_multiplier = self.config.get('iqr_multiplier', 1.5)
        self.min_change_percent = self.config.get('min_change_percent', 10.0)
        self.seasonal_periods = self.config.get('seasonal_periods', 4)
        
        logger.info(f"Initialized AnomalyDetector with z-score threshold: {self.z_score_threshold}")
    
    def detect_anomalies(self, df: pd.DataFrame, categories: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Detect anomalies using multiple methods
        
        Args:
            df: Cost data DataFrame
            categories: List of cost categories to analyze
            
        Returns:
            Dictionary containing anomaly detection results
        """
        if df.empty:
            logger.warning("Empty DataFrame provided for anomaly detection")
            return {}
        
        if categories is None:
            categories = [col.replace('_cost', '') for col in df.columns if col.endswith('_cost')]
        
        results = {
            'summary': {
                'total_anomalies': 0,
                'anomaly_weeks': [],
                'severity_distribution': {'low': 0, 'medium': 0, 'high': 0}
            },
            'methods': {
                'z_score': {},
                'iqr': {},
                'isolation_forest': {},
                'seasonal_decomposition': {},
                'week_over_week': {}
            },
            'category_analysis': {},
            'recommendations': []
        }
        
        # Apply different anomaly detection methods
        z_score_anomalies = self._detect_z_score_anomalies(df, categories)
        iqr_anomalies = self._detect_iqr_anomalies(df, categories)
        isolation_anomalies = self._detect_isolation_forest_anomalies(df, categories)
        seasonal_anomalies = self._detect_seasonal_anomalies(df, categories)
        wow_anomalies = self._detect_week_over_week_anomalies(df, categories)
        
        # Store method results
        results['methods']['z_score'] = z_score_anomalies
        results['methods']['iqr'] = iqr_anomalies
        results['methods']['isolation_forest'] = isolation_anomalies
        results['methods']['seasonal_decomposition'] = seasonal_anomalies
        results['methods']['week_over_week'] = wow_anomalies
        
        # Combine and analyze results
        combined_anomalies = self._combine_anomaly_results(
            df, [z_score_anomalies, iqr_anomalies, isolation_anomalies, seasonal_anomalies, wow_anomalies]
        )
        
        # Update summary
        results['summary'] = self._generate_anomaly_summary(combined_anomalies)
        results['category_analysis'] = self._analyze_category_anomalies(combined_anomalies, categories)
        results['recommendations'] = self._generate_recommendations(combined_anomalies, df)
        
        logger.info(f"Detected {results['summary']['total_anomalies']} anomalies across {len(categories)} categories")
        return results
    
    def _detect_z_score_anomalies(self, df: pd.DataFrame, categories: List[str]) -> Dict[str, Any]:
        """Detect anomalies using Z-score method"""
        anomalies = {'method': 'z_score', 'threshold': self.z_score_threshold, 'results': {}}
        
        for category in categories:
            cost_col = f'{category}_cost'
            if cost_col not in df.columns:
                continue
            
            values = df[cost_col].values
            if len(values) < 3:
                continue
            
            # Calculate Z-scores
            z_scores = np.abs(stats.zscore(values, nan_policy='omit'))
            anomaly_mask = z_scores > self.z_score_threshold
            
            anomaly_indices = np.where(anomaly_mask)[0]
            anomaly_weeks = df.iloc[anomaly_indices]['week_start'].dt.strftime('%Y-%m-%d').tolist()
            anomaly_values = values[anomaly_indices].tolist()
            anomaly_z_scores = z_scores[anomaly_indices].tolist()
            
            anomalies['results'][category] = {
                'anomaly_count': len(anomaly_indices),
                'anomaly_weeks': anomaly_weeks,
                'anomaly_values': anomaly_values,
                'z_scores': anomaly_z_scores,
                'severity': self._calculate_severity(anomaly_z_scores, 'z_score')
            }
        
        return anomalies
    
    def _detect_iqr_anomalies(self, df: pd.DataFrame, categories: List[str]) -> Dict[str, Any]:
        """Detect anomalies using Interquartile Range (IQR) method"""
        anomalies = {'method': 'iqr', 'multiplier': self.iqr_multiplier, 'results': {}}
        
        for category in categories:
            cost_col = f'{category}_cost'
            if cost_col not in df.columns:
                continue
            
            values = df[cost_col].dropna().values
            if len(values) < 4:
                continue
            
            # Calculate IQR
            q1 = np.percentile(values, 25)
            q3 = np.percentile(values, 75)
            iqr = q3 - q1
            
            lower_bound = q1 - self.iqr_multiplier * iqr
            upper_bound = q3 + self.iqr_multiplier * iqr
            
            # Find anomalies
            anomaly_mask = (df[cost_col] < lower_bound) | (df[cost_col] > upper_bound)
            anomaly_indices = df[anomaly_mask].index.tolist()
            
            anomaly_weeks = df.loc[anomaly_indices, 'week_start'].dt.strftime('%Y-%m-%d').tolist()
            anomaly_values = df.loc[anomaly_indices, cost_col].tolist()
            
            # Calculate severity based on distance from bounds
            severity_scores = []
            for val in anomaly_values:
                if val < lower_bound:
                    severity_scores.append(abs(val - lower_bound) / iqr)
                else:
                    severity_scores.append(abs(val - upper_bound) / iqr)
            
            anomalies['results'][category] = {
                'anomaly_count': len(anomaly_indices),
                'anomaly_weeks': anomaly_weeks,
                'anomaly_values': anomaly_values,
                'bounds': {'lower': lower_bound, 'upper': upper_bound},
                'severity': self._calculate_severity(severity_scores, 'iqr')
            }
        
        return anomalies
    
    def _detect_isolation_forest_anomalies(self, df: pd.DataFrame, categories: List[str]) -> Dict[str, Any]:
        """Detect anomalies using Isolation Forest algorithm"""
        anomalies = {'method': 'isolation_forest', 'contamination': 0.1, 'results': {}}
        
        # Prepare feature matrix
        feature_cols = [f'{cat}_cost' for cat in categories if f'{cat}_cost' in df.columns]
        if len(feature_cols) < 2 or len(df) < 10:
            return anomalies
        
        feature_matrix = df[feature_cols].fillna(0).values
        
        # Standardize features
        scaler = StandardScaler()
        feature_matrix_scaled = scaler.fit_transform(feature_matrix)
        
        # Apply Isolation Forest
        iso_forest = IsolationForest(contamination=0.1, random_state=42)
        anomaly_labels = iso_forest.fit_predict(feature_matrix_scaled)
        anomaly_scores = iso_forest.score_samples(feature_matrix_scaled)
        
        # Find anomalies (labeled as -1)
        anomaly_mask = anomaly_labels == -1
        anomaly_indices = np.where(anomaly_mask)[0]
        
        anomaly_weeks = df.iloc[anomaly_indices]['week_start'].dt.strftime('%Y-%m-%d').tolist()
        anomaly_score_values = anomaly_scores[anomaly_indices].tolist()
        
        # Analyze which categories contributed to anomalies
        category_contributions = {}
        for i, category in enumerate(categories):
            if f'{category}_cost' in feature_cols:
                col_idx = feature_cols.index(f'{category}_cost')
                category_values = feature_matrix_scaled[anomaly_mask, col_idx]
                category_contributions[category] = {
                    'mean_anomaly_value': float(np.mean(category_values)),
                    'contribution_score': float(np.mean(np.abs(category_values)))
                }
        
        anomalies['results']['global'] = {
            'anomaly_count': len(anomaly_indices),
            'anomaly_weeks': anomaly_weeks,
            'anomaly_scores': anomaly_score_values,
            'category_contributions': category_contributions,
            'severity': self._calculate_severity([-score for score in anomaly_score_values], 'isolation_forest')
        }
        
        return anomalies
    
    def _detect_seasonal_anomalies(self, df: pd.DataFrame, categories: List[str]) -> Dict[str, Any]:
        """Detect anomalies using seasonal decomposition"""
        anomalies = {'method': 'seasonal_decomposition', 'period': self.seasonal_periods, 'results': {}}
        
        if len(df) < self.seasonal_periods * 2:
            logger.warning("Insufficient data for seasonal decomposition")
            return anomalies
        
        for category in categories:
            cost_col = f'{category}_cost'
            if cost_col not in df.columns:
                continue
            
            try:
                # Perform seasonal decomposition
                series = df[cost_col].ffill().bfill()
                if series.std() == 0:  # Skip if no variation
                    continue
                
                decomposition = seasonal_decompose(
                    series, 
                    model='additive', 
                    period=self.seasonal_periods,
                    extrapolate_trend='freq'
                )
                
                # Calculate residuals and detect anomalies
                residuals = decomposition.resid.dropna()
                residual_std = residuals.std()
                residual_mean = residuals.mean()
                
                # Anomalies are residuals beyond 2 standard deviations
                threshold = 2 * residual_std
                anomaly_mask = np.abs(residuals - residual_mean) > threshold
                
                anomaly_indices = residuals[anomaly_mask].index.tolist()
                anomaly_weeks = df.loc[anomaly_indices, 'week_start'].dt.strftime('%Y-%m-%d').tolist()
                anomaly_residuals = residuals[anomaly_mask].tolist()
                
                anomalies['results'][category] = {
                    'anomaly_count': len(anomaly_indices),
                    'anomaly_weeks': anomaly_weeks,
                    'residual_values': anomaly_residuals,
                    'residual_threshold': threshold,
                    'trend_direction': 'increasing' if decomposition.trend.iloc[-1] > decomposition.trend.iloc[0] else 'decreasing',
                    'severity': self._calculate_severity([abs(r) / residual_std for r in anomaly_residuals], 'seasonal')
                }
                
            except Exception as e:
                logger.warning(f"Seasonal decomposition failed for {category}: {e}")
                continue
        
        return anomalies
    
    def _detect_week_over_week_anomalies(self, df: pd.DataFrame, categories: List[str]) -> Dict[str, Any]:
        """Detect anomalies based on week-over-week changes"""
        anomalies = {'method': 'week_over_week', 'threshold_pct': self.min_change_percent, 'results': {}}
        
        for category in categories:
            change_col = f'{category}_wow_change'
            cost_col = f'{category}_cost'
            
            if change_col not in df.columns or cost_col not in df.columns:
                continue
            
            # Find significant week-over-week changes
            significant_changes = df[np.abs(df[change_col]) > self.min_change_percent]
            
            if len(significant_changes) == 0:
                continue
            
            anomaly_weeks = significant_changes['week_start'].dt.strftime('%Y-%m-%d').tolist()
            change_values = significant_changes[change_col].tolist()
            cost_values = significant_changes[cost_col].tolist()
            
            # Categorize changes
            increases = [c for c in change_values if c > 0]
            decreases = [c for c in change_values if c < 0]
            
            anomalies['results'][category] = {
                'anomaly_count': len(significant_changes),
                'anomaly_weeks': anomaly_weeks,
                'change_values': change_values,
                'cost_values': cost_values,
                'increases': len(increases),
                'decreases': len(decreases),
                'max_increase': max(increases) if increases else 0,
                'max_decrease': min(decreases) if decreases else 0,
                'severity': self._calculate_severity([abs(c) / self.min_change_percent for c in change_values], 'wow')
            }
        
        return anomalies
    
    def _combine_anomaly_results(self, df: pd.DataFrame, method_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Combine results from multiple anomaly detection methods"""
        combined = {
            'anomaly_weeks': set(),
            'category_scores': {},
            'week_details': {}
        }
        
        # Collect all anomaly weeks
        for method_result in method_results:
            if 'results' in method_result:
                for category, results in method_result['results'].items():
                    if 'anomaly_weeks' in results:
                        combined['anomaly_weeks'].update(results['anomaly_weeks'])
        
        # Analyze each anomaly week
        for week_str in combined['anomaly_weeks']:
            week_date = pd.to_datetime(week_str)
            week_row = df[df['week_start'] == week_date]
            
            if len(week_row) == 0:
                continue
            
            week_idx = week_row.index[0]
            week_details = {
                'week_start': week_str,
                'total_cost': float(week_row['total_cost'].iloc[0]),
                'methods_detected': [],
                'category_impacts': {},
                'overall_severity': 0
            }
            
            # Check which methods detected this week
            method_names = ['z_score', 'iqr', 'isolation_forest', 'seasonal_decomposition', 'week_over_week']
            for i, method_result in enumerate(method_results):
                method_name = method_names[i]
                if 'results' in method_result:
                    for category, results in method_result['results'].items():
                        if 'anomaly_weeks' in results and week_str in results['anomaly_weeks']:
                            week_details['methods_detected'].append(f"{method_name}_{category}")
            
            # Calculate overall severity
            week_details['overall_severity'] = len(week_details['methods_detected'])
            combined['week_details'][week_str] = week_details
        
        return combined
    
    def _calculate_severity(self, scores: List[float], method: str) -> Dict[str, Any]:
        """Calculate severity distribution for anomaly scores"""
        if not scores:
            return {'low': 0, 'medium': 0, 'high': 0, 'max_score': 0}
        
        # Define thresholds based on method
        thresholds = {
            'z_score': {'medium': 2.5, 'high': 3.5},
            'iqr': {'medium': 1.5, 'high': 2.5},
            'isolation_forest': {'medium': 0.3, 'high': 0.5},
            'seasonal': {'medium': 2.0, 'high': 3.0},
            'wow': {'medium': 1.5, 'high': 2.5}
        }
        
        thresh = thresholds.get(method, {'medium': 1.5, 'high': 2.5})
        
        severity = {'low': 0, 'medium': 0, 'high': 0, 'max_score': max(scores)}
        
        for score in scores:
            if score >= thresh['high']:
                severity['high'] += 1
            elif score >= thresh['medium']:
                severity['medium'] += 1
            else:
                severity['low'] += 1
        
        return severity
    
    def _generate_anomaly_summary(self, combined_anomalies: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of anomaly detection results"""
        summary = {
            'total_anomalies': len(combined_anomalies['anomaly_weeks']),
            'anomaly_weeks': sorted(list(combined_anomalies['anomaly_weeks'])),
            'severity_distribution': {'low': 0, 'medium': 0, 'high': 0}
        }
        
        # Calculate severity distribution
        for week_details in combined_anomalies['week_details'].values():
            severity_score = week_details['overall_severity']
            if severity_score >= 5:
                summary['severity_distribution']['high'] += 1
            elif severity_score >= 3:
                summary['severity_distribution']['medium'] += 1
            else:
                summary['severity_distribution']['low'] += 1
        
        return summary
    
    def _analyze_category_anomalies(self, combined_anomalies: Dict[str, Any], categories: List[str]) -> Dict[str, Any]:
        """Analyze anomalies by category"""
        category_analysis = {}
        
        for category in categories:
            category_analysis[category] = {
                'anomaly_frequency': 0,
                'avg_severity': 0,
                'most_common_methods': []
            }
        
        # Count anomalies by category
        method_counts = {}
        for week_details in combined_anomalies['week_details'].values():
            for method_category in week_details['methods_detected']:
                if '_' in method_category:
                    method, cat = method_category.split('_', 1)
                    if cat in categories:
                        category_analysis[cat]['anomaly_frequency'] += 1
                        if method not in method_counts:
                            method_counts[method] = 0
                        method_counts[method] += 1
        
        # Find most common detection methods
        sorted_methods = sorted(method_counts.items(), key=lambda x: x[1], reverse=True)
        for category in categories:
            category_analysis[category]['most_common_methods'] = [method for method, _ in sorted_methods[:3]]
        
        return category_analysis
    
    def _generate_recommendations(self, combined_anomalies: Dict[str, Any], df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Generate recommendations based on anomaly analysis"""
        recommendations = []
        
        if len(combined_anomalies['anomaly_weeks']) == 0:
            recommendations.append({
                'type': 'info',
                'priority': 'low',
                'title': 'No Significant Anomalies Detected',
                'description': 'Cost patterns appear normal within expected ranges.',
                'action': 'Continue monitoring for future anomalies.'
            })
            return recommendations
        
        # High frequency anomalies
        if len(combined_anomalies['anomaly_weeks']) > len(df) * 0.3:
            recommendations.append({
                'type': 'warning',
                'priority': 'high',
                'title': 'High Anomaly Frequency',
                'description': f'Detected anomalies in {len(combined_anomalies["anomaly_weeks"])} out of {len(df)} weeks.',
                'action': 'Review cost management processes and consider adjusting baseline expectations.'
            })
        
        # Recent anomalies
        recent_anomalies = [w for w in combined_anomalies['anomaly_weeks'] 
                          if pd.to_datetime(w) >= df['week_start'].max() - pd.Timedelta(weeks=2)]
        
        if recent_anomalies:
            recommendations.append({
                'type': 'alert',
                'priority': 'high',
                'title': 'Recent Cost Anomalies',
                'description': f'Detected {len(recent_anomalies)} anomalies in the last 2 weeks.',
                'action': 'Investigate recent changes in infrastructure or usage patterns.'
            })
        
        # Seasonal patterns
        if len(df) >= 8:  # Need enough data for seasonal analysis
            recommendations.append({
                'type': 'info',
                'priority': 'medium',
                'title': 'Seasonal Analysis Available',
                'description': 'Consider seasonal patterns when evaluating cost anomalies.',
                'action': 'Review seasonal decomposition results for trend insights.'
            })
        
        return recommendations