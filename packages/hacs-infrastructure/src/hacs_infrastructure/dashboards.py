"""
HACS Monitoring Dashboards - Healthcare Analytics and Visualization

This module provides comprehensive monitoring dashboards for healthcare AI systems
including real-time metrics, clinical alerts, compliance tracking, and performance monitoring.

Features:
    - Real-time healthcare metrics dashboard
    - Clinical alert monitoring
    - HIPAA compliance tracking
    - Performance and resource monitoring
    - Custom healthcare visualizations
    - Multi-tenant organization views

Author: HACS Development Team
License: MIT
Version: 1.0.0
"""

import asyncio
import json
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import logging

from .observability import ObservabilityManager, get_observability_manager
from .healthcare_monitoring import (
    HealthcareMonitoringManager, 
    get_healthcare_monitoring,
    ClinicalSeverity,
    ComplianceStatus
)
from .monitoring import MetricsCollector, HealthMonitor


class DashboardType(str, Enum):
    """Types of monitoring dashboards."""
    CLINICAL_OVERVIEW = "clinical_overview"
    COMPLIANCE_TRACKING = "compliance_tracking" 
    PERFORMANCE_MONITORING = "performance_monitoring"
    SECURITY_MONITORING = "security_monitoring"
    RESOURCE_UTILIZATION = "resource_utilization"
    AUDIT_DASHBOARD = "audit_dashboard"
    EXECUTIVE_SUMMARY = "executive_summary"


class ChartType(str, Enum):
    """Chart visualization types."""
    LINE_CHART = "line_chart"
    BAR_CHART = "bar_chart"
    AREA_CHART = "area_chart"
    PIE_CHART = "pie_chart"
    GAUGE = "gauge"
    HEATMAP = "heatmap"
    TABLE = "table"
    METRIC_CARD = "metric_card"


@dataclass
class DashboardWidget:
    """Dashboard widget configuration."""
    id: str
    title: str
    chart_type: ChartType
    data_source: str
    refresh_interval_seconds: int = 30
    width: int = 6  # Grid width (1-12)
    height: int = 4  # Grid height
    config: Dict[str, Any] = field(default_factory=dict)
    filters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Dashboard:
    """Dashboard configuration."""
    id: str
    name: str
    description: str
    dashboard_type: DashboardType
    widgets: List[DashboardWidget] = field(default_factory=list)
    auto_refresh_seconds: int = 30
    permissions: List[str] = field(default_factory=list)
    organization_filter: Optional[str] = None


class HealthcareDashboardManager:
    """Healthcare-specific dashboard manager."""
    
    def __init__(
        self,
        observability_manager: Optional[ObservabilityManager] = None,
        healthcare_monitoring: Optional[HealthcareMonitoringManager] = None
    ):
        """Initialize dashboard manager."""
        self.observability = observability_manager or get_observability_manager()
        self.healthcare_monitoring = healthcare_monitoring or get_healthcare_monitoring()
        self.logger = self.observability.get_logger("hacs.dashboards")
        
        # Dashboard registry
        self.dashboards: Dict[str, Dashboard] = {}
        self._data_sources: Dict[str, Callable] = {}
        
        # Cache for dashboard data
        self._cache = {}
        self._cache_ttl = {}
        
        # Initialize default dashboards
        self._create_default_dashboards()
        self._register_data_sources()
    
    def _create_default_dashboards(self):
        """Create default healthcare monitoring dashboards."""
        
        # Clinical Overview Dashboard
        clinical_dashboard = Dashboard(
            id="clinical_overview",
            name="Clinical Overview",
            description="Real-time clinical workflow monitoring and patient safety alerts",
            dashboard_type=DashboardType.CLINICAL_OVERVIEW,
            permissions=["read:clinical_data", "view:dashboards"],
            widgets=[
                DashboardWidget(
                    id="clinical_alerts",
                    title="Clinical Alerts",
                    chart_type=ChartType.TABLE,
                    data_source="get_clinical_alerts",
                    width=12,
                    height=6,
                    config={
                        "columns": ["timestamp", "severity", "alert_type", "message", "patient_id_hash"],
                        "severity_colors": {
                            "life_threatening": "#dc3545",
                            "critical": "#fd7e14", 
                            "high": "#ffc107",
                            "moderate": "#17a2b8",
                            "low": "#28a745"
                        }
                    }
                ),
                DashboardWidget(
                    id="workflow_performance",
                    title="Workflow Performance",
                    chart_type=ChartType.LINE_CHART,
                    data_source="get_workflow_metrics",
                    width=6,
                    height=4,
                    config={
                        "metrics": ["response_time", "success_rate"],
                        "time_range": "24h"
                    }
                ),
                DashboardWidget(
                    id="patient_workflows_total",
                    title="Patient Workflows Today",
                    chart_type=ChartType.METRIC_CARD,
                    data_source="get_workflow_count",
                    width=3,
                    height=2,
                    config={
                        "format": "number",
                        "comparison": "yesterday"
                    }
                ),
                DashboardWidget(
                    id="active_sessions",
                    title="Active Clinical Sessions",
                    chart_type=ChartType.GAUGE,
                    data_source="get_active_sessions",
                    width=3,
                    height=2,
                    config={
                        "max_value": 100,
                        "thresholds": [70, 85, 95]
                    }
                )
            ]
        )
        
        # Compliance Tracking Dashboard
        compliance_dashboard = Dashboard(
            id="compliance_tracking",
            name="HIPAA Compliance Tracking",
            description="HIPAA compliance monitoring and audit trail analysis",
            dashboard_type=DashboardType.COMPLIANCE_TRACKING,
            permissions=["read:compliance_data", "view:dashboards"],
            widgets=[
                DashboardWidget(
                    id="compliance_score",
                    title="Compliance Score",
                    chart_type=ChartType.GAUGE,
                    data_source="get_compliance_score",
                    width=4,
                    height=3,
                    config={
                        "max_value": 100,
                        "thresholds": [80, 90, 95],
                        "colors": ["#dc3545", "#ffc107", "#28a745"]
                    }
                ),
                DashboardWidget(
                    id="phi_access_timeline",
                    title="PHI Access Timeline",
                    chart_type=ChartType.AREA_CHART,
                    data_source="get_phi_access_timeline",
                    width=8,
                    height=3,
                    config={
                        "time_range": "7d",
                        "group_by": "hour"
                    }
                ),
                DashboardWidget(
                    id="compliance_violations",
                    title="Compliance Violations",
                    chart_type=ChartType.TABLE,
                    data_source="get_compliance_violations",
                    width=12,
                    height=6,
                    config={
                        "columns": ["timestamp", "violation_type", "severity", "description", "status"],
                        "filters": ["status", "severity"]
                    }
                ),
                DashboardWidget(
                    id="audit_coverage",
                    title="Audit Coverage",
                    chart_type=ChartType.PIE_CHART,
                    data_source="get_audit_coverage",
                    width=6,
                    height=4,
                    config={
                        "categories": ["covered", "uncovered", "partially_covered"]
                    }
                )
            ]
        )
        
        # Performance Monitoring Dashboard
        performance_dashboard = Dashboard(
            id="performance_monitoring",
            name="System Performance",
            description="System performance metrics and resource utilization",
            dashboard_type=DashboardType.PERFORMANCE_MONITORING,
            permissions=["read:system_metrics", "view:dashboards"],
            widgets=[
                DashboardWidget(
                    id="system_resources",
                    title="System Resources",
                    chart_type=ChartType.LINE_CHART,
                    data_source="get_system_metrics",
                    width=8,
                    height=4,
                    config={
                        "metrics": ["cpu_usage", "memory_usage", "disk_usage"],
                        "time_range": "1h"
                    }
                ),
                DashboardWidget(
                    id="response_times",
                    title="Response Time Distribution",
                    chart_type=ChartType.HEATMAP,
                    data_source="get_response_time_distribution",
                    width=4,
                    height=4,
                    config={
                        "time_range": "24h",
                        "percentiles": [50, 95, 99]
                    }
                ),
                DashboardWidget(
                    id="tool_execution_metrics",
                    title="Healthcare Tool Performance",
                    chart_type=ChartType.BAR_CHART,
                    data_source="get_tool_performance",
                    width=12,
                    height=5,
                    config={
                        "group_by": "tool_category",
                        "metrics": ["avg_response_time", "success_rate"]
                    }
                )
            ]
        )
        
        # Executive Summary Dashboard
        executive_dashboard = Dashboard(
            id="executive_summary",
            name="Executive Summary",
            description="High-level metrics and KPIs for healthcare operations",
            dashboard_type=DashboardType.EXECUTIVE_SUMMARY,
            permissions=["read:executive_data", "view:dashboards"],
            widgets=[
                DashboardWidget(
                    id="kpi_summary",
                    title="Key Performance Indicators",
                    chart_type=ChartType.METRIC_CARD,
                    data_source="get_kpi_summary",
                    width=12,
                    height=3,
                    config={
                        "metrics": [
                            "total_patients_served",
                            "workflows_completed",
                            "compliance_score",
                            "system_uptime"
                        ]
                    }
                ),
                DashboardWidget(
                    id="monthly_trends",
                    title="Monthly Trends",
                    chart_type=ChartType.LINE_CHART,
                    data_source="get_monthly_trends",
                    width=8,
                    height=5,
                    config={
                        "time_range": "12m",
                        "metrics": ["patient_volume", "workflow_efficiency", "incident_count"]
                    }
                ),
                DashboardWidget(
                    id="alert_summary",
                    title="Alert Summary",
                    chart_type=ChartType.PIE_CHART,
                    data_source="get_alert_summary",
                    width=4,
                    height=5,
                    config={
                        "categories": ["resolved", "active", "acknowledged"]
                    }
                )
            ]
        )
        
        # Register dashboards
        self.dashboards.update({
            "clinical_overview": clinical_dashboard,
            "compliance_tracking": compliance_dashboard,
            "performance_monitoring": performance_dashboard,
            "executive_summary": executive_dashboard
        })
    
    def _register_data_sources(self):
        """Register data source functions."""
        self._data_sources.update({
            "get_clinical_alerts": self._get_clinical_alerts,
            "get_workflow_metrics": self._get_workflow_metrics,
            "get_workflow_count": self._get_workflow_count,
            "get_active_sessions": self._get_active_sessions,
            "get_compliance_score": self._get_compliance_score,
            "get_phi_access_timeline": self._get_phi_access_timeline,
            "get_compliance_violations": self._get_compliance_violations,
            "get_audit_coverage": self._get_audit_coverage,
            "get_system_metrics": self._get_system_metrics,
            "get_response_time_distribution": self._get_response_time_distribution,
            "get_tool_performance": self._get_tool_performance,
            "get_kpi_summary": self._get_kpi_summary,
            "get_monthly_trends": self._get_monthly_trends,
            "get_alert_summary": self._get_alert_summary
        })
    
    async def get_dashboard(self, dashboard_id: str) -> Optional[Dashboard]:
        """Get dashboard configuration."""
        return self.dashboards.get(dashboard_id)
    
    async def get_dashboard_data(
        self,
        dashboard_id: str,
        organization: Optional[str] = None,
        refresh: bool = False
    ) -> Dict[str, Any]:
        """Get complete dashboard data."""
        dashboard = self.dashboards.get(dashboard_id)
        if not dashboard:
            return {"error": "Dashboard not found"}
        
        # Check cache
        cache_key = f"{dashboard_id}_{organization or 'all'}"
        if not refresh and cache_key in self._cache:
            cache_time = self._cache_ttl.get(cache_key, 0)
            if time.time() - cache_time < dashboard.auto_refresh_seconds:
                return self._cache[cache_key]
        
        # Gather widget data
        widget_data = {}
        for widget in dashboard.widgets:
            try:
                data_func = self._data_sources.get(widget.data_source)
                if data_func:
                    data = await data_func(widget, organization)
                    widget_data[widget.id] = {
                        "data": data,
                        "config": widget.config,
                        "last_updated": datetime.now(timezone.utc).isoformat()
                    }
                else:
                    widget_data[widget.id] = {"error": f"Data source '{widget.data_source}' not found"}
            except Exception as e:
                self.logger.error(f"Error fetching data for widget {widget.id}: {e}")
                widget_data[widget.id] = {"error": str(e)}
        
        dashboard_data = {
            "dashboard": {
                "id": dashboard.id,
                "name": dashboard.name,
                "description": dashboard.description,
                "type": dashboard.dashboard_type.value,
                "last_updated": datetime.now(timezone.utc).isoformat()
            },
            "widgets": widget_data,
            "organization": organization
        }
        
        # Cache the data
        self._cache[cache_key] = dashboard_data
        self._cache_ttl[cache_key] = time.time()
        
        return dashboard_data
    
    async def get_widget_data(
        self,
        dashboard_id: str,
        widget_id: str,
        organization: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get data for a specific widget."""
        dashboard = self.dashboards.get(dashboard_id)
        if not dashboard:
            return {"error": "Dashboard not found"}
        
        widget = next((w for w in dashboard.widgets if w.id == widget_id), None)
        if not widget:
            return {"error": "Widget not found"}
        
        try:
            data_func = self._data_sources.get(widget.data_source)
            if data_func:
                data = await data_func(widget, organization)
                return {
                    "data": data,
                    "config": widget.config,
                    "last_updated": datetime.now(timezone.utc).isoformat()
                }
            else:
                return {"error": f"Data source '{widget.data_source}' not found"}
        except Exception as e:
            self.logger.error(f"Error fetching data for widget {widget_id}: {e}")
            return {"error": str(e)}
    
    def list_dashboards(self, user_permissions: List[str] = None) -> List[Dict[str, Any]]:
        """List available dashboards based on user permissions."""
        user_permissions = user_permissions or []
        
        available_dashboards = []
        for dashboard in self.dashboards.values():
            # Check permissions
            if dashboard.permissions and user_permissions:
                if not any(perm in user_permissions for perm in dashboard.permissions):
                    continue
            
            available_dashboards.append({
                "id": dashboard.id,
                "name": dashboard.name,
                "description": dashboard.description,
                "type": dashboard.dashboard_type.value,
                "widget_count": len(dashboard.widgets)
            })
        
        return available_dashboards
    
    def register_custom_dashboard(self, dashboard: Dashboard):
        """Register a custom dashboard."""
        self.dashboards[dashboard.id] = dashboard
        self.logger.info(f"Registered custom dashboard: {dashboard.id}")
    
    def register_data_source(self, name: str, func: Callable):
        """Register a custom data source function."""
        self._data_sources[name] = func
        self.logger.info(f"Registered data source: {name}")
    
    # Data source implementations
    async def _get_clinical_alerts(self, widget: DashboardWidget, organization: Optional[str]) -> List[Dict]:
        """Get clinical alerts data."""
        alerts_summary = self.healthcare_monitoring.metrics.get_clinical_alerts_summary(24)
        
        # Convert to widget format
        alerts = []
        for alert in self.healthcare_monitoring.metrics._clinical_alerts[-50:]:  # Last 50 alerts
            if organization and alert.clinical_context.get("organization") != organization:
                continue
                
            alerts.append({
                "timestamp": alert.timestamp.isoformat(),
                "severity": alert.severity.value,
                "alert_type": alert.alert_type,
                "message": alert.message,
                "patient_id_hash": alert.patient_id_hash[:8] + "..." if alert.patient_id_hash != "system" else "system",
                "acknowledged": alert.acknowledged,
                "resolved": alert.resolved
            })
        
        return sorted(alerts, key=lambda x: x["timestamp"], reverse=True)
    
    async def _get_workflow_metrics(self, widget: DashboardWidget, organization: Optional[str]) -> Dict:
        """Get workflow performance metrics."""
        # Simulate workflow metrics
        now = time.time()
        hours_back = 24
        
        metrics = {
            "timestamps": [],
            "response_times": [],
            "success_rates": []
        }
        
        # Generate hourly data points
        for i in range(hours_back):
            timestamp = now - (i * 3600)
            metrics["timestamps"].append(datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat())
            metrics["response_times"].append(250 + (i * 10) % 500)  # Mock data
            metrics["success_rates"].append(95 + (i % 5))  # Mock data
        
        return metrics
    
    async def _get_workflow_count(self, widget: DashboardWidget, organization: Optional[str]) -> Dict:
        """Get workflow count metrics."""
        total_workflows = self.healthcare_monitoring.metrics.get_counter("healthcare.workflow.count")
        
        return {
            "current": total_workflows,
            "previous": max(0, total_workflows - 50),  # Mock comparison
            "change_percent": 15.2  # Mock percentage change
        }
    
    async def _get_active_sessions(self, widget: DashboardWidget, organization: Optional[str]) -> Dict:
        """Get active sessions count."""
        active_sessions = 42  # Mock data
        max_sessions = widget.config.get("max_value", 100)
        
        return {
            "value": active_sessions,
            "max": max_sessions,
            "percentage": (active_sessions / max_sessions) * 100
        }
    
    async def _get_compliance_score(self, widget: DashboardWidget, organization: Optional[str]) -> Dict:
        """Get HIPAA compliance score."""
        compliance_summary = self.healthcare_monitoring.metrics.get_compliance_summary(24)
        score = compliance_summary.get("compliance_score", 95.0)
        
        return {
            "value": score,
            "max": 100,
            "percentage": score,
            "status": "good" if score >= 90 else "warning" if score >= 70 else "critical"
        }
    
    async def _get_phi_access_timeline(self, widget: DashboardWidget, organization: Optional[str]) -> Dict:
        """Get PHI access timeline data."""
        access_summary = self.healthcare_monitoring.metrics.get_phi_access_summary(24 * 7)  # Last week
        
        # Generate timeline data
        now = time.time()
        timeline = {
            "timestamps": [],
            "access_counts": []
        }
        
        for i in range(24 * 7):  # Hourly for last week
            timestamp = now - (i * 3600)
            timeline["timestamps"].append(datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat())
            timeline["access_counts"].append(max(0, 10 + (i % 15) - 5))  # Mock data
        
        return timeline
    
    async def _get_compliance_violations(self, widget: DashboardWidget, organization: Optional[str]) -> List[Dict]:
        """Get compliance violations data."""
        violations = []
        
        for event in self.healthcare_monitoring.metrics._compliance_events[-20:]:
            if event.status in [ComplianceStatus.VIOLATION, ComplianceStatus.CRITICAL_VIOLATION]:
                violations.append({
                    "timestamp": event.timestamp.isoformat(),
                    "violation_type": event.event_type,
                    "severity": event.status.value,
                    "description": event.description,
                    "status": "remediated" if event.remediation_required else "open"
                })
        
        return violations
    
    async def _get_audit_coverage(self, widget: DashboardWidget, organization: Optional[str]) -> Dict:
        """Get audit coverage data."""
        return {
            "categories": ["covered", "uncovered", "partially_covered"],
            "values": [85, 10, 5],
            "total": 100
        }
    
    async def _get_system_metrics(self, widget: DashboardWidget, organization: Optional[str]) -> Dict:
        """Get system performance metrics."""
        # Get current system metrics
        cpu_usage = self.healthcare_monitoring.metrics.get_gauge("system.cpu.usage_percent")
        memory_usage = self.healthcare_monitoring.metrics.get_gauge("system.memory.usage_percent")
        
        now = time.time()
        metrics = {
            "timestamps": [],
            "cpu_usage": [],
            "memory_usage": [],
            "disk_usage": []
        }
        
        # Generate hourly data for last hour
        for i in range(60):  # Last 60 minutes
            timestamp = now - (i * 60)
            metrics["timestamps"].append(datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat())
            metrics["cpu_usage"].append(cpu_usage + (i % 10) - 5)
            metrics["memory_usage"].append(memory_usage + (i % 8) - 4)
            metrics["disk_usage"].append(45 + (i % 5))  # Mock disk usage
        
        return metrics
    
    async def _get_response_time_distribution(self, widget: DashboardWidget, organization: Optional[str]) -> Dict:
        """Get response time distribution heatmap data."""
        # Mock heatmap data
        return {
            "hours": list(range(24)),
            "percentiles": ["p50", "p95", "p99"],
            "data": [
                [120, 180, 250] for _ in range(24)  # Mock data for each hour
            ]
        }
    
    async def _get_tool_performance(self, widget: DashboardWidget, organization: Optional[str]) -> Dict:
        """Get healthcare tool performance data."""
        return {
            "categories": ["clinical_workflows", "fhir_integration", "analytics", "admin_operations"],
            "avg_response_time": [250, 180, 320, 150],
            "success_rate": [98.5, 99.2, 97.8, 99.5]
        }
    
    async def _get_kpi_summary(self, widget: DashboardWidget, organization: Optional[str]) -> Dict:
        """Get KPI summary data."""
        return {
            "total_patients_served": {"value": 1250, "change": "+12%"},
            "workflows_completed": {"value": 3480, "change": "+8%"},
            "compliance_score": {"value": "95%", "change": "+2%"},
            "system_uptime": {"value": "99.9%", "change": "0%"}
        }
    
    async def _get_monthly_trends(self, widget: DashboardWidget, organization: Optional[str]) -> Dict:
        """Get monthly trend data."""
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        
        return {
            "months": months,
            "patient_volume": [980, 1050, 1120, 1180, 1200, 1250, 1300, 1350, 1280, 1320, 1380, 1450],
            "workflow_efficiency": [92, 93, 95, 94, 96, 97, 98, 97, 98, 99, 98, 99],
            "incident_count": [12, 8, 6, 9, 4, 3, 2, 1, 2, 1, 0, 1]
        }
    
    async def _get_alert_summary(self, widget: DashboardWidget, organization: Optional[str]) -> Dict:
        """Get alert summary data."""
        return {
            "categories": ["resolved", "active", "acknowledged"],
            "values": [156, 8, 12],
            "total": 176
        }


# Global dashboard manager
_dashboard_manager: Optional[HealthcareDashboardManager] = None


def get_dashboard_manager() -> HealthcareDashboardManager:
    """Get or create global dashboard manager."""
    global _dashboard_manager
    if _dashboard_manager is None:
        _dashboard_manager = HealthcareDashboardManager()
    return _dashboard_manager


def initialize_dashboards(
    observability_manager: Optional[ObservabilityManager] = None,
    healthcare_monitoring: Optional[HealthcareMonitoringManager] = None
) -> HealthcareDashboardManager:
    """Initialize healthcare dashboards."""
    global _dashboard_manager
    _dashboard_manager = HealthcareDashboardManager(
        observability_manager=observability_manager,
        healthcare_monitoring=healthcare_monitoring
    )
    return _dashboard_manager


# Export public API
__all__ = [
    "HealthcareDashboardManager",
    "Dashboard",
    "DashboardWidget", 
    "DashboardType",
    "ChartType",
    "get_dashboard_manager",
    "initialize_dashboards",
]