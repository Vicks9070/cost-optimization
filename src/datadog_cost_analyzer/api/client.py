"""
Datadog API client for fetching cost and usage data
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
from datadog_api_client import ApiClient, Configuration
from datadog_api_client.v2.api.usage_metering_api import UsageMeteringApi
from datadog_api_client.v1.api.usage_metering_api import UsageMeteringApi as UsageMeteringApiV1
from datadog_api_client.exceptions import ApiException

logger = logging.getLogger(__name__)


class DatadogCostClient:
    """Client for fetching cost and usage data from Datadog API"""
    
    def __init__(self, api_key: Optional[str] = None, app_key: Optional[str] = None, 
                 site: str = "datadoghq.com"):
        """
        Initialize Datadog API client
        
        Args:
            api_key: Datadog API key (defaults to DD_API_KEY env var)
            app_key: Datadog Application key (defaults to DD_APP_KEY env var)
            site: Datadog site (defaults to datadoghq.com)
        """
        self.api_key = api_key or os.getenv("DD_API_KEY")
        self.app_key = app_key or os.getenv("DD_APP_KEY")
        self.site = site or os.getenv("DD_SITE", "datadoghq.com")
        
        if not self.api_key or not self.app_key:
            raise ValueError("API key and App key are required. Set DD_API_KEY and DD_APP_KEY environment variables.")
        
        # Configure API client
        configuration = Configuration()
        configuration.api_key["apiKeyAuth"] = self.api_key
        configuration.api_key["appKeyAuth"] = self.app_key
        configuration.server_variables["site"] = self.site
        
        self.api_client = ApiClient(configuration)
        self.usage_api_v2 = UsageMeteringApi(self.api_client)
        self.usage_api_v1 = UsageMeteringApiV1(self.api_client)
        
        logger.info(f"Initialized Datadog client for site: {self.site}")
    
    def get_usage_summary(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Get usage summary for a date range
        
        Args:
            start_date: Start date for usage data
            end_date: End date for usage data
            
        Returns:
            Dictionary containing usage summary data
        """
        try:
            response = self.usage_api_v1.get_usage_summary(
                start_month=start_date,
                end_month=end_date,
                include_org_details=True
            )
            return response.to_dict()
        except ApiException as e:
            logger.error(f"Error fetching usage summary: {e}")
            raise
    
    def get_hourly_usage(self, start_date: datetime, end_date: datetime, 
                        product_families: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get hourly usage data for specified product families
        
        Args:
            start_date: Start date for usage data
            end_date: End date for usage data
            product_families: List of product families to include
            
        Returns:
            Dictionary containing hourly usage data
        """
        if product_families is None:
            product_families = [
                "infra_hosts", "logs", "metrics", "apm_hosts", 
                "synthetics", "rum", "security", "network"
            ]
        
        try:
            response = self.usage_api_v2.get_hourly_usage(
                filter_timestamp_start=start_date,
                filter_timestamp_end=end_date,
                filter_product_families=",".join(product_families),
                page_size=5000
            )
            return response.to_dict()
        except ApiException as e:
            logger.error(f"Error fetching hourly usage: {e}")
            raise
    
    def get_estimated_cost(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Get estimated cost data for a date range
        
        Args:
            start_date: Start date for cost data
            end_date: End date for cost data
            
        Returns:
            Dictionary containing estimated cost data
        """
        try:
            response = self.usage_api_v2.get_estimated_cost_by_org(
                start_month=start_date,
                end_month=end_date
            )
            return response.to_dict()
        except ApiException as e:
            logger.error(f"Error fetching estimated cost: {e}")
            raise
    
    def get_cost_by_tag(self, start_date: datetime, end_date: datetime, 
                       tag_keys: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get cost breakdown by tags
        
        Args:
            start_date: Start date for cost data
            end_date: End date for cost data
            tag_keys: List of tag keys to group by
            
        Returns:
            Dictionary containing cost data grouped by tags
        """
        if tag_keys is None:
            tag_keys = ["env", "service", "team"]
        
        try:
            response = self.usage_api_v2.get_cost_by_org(
                start_month=start_date,
                end_month=end_date,
                tag_breakdown_keys=",".join(tag_keys)
            )
            return response.to_dict()
        except ApiException as e:
            logger.error(f"Error fetching cost by tag: {e}")
            raise
    
    def get_weekly_cost_data(self, weeks_back: int = 12) -> pd.DataFrame:
        """
        Get weekly cost data for analysis
        
        Args:
            weeks_back: Number of weeks to look back
            
        Returns:
            DataFrame with weekly cost data
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(weeks=weeks_back)
        
        logger.info(f"Fetching cost data from {start_date.date()} to {end_date.date()}")
        
        # Get usage summary data
        usage_data = self.get_usage_summary(start_date, end_date)
        
        # Get estimated cost data
        try:
            cost_data = self.get_estimated_cost(start_date, end_date)
        except ApiException:
            logger.warning("Estimated cost API not available, using usage data only")
            cost_data = None
        
        # Process data into weekly format
        weekly_data = self._process_weekly_data(usage_data, cost_data, start_date, end_date)
        
        return pd.DataFrame(weekly_data)
    
    def _process_weekly_data(self, usage_data: Dict[str, Any], cost_data: Optional[Dict[str, Any]], 
                           start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        Process raw API data into weekly format
        
        Args:
            usage_data: Raw usage data from API
            cost_data: Raw cost data from API (optional)
            start_date: Start date for processing
            end_date: End date for processing
            
        Returns:
            List of dictionaries containing weekly data
        """
        weekly_data = []
        
        # Generate weekly periods
        current_date = start_date
        while current_date < end_date:
            week_end = min(current_date + timedelta(days=7), end_date)
            
            week_data = {
                'week_start': current_date.date(),
                'week_end': week_end.date(),
                'infrastructure_cost': 0.0,
                'logs_cost': 0.0,
                'metrics_cost': 0.0,
                'traces_cost': 0.0,
                'synthetics_cost': 0.0,
                'rum_cost': 0.0,
                'security_cost': 0.0,
                'network_cost': 0.0,
                'total_cost': 0.0,
                'infrastructure_usage': 0.0,
                'logs_usage': 0.0,
                'metrics_usage': 0.0,
                'traces_usage': 0.0
            }
            
            # Extract usage data for this week
            if 'usage' in usage_data:
                for day_usage in usage_data['usage']:
                    usage_date = datetime.strptime(day_usage.get('date', ''), '%Y-%m-%d').date()
                    if current_date.date() <= usage_date < week_end.date():
                        # Map usage data to cost categories
                        week_data['infrastructure_usage'] += day_usage.get('infra_host_hours', 0)
                        week_data['logs_usage'] += day_usage.get('logs_indexed_events_count', 0)
                        week_data['metrics_usage'] += day_usage.get('custom_metrics_count', 0)
                        week_data['traces_usage'] += day_usage.get('apm_host_hours', 0)
            
            # Extract cost data if available
            if cost_data and 'estimated_cost' in cost_data:
                for cost_item in cost_data['estimated_cost']:
                    cost_date = datetime.strptime(cost_item.get('date', ''), '%Y-%m-%d').date()
                    if current_date.date() <= cost_date < week_end.date():
                        # Map cost data by product
                        product = cost_item.get('product_name', '').lower()
                        cost_value = cost_item.get('cost_usd', 0.0)
                        
                        if 'infrastructure' in product or 'host' in product:
                            week_data['infrastructure_cost'] += cost_value
                        elif 'log' in product:
                            week_data['logs_cost'] += cost_value
                        elif 'metric' in product:
                            week_data['metrics_cost'] += cost_value
                        elif 'trace' in product or 'apm' in product:
                            week_data['traces_cost'] += cost_value
                        elif 'synthetic' in product:
                            week_data['synthetics_cost'] += cost_value
                        elif 'rum' in product:
                            week_data['rum_cost'] += cost_value
                        elif 'security' in product:
                            week_data['security_cost'] += cost_value
                        elif 'network' in product:
                            week_data['network_cost'] += cost_value
            
            # Calculate total cost
            week_data['total_cost'] = sum([
                week_data['infrastructure_cost'],
                week_data['logs_cost'],
                week_data['metrics_cost'],
                week_data['traces_cost'],
                week_data['synthetics_cost'],
                week_data['rum_cost'],
                week_data['security_cost'],
                week_data['network_cost']
            ])
            
            weekly_data.append(week_data)
            current_date = week_end
        
        return weekly_data
    
    def test_connection(self) -> bool:
        """
        Test the connection to Datadog API
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Try to fetch a small amount of data to test connection
            end_date = datetime.now()
            start_date = end_date - timedelta(days=1)
            self.get_usage_summary(start_date, end_date)
            logger.info("Successfully connected to Datadog API")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Datadog API: {e}")
            return False