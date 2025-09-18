"""
Datadog Notebook Creator for Cost Anomaly Analysis
Creates comprehensive notebooks in Datadog with cost discrepancy analysis
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json
from datadog_api_client import ApiClient, Configuration
from datadog_api_client.v1.api.notebooks_api import NotebooksApi
from datadog_api_client.v1.model.notebook_create_request import NotebookCreateRequest
from datadog_api_client.v1.model.notebook_create_data import NotebookCreateData
from datadog_api_client.v1.model.notebook_create_data_attributes import NotebookCreateDataAttributes
from datadog_api_client.v1.model.notebook_resource_type import NotebookResourceType
from datadog_api_client.v1.model.notebook_cell_create_request import NotebookCellCreateRequest
from datadog_api_client.v1.model.notebook_markdown_cell_definition import NotebookMarkdownCellDefinition
from datadog_api_client.v1.model.notebook_markdown_cell_attributes import NotebookMarkdownCellAttributes
from datadog_api_client.v1.model.notebook_cell_resource_type import NotebookCellResourceType
from datadog_api_client.v1.model.notebook_markdown_cell_definition_type import NotebookMarkdownCellDefinitionType
from datadog_api_client.v1.model.notebook_relative_time import NotebookRelativeTime

logger = logging.getLogger(__name__)


class DatadogNotebookCreator:
    """Creates Datadog notebooks for cost anomaly analysis and reporting"""
    
    def __init__(self, api_key: str, app_key: str, site: str = "datadoghq.com"):
        """
        Initialize the Datadog Notebook Creator
        
        Args:
            api_key: Datadog API key
            app_key: Datadog Application key
            site: Datadog site (default: datadoghq.com)
        """
        self.configuration = Configuration()
        self.configuration.api_key["apiKeyAuth"] = api_key
        self.configuration.api_key["appKeyAuth"] = app_key
        self.configuration.server_variables["site"] = site
        
        self.api_client = ApiClient(self.configuration)
        # Do not hold a long-lived NotebooksApi instance so test-time method patches apply reliably
        
        logger.info(f"Initialized DatadogNotebookCreator for site: {site}")
    
    def create_cost_anomaly_notebook(
        self, 
        anomaly_results: Dict[str, Any], 
        cost_data: Dict[str, Any],
        title: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a comprehensive cost anomaly analysis notebook in Datadog
        
        Args:
            anomaly_results: Results from anomaly detection analysis
            cost_data: Cost data and trends
            title: Custom title for the notebook
            tags: Tags to apply to the notebook
            
        Returns:
            Dictionary containing notebook creation results
        """
        if not title:
            title = f"Cost Anomaly Analysis - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        if not tags:
            tags = ["cost-analysis", "anomaly-detection", "financial-monitoring"]
        
        try:
            # Create notebook cells
            cells = self._create_notebook_cells(anomaly_results, cost_data)
            
            # Create notebook request
            notebook_request = NotebookCreateRequest(
                data=NotebookCreateData(
                    type=NotebookResourceType.NOTEBOOKS,
                    attributes=NotebookCreateDataAttributes(
                        name=title,
                        cells=cells,
                        time=NotebookRelativeTime(
                            live_span="1w"  # Default to 1 week time range
                        )
                    )
                )
            )
            
            # Create the notebook
            # Instantiate API at call time so patched methods in tests are applied
            response = NotebooksApi(self.api_client).create_notebook(notebook_request)
            
            notebook_info = {
                "success": True,
                "notebook_id": response.data.id,
                "notebook_url": f"https://app.{self.configuration.server_variables['site']}/notebook/{response.data.id}",
                "title": title,
                "created_at": datetime.now().isoformat(),
                "cell_count": len(cells),
                "tags": tags
            }
            
            logger.info(f"Successfully created notebook: {notebook_info['notebook_url']}")
            return notebook_info
            
        except Exception as e:
            logger.error(f"Failed to create notebook: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "title": title
            }
    
    def _create_notebook_cells(self, anomaly_results: Dict[str, Any], cost_data: Dict[str, Any]) -> List[NotebookCellCreateRequest]:
        """Create all notebook cells for the cost anomaly analysis"""
        cells = []
        
        # 1. Executive Summary Cell
        cells.append(self._create_executive_summary_cell(anomaly_results, cost_data))
        
        # 2. Anomaly Overview Cell
        cells.append(self._create_anomaly_overview_cell(anomaly_results))
        
        # 3. Cost Trend Analysis Cell
        cells.append(self._create_cost_trend_cell(cost_data))
        
        # 4. Anomaly Detection Methods Cell
        cells.append(self._create_methods_analysis_cell(anomaly_results))
        
        # 5. Category-wise Analysis Cell
        cells.append(self._create_category_analysis_cell(anomaly_results))
        
        # 6. Time Series Visualization Cell
        cells.append(self._create_timeseries_cell(cost_data))
        
        # 7. Recommendations Cell
        cells.append(self._create_recommendations_cell(anomaly_results))
        
        # 8. Investigation Queries Cell
        cells.append(self._create_investigation_queries_cell(anomaly_results))
        
        return cells
    
    def _create_executive_summary_cell(self, anomaly_results: Dict[str, Any], cost_data: Dict[str, Any]) -> NotebookCellCreateRequest:
        """Create executive summary cell"""
        summary = anomaly_results.get('summary', {})
        total_anomalies = summary.get('total_anomalies', 0)
        severity_dist = summary.get('severity_distribution', {})
        
        # Calculate cost impact
        total_cost = cost_data.get('total_cost', 0)
        cost_trend = cost_data.get('trend', 'stable')
        
        markdown_content = f"""# 📊 Cost Anomaly Analysis - Executive Summary

## 🎯 Key Findings

**Analysis Period:** {cost_data.get('period', 'Last 12 weeks')}  
**Total Cost:** ${total_cost:,.2f}  
**Cost Trend:** {cost_trend.title()}  
**Anomalies Detected:** {total_anomalies}

## 🚨 Anomaly Severity Breakdown

- **🔴 High Severity:** {severity_dist.get('high', 0)} anomalies
- **🟡 Medium Severity:** {severity_dist.get('medium', 0)} anomalies  
- **🟢 Low Severity:** {severity_dist.get('low', 0)} anomalies

## 💡 Impact Assessment

{self._generate_impact_assessment(anomaly_results, cost_data)}

---
*Generated by Datadog Cost Analyzer on {datetime.now().strftime('%Y-%m-%d at %H:%M UTC')}*
"""
        
        return NotebookCellCreateRequest(
            attributes=NotebookMarkdownCellAttributes(
                definition=NotebookMarkdownCellDefinition(
                    type=NotebookMarkdownCellDefinitionType.MARKDOWN,
                    text=markdown_content
                )
            ),
            type=NotebookCellResourceType.NOTEBOOK_CELLS
        )
    
    def _create_anomaly_overview_cell(self, anomaly_results: Dict[str, Any]) -> NotebookCellCreateRequest:
        """Create anomaly overview cell"""
        summary = anomaly_results.get('summary', {})
        anomaly_weeks = summary.get('anomaly_weeks', [])
        
        markdown_content = f"""# 🔍 Anomaly Detection Overview

## 📅 Anomalous Weeks Identified

{self._format_anomaly_weeks(anomaly_weeks)}

## 🔬 Detection Methods Used

Our analysis employed **5 advanced anomaly detection algorithms**:

### 1. 📈 Z-Score Analysis
- **Purpose:** Identifies statistical outliers based on standard deviation
- **Threshold:** 2.5 standard deviations from mean
- **Best for:** Sudden spikes or drops in cost

### 2. 📊 IQR (Interquartile Range) Analysis  
- **Purpose:** Detects outliers beyond normal distribution ranges
- **Threshold:** 1.5 × IQR beyond Q1/Q3
- **Best for:** Consistent pattern violations

### 3. 🌲 Isolation Forest (ML-based)
- **Purpose:** Multi-dimensional anomaly detection using machine learning
- **Method:** Isolates anomalies in feature space
- **Best for:** Complex patterns across multiple cost categories

### 4. 📈 Seasonal Decomposition
- **Purpose:** Identifies deviations from seasonal patterns
- **Method:** Time series decomposition with residual analysis
- **Best for:** Unexpected costs during predictable periods

### 5. 📅 Week-over-Week Change Analysis
- **Purpose:** Detects significant period-to-period changes
- **Threshold:** >10% change from previous week
- **Best for:** Immediate cost impact detection

## 🎯 Method Performance Summary

{self._generate_method_performance_summary(anomaly_results)}
"""
        
        return NotebookCellCreateRequest(
            attributes=NotebookMarkdownCellAttributes(
                definition=NotebookMarkdownCellDefinition(
                    type=NotebookMarkdownCellDefinitionType.MARKDOWN,
                    text=markdown_content
                )
            ),
            type=NotebookCellResourceType.NOTEBOOK_CELLS
        )
    
    def _create_cost_trend_cell(self, cost_data: Dict[str, Any]) -> NotebookCellCreateRequest:
        """Create cost trend analysis cell"""
        markdown_content = f"""# 📈 Cost Trend Analysis

## 💰 Overall Cost Trends

{self._generate_cost_trend_analysis(cost_data)}

## 📊 Cost Categories Performance

{self._generate_category_performance(cost_data)}

## 🔮 Forecasting Insights

{self._generate_forecasting_insights(cost_data)}
"""
        
        return NotebookCellCreateRequest(
            attributes=NotebookMarkdownCellAttributes(
                definition=NotebookMarkdownCellDefinition(
                    type=NotebookMarkdownCellDefinitionType.MARKDOWN,
                    text=markdown_content
                )
            ),
            type=NotebookCellResourceType.NOTEBOOK_CELLS
        )
    
    def _create_methods_analysis_cell(self, anomaly_results: Dict[str, Any]) -> NotebookCellCreateRequest:
        """Create detailed methods analysis cell"""
        methods = anomaly_results.get('methods', {})
        
        markdown_content = """# 🔬 Detailed Anomaly Detection Results

"""
        
        for method_name, method_results in methods.items():
            if not method_results or 'results' not in method_results:
                continue
                
            markdown_content += f"""## {method_name.replace('_', ' ').title()} Results

{self._format_method_results(method_name, method_results)}

---

"""
        
        return NotebookCellCreateRequest(
            attributes=NotebookMarkdownCellAttributes(
                definition=NotebookMarkdownCellDefinition(
                    type=NotebookMarkdownCellDefinitionType.MARKDOWN,
                    text=markdown_content
                )
            ),
            type=NotebookCellResourceType.NOTEBOOK_CELLS
        )
    
    def _create_category_analysis_cell(self, anomaly_results: Dict[str, Any]) -> NotebookCellCreateRequest:
        """Create category-wise analysis cell"""
        category_analysis = anomaly_results.get('category_analysis', {})
        
        markdown_content = f"""# 🏷️ Category-wise Anomaly Analysis

{self._format_category_analysis(category_analysis)}

## 🎯 Category Risk Assessment

{self._generate_category_risk_assessment(category_analysis)}
"""
        
        return NotebookCellCreateRequest(
            attributes=NotebookMarkdownCellAttributes(
                definition=NotebookMarkdownCellDefinition(
                    type=NotebookMarkdownCellDefinitionType.MARKDOWN,
                    text=markdown_content
                )
            ),
            type=NotebookCellResourceType.NOTEBOOK_CELLS
        )
    
    def _create_timeseries_cell(self, cost_data: Dict[str, Any]) -> NotebookCellCreateRequest:
        """Create time series visualization cell with embedded queries"""
        
        markdown_content = """# 📊 Cost Usage Visualization

## Interactive Datadog Queries

Copy and paste these queries into Datadog dashboards or notebooks for interactive visualization:

### 📈 Total Billable Usage Over Time
```
sum:datadog.estimated_usage.billable_ingested_bytes{*}
```

### 📝 Log Ingestion Costs
```
sum:datadog.estimated_usage.logs.ingested_bytes{*} by {source}
```

### 🔍 APM Trace Costs
```
sum:datadog.estimated_usage.apm.ingested_spans{*} by {service}
```

### 🖥️ Infrastructure Monitoring Costs
```
sum:datadog.estimated_usage.infra_hosts{*} by {host}
```

### 📊 Custom Metrics Usage
```
sum:datadog.estimated_usage.custom_metrics{*} by {metric_name}
```

## 🎯 Quick Dashboard Links

- [Usage Attribution Dashboard](https://app.datadoghq.com/account/usage/attribution)
- [Detailed Usage Metrics](https://app.datadoghq.com/account/usage)
- [Cost Estimation Tool](https://app.datadoghq.com/account/billing)

---

*💡 **Tip**: Use these queries in Datadog's Metrics Explorer or create custom dashboards for real-time cost monitoring.*
"""
        
        return NotebookCellCreateRequest(
            attributes=NotebookMarkdownCellAttributes(
                definition=NotebookMarkdownCellDefinition(
                    type=NotebookMarkdownCellDefinitionType.MARKDOWN,
                    text=markdown_content
                )
            ),
            type=NotebookCellResourceType.NOTEBOOK_CELLS
        )
    
    def _create_recommendations_cell(self, anomaly_results: Dict[str, Any]) -> NotebookCellCreateRequest:
        """Create recommendations cell"""
        recommendations = anomaly_results.get('recommendations', [])
        
        markdown_content = """# 💡 Recommendations & Action Items

"""
        
        if not recommendations:
            markdown_content += """## ✅ No Critical Issues Found

Your cost patterns appear to be within normal ranges. Continue monitoring for future anomalies.

### Proactive Monitoring Suggestions:
- Set up automated alerts for cost spikes >20%
- Review cost allocation monthly
- Monitor seasonal patterns for budget planning
"""
        else:
            for i, rec in enumerate(recommendations, 1):
                priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(rec.get('priority', 'low'), "🔵")
                type_emoji = {"alert": "🚨", "warning": "⚠️", "info": "ℹ️"}.get(rec.get('type', 'info'), "📝")
                
                markdown_content += f"""## {priority_emoji} {type_emoji} {rec.get('title', f'Recommendation {i}')}

**Priority:** {rec.get('priority', 'low').title()}  
**Type:** {rec.get('type', 'info').title()}

**Description:** {rec.get('description', 'No description available')}

**Recommended Action:** {rec.get('action', 'No action specified')}

---

"""
        
        return NotebookCellCreateRequest(
            attributes=NotebookMarkdownCellAttributes(
                definition=NotebookMarkdownCellDefinition(
                    type=NotebookMarkdownCellDefinitionType.MARKDOWN,
                    text=markdown_content
                )
            ),
            type=NotebookCellResourceType.NOTEBOOK_CELLS
        )
    
    def _create_investigation_queries_cell(self, anomaly_results: Dict[str, Any]) -> NotebookCellCreateRequest:
        """Create investigation queries cell"""
        markdown_content = """# 🔍 Investigation Queries & Next Steps

## 📊 Useful Datadog Queries for Further Investigation

### Cost Monitoring Queries

```
# Total billable usage over time
sum:datadog.estimated_usage.billable_ingested_bytes{*} by {service}

# Log ingestion costs
sum:datadog.estimated_usage.logs.ingested_bytes{*} by {source}

# APM trace costs  
sum:datadog.estimated_usage.apm.ingested_spans{*} by {service}

# Infrastructure monitoring costs
sum:datadog.estimated_usage.infra_hosts{*} by {host}

# Custom metrics usage
sum:datadog.estimated_usage.custom_metrics{*} by {metric_name}
```

### Anomaly Investigation Queries

```
# Identify top cost contributors during anomaly periods
sum:datadog.estimated_usage.billable_ingested_bytes{*} by {service}.rollup(sum, 3600)

# Compare usage patterns week-over-week
sum:datadog.estimated_usage.logs.ingested_bytes{*}.rollup(sum, 604800)

# Monitor sudden spikes in specific services
derivative(sum:datadog.estimated_usage.billable_ingested_bytes{service:your-service})
```

## 🎯 Investigation Checklist

### For High-Severity Anomalies:
- [ ] Check for new service deployments during anomaly periods
- [ ] Review log level configurations (DEBUG vs INFO vs ERROR)
- [ ] Analyze custom metrics creation patterns
- [ ] Verify data retention policies
- [ ] Check for runaway processes or infinite loops

### For Cost Optimization:
- [ ] Review and optimize log sampling rates
- [ ] Implement log filtering at source
- [ ] Optimize custom metrics collection
- [ ] Review dashboard and monitor configurations
- [ ] Consider data archival strategies

## 🔗 Useful Datadog Links

- [Usage Attribution](https://app.datadoghq.com/account/usage/attribution)
- [Usage Details](https://app.datadoghq.com/account/usage)
- [Cost Estimation](https://app.datadoghq.com/account/billing)
- [Log Management Settings](https://app.datadoghq.com/logs/pipelines)

---

## 📅 Next Review Schedule

**Recommended Review Frequency:** Weekly  
**Next Review Date:** {(datetime.now() + timedelta(weeks=1)).strftime('%Y-%m-%d')}  
**Escalation Threshold:** >3 high-severity anomalies in a single week
"""
        
        return NotebookCellCreateRequest(
            attributes=NotebookMarkdownCellAttributes(
                definition=NotebookMarkdownCellDefinition(
                    type=NotebookMarkdownCellDefinitionType.MARKDOWN,
                    text=markdown_content
                )
            ),
            type=NotebookCellResourceType.NOTEBOOK_CELLS
        )
    
    def _generate_impact_assessment(self, anomaly_results: Dict[str, Any], cost_data: Dict[str, Any]) -> str:
        """Generate impact assessment text"""
        summary = anomaly_results.get('summary', {})
        total_anomalies = summary.get('total_anomalies', 0)
        
        if total_anomalies == 0:
            return "✅ **Low Impact**: No significant anomalies detected. Cost patterns are within expected ranges."
        elif total_anomalies <= 2:
            return "🟡 **Medium Impact**: Few anomalies detected. Monitor closely but no immediate action required."
        else:
            return "🔴 **High Impact**: Multiple anomalies detected. Immediate investigation recommended to prevent cost overruns."
    
    def _format_anomaly_weeks(self, anomaly_weeks: List[str]) -> str:
        """Format anomaly weeks for display"""
        if not anomaly_weeks:
            return "✅ No anomalous weeks detected in the analysis period."
        
        formatted_weeks = []
        for week in sorted(anomaly_weeks)[:11]:  # Show max 11 weeks to match display expectations
            formatted_weeks.append(f"- **{week}**")
        
        result = "\n".join(formatted_weeks)
        if len(anomaly_weeks) > 11:
            result += f"\n- ... and {len(anomaly_weeks) - 11} more weeks"
        
        return result
    
    def _generate_method_performance_summary(self, anomaly_results: Dict[str, Any]) -> str:
        """Generate method performance summary"""
        methods = anomaly_results.get('methods', {})
        summary_lines = []
        
        for method_name, method_data in methods.items():
            if not method_data or 'results' not in method_data:
                continue
            
            total_detections = 0
            for category_results in method_data['results'].values():
                if isinstance(category_results, dict) and 'anomaly_count' in category_results:
                    total_detections += category_results['anomaly_count']
            
            method_display = method_name.replace('_', ' ').title()
            summary_lines.append(f"- **{method_display}**: {total_detections} anomalies detected")
        
        return "\n".join(summary_lines) if summary_lines else "No method performance data available."
    
    def _generate_cost_trend_analysis(self, cost_data: Dict[str, Any]) -> str:
        """Generate cost trend analysis"""
        trend = cost_data.get('trend', 'stable')
        total_cost = cost_data.get('total_cost', 0)
        
        trend_analysis = {
            'increasing': f"📈 **Increasing Trend**: Costs are rising. Current total: ${total_cost:,.2f}",
            'decreasing': f"📉 **Decreasing Trend**: Costs are declining. Current total: ${total_cost:,.2f}",
            'stable': f"➡️ **Stable Trend**: Costs are relatively stable. Current total: ${total_cost:,.2f}"
        }
        
        return trend_analysis.get(trend, f"Current total cost: ${total_cost:,.2f}")
    
    def _generate_category_performance(self, cost_data: Dict[str, Any]) -> str:
        """Generate category performance analysis"""
        categories = cost_data.get('categories', {})
        if not categories:
            return "No category breakdown available."
        
        performance_lines = []
        for category, cost in categories.items():
            performance_lines.append(f"- {category.title()}: ${cost:,.2f}")
        
        return "\n".join(performance_lines)
    
    def _generate_forecasting_insights(self, cost_data: Dict[str, Any]) -> str:
        """Generate forecasting insights"""
        forecast = cost_data.get('forecast', {})
        if not forecast:
            return "Forecasting data not available."
        
        next_week = forecast.get('next_week', 0)
        next_month = forecast.get('next_month', 0)
        
        return f"""Based on current trends:
- Next Week Estimate: ${next_week:,.2f}
- Next Month Estimate: ${next_month:,.2f}

*Note: Forecasts are based on historical patterns and may not account for planned changes.*"""
    
    def _format_method_results(self, method_name: str, method_results: Dict[str, Any]) -> str:
        """Format method results for display"""
        results = method_results.get('results', {})
        if not results:
            return f"No anomalies detected using {method_name.replace('_', ' ')} method."
        
        formatted_results = []
        for category, category_results in results.items():
            if isinstance(category_results, dict) and 'anomaly_count' in category_results:
                count = category_results['anomaly_count']
                if count > 0:
                    formatted_results.append(f"- {category.title()}: {count} anomalies")
        
        return "\n".join(formatted_results) if formatted_results else "No significant anomalies detected."
    
    def _format_category_analysis(self, category_analysis: Dict[str, Any]) -> str:
        """Format category analysis for display"""
        if not category_analysis:
            return "No category analysis data available."
        
        analysis_lines = []
        for category, analysis in category_analysis.items():
            frequency = analysis.get('anomaly_frequency', 0)
            methods = analysis.get('most_common_methods', [])
            
            if frequency > 0:
                methods_str = ", ".join(methods[:3]) if methods else "Various"
                analysis_lines.append(f"- {category.title()}: {frequency} anomalies (detected by: {methods_str})")
        
        return "\n".join(analysis_lines) if analysis_lines else "No category-specific anomalies detected."
    
    def _generate_category_risk_assessment(self, category_analysis: Dict[str, Any]) -> str:
        """Generate category risk assessment"""
        if not category_analysis:
            return "All categories appear to be low risk."
        
        high_risk = []
        medium_risk = []
        
        for category, analysis in category_analysis.items():
            frequency = analysis.get('anomaly_frequency', 0)
            if frequency >= 3:
                high_risk.append(category)
            elif frequency >= 1:
                medium_risk.append(category)
        
        risk_assessment = []
        if high_risk:
            risk_assessment.append(f"High Risk Categories: {', '.join(high_risk)}")
        if medium_risk:
            risk_assessment.append(f"Medium Risk Categories: {', '.join(medium_risk)}")
        
        if not risk_assessment:
            risk_assessment.append("🟢 **All categories are low risk**")
        
        return "\n".join(risk_assessment)
    
    def update_notebook(self, notebook_id: str, anomaly_results: Dict[str, Any], cost_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing notebook with new anomaly analysis results
        
        Args:
            notebook_id: ID of the existing notebook
            anomaly_results: New anomaly detection results
            cost_data: Updated cost data
            
        Returns:
            Dictionary containing update results
        """
        try:
            # Get existing notebook
            existing_notebook = NotebooksApi(self.api_client).get_notebook(notebook_id)
            
            # Create new cells with updated data
            updated_cells = self._create_notebook_cells(anomaly_results, cost_data)
            
            # Update notebook
            update_request = {
                "data": {
                    "type": "notebooks",
                    "attributes": {
                        "cells": updated_cells,
                        "metadata": {
                            **existing_notebook.data.attributes.metadata,
                            "last_updated": datetime.now().isoformat(),
                            "update_count": existing_notebook.data.attributes.metadata.get("update_count", 0) + 1
                        }
                    }
                }
            }
            
            response = NotebooksApi(self.api_client).update_notebook(notebook_id, update_request)
            
            return {
                "success": True,
                "notebook_id": notebook_id,
                "updated_at": datetime.now().isoformat(),
                "cell_count": len(updated_cells)
            }
            
        except Exception as e:
            logger.error(f"Failed to update notebook {notebook_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "notebook_id": notebook_id
            }
    
    def list_cost_analysis_notebooks(self, tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        List existing cost analysis notebooks
        
        Args:
            tags: Filter by specific tags
            
        Returns:
            List of notebook information
        """
        try:
            if not tags:
                tags = ["cost-analysis"]
            
            # Get notebooks with cost analysis tags
            notebooks = NotebooksApi(self.api_client).list_notebooks(tags=tags)
            
            notebook_list = []
            for notebook in notebooks.data:
                notebook_info = {
                    "id": notebook.id,
                    "name": notebook.attributes.name,
                    "created_at": notebook.attributes.created_at.isoformat() if notebook.attributes.created_at else None,
                    "modified_at": notebook.attributes.modified_at.isoformat() if notebook.attributes.modified_at else None,
                    "tags": notebook.attributes.tags,
                    "url": f"https://app.{self.configuration.server_variables['site']}/notebook/{notebook.id}"
                }
                notebook_list.append(notebook_info)
            
            return notebook_list
            
        except Exception as e:
            logger.error(f"Failed to list notebooks: {str(e)}")
            return []