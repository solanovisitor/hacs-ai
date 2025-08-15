#!/usr/bin/env python3
"""
HF Ingestion Workflow Visualizer

Provides comprehensive visual reporting and analysis for the HF ingestion workflow.
Generates DAG cards, performance metrics, resource analysis, and interactive reports.
"""

import os
import json
import time
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.tree import Tree
from rich.syntax import Syntax
from rich.markdown import Markdown

# Set up rich console for beautiful output
console = Console(record=True)
logger = logging.getLogger(__name__)

@dataclass
class WorkflowMetrics:
    """Comprehensive workflow performance metrics."""
    stage_name: str
    start_time: float
    end_time: float
    duration: float
    success: bool
    resources_processed: int = 0
    resources_created: int = 0
    errors: List[str] = None
    memory_usage_mb: float = 0.0
    throughput_per_sec: float = 0.0

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.resources_processed > 0:
            self.throughput_per_sec = self.resources_processed / self.duration if self.duration > 0 else 0


@dataclass
class ResourceAnalysis:
    """Analysis of created HACS resources."""
    resource_type: str
    count: int
    success_rate: float
    avg_fields_populated: float
    sample_resource: Dict[str, Any] = None
    field_distribution: Dict[str, int] = None

    def __post_init__(self):
        if self.field_distribution is None:
            self.field_distribution = {}


class WorkflowVisualizer:
    """Enhanced workflow visualization and reporting."""
    
    def __init__(self, output_dir: str = "workflow_reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.metrics: List[WorkflowMetrics] = []
        self.start_time = time.time()
        
        # Configure matplotlib for better visuals
        plt.style.use('seaborn-v0_8-darkgrid')
        sns.set_palette("husl")
        
    def log_stage_start(self, stage_name: str) -> str:
        """Log the start of a workflow stage."""
        stage_id = f"{stage_name}_{int(time.time())}"
        console.print(f"\n🚀 [bold blue]Starting Stage:[/bold blue] {stage_name}")
        return stage_id
        
    def log_stage_end(self, stage_name: str, stage_id: str, success: bool, 
                     resources_processed: int = 0, resources_created: int = 0, 
                     errors: List[str] = None):
        """Log the completion of a workflow stage."""
        end_time = time.time()
        # Extract start time from stage_id
        start_time = float(stage_id.split('_')[-1])
        duration = end_time - start_time
        
        metrics = WorkflowMetrics(
            stage_name=stage_name,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            success=success,
            resources_processed=resources_processed,
            resources_created=resources_created,
            errors=errors or []
        )
        
        self.metrics.append(metrics)
        
        # Visual status indicator
        status_icon = "✅" if success else "❌"
        status_color = "green" if success else "red"
        
        console.print(f"{status_icon} [bold {status_color}]Stage Complete:[/bold {status_color}] {stage_name}")
        console.print(f"   ⏱️  Duration: {duration:.2f}s")
        if resources_processed > 0:
            console.print(f"   📊 Processed: {resources_processed} resources")
        if resources_created > 0:
            console.print(f"   🏗️  Created: {resources_created} resources")
        if errors:
            console.print(f"   ⚠️  Errors: {len(errors)}")
            
    def create_workflow_dag(self) -> str:
        """Create a visual DAG representation of the workflow."""
        dag_tree = Tree("🔄 [bold blue]HF Ingestion Workflow DAG[/bold blue]")
        
        # Add workflow stages as tree branches
        stages = {
            "📊 Dataset Loading": ["🔐 HF Authentication", "📥 Data Download", "🔍 Structure Analysis"],
            "🛠️ HACS Tools Validation": ["🔧 Tool Discovery", "📋 Schema Retrieval", "✅ Capability Check"],
            "🏗️ Template Registration": ["📝 Markdown Parsing", "🎯 Resource Mapping", "💾 Template Storage"],
            "⚙️ Resource Processing": ["🔄 Batch Processing", "🏥 Stack Instantiation", "💽 Database Persistence"],
            "📋 Report Generation": ["📊 Metrics Collection", "📈 Analysis", "📄 Report Export"]
        }
        
        for main_stage, sub_stages in stages.items():
            stage_branch = dag_tree.add(main_stage)
            for sub_stage in sub_stages:
                stage_branch.add(sub_stage)
                
        return dag_tree
    
    def create_performance_timeline(self) -> str:
        """Create a performance timeline visualization."""
        if not self.metrics:
            return "No metrics available for timeline"
            
        # Create timeline data
        timeline_data = []
        for i, metric in enumerate(self.metrics):
            start_relative = metric.start_time - self.start_time
            end_relative = metric.end_time - self.start_time
            timeline_data.append({
                'Stage': metric.stage_name,
                'Start': start_relative,
                'Duration': metric.duration,
                'Success': metric.success,
                'Throughput': metric.throughput_per_sec
            })
            
        # Create performance table
        table = Table(title="🕒 Workflow Performance Timeline")
        table.add_column("Stage", style="cyan", no_wrap=True)
        table.add_column("Start (s)", justify="right", style="magenta")
        table.add_column("Duration (s)", justify="right", style="yellow")
        table.add_column("Status", justify="center")
        table.add_column("Throughput/s", justify="right", style="green")
        
        for data in timeline_data:
            status = "✅" if data['Success'] else "❌"
            throughput = f"{data['Throughput']:.2f}" if data['Throughput'] > 0 else "N/A"
            table.add_row(
                data['Stage'],
                f"{data['Start']:.2f}",
                f"{data['Duration']:.2f}",
                status,
                throughput
            )
            
        return table
    
    def create_resource_analysis_chart(self, resources_data: Dict[str, Any]) -> str:
        """Create resource analysis visualization."""
        if not resources_data:
            return Panel("No resource data available", title="📊 Resource Analysis")
            
        # Create resource summary table
        table = Table(title="🏥 HACS Resource Analysis")
        table.add_column("Resource Type", style="cyan")
        table.add_column("Count", justify="right", style="magenta")
        table.add_column("Success Rate", justify="right", style="green")
        table.add_column("Avg Fields", justify="right", style="yellow")
        
        resource_counts = resources_data.get('resource_counts', {})
        total_resources = sum(resource_counts.values())
        
        for resource_type, count in resource_counts.items():
            success_rate = "100%" if count > 0 else "0%"  # Simplified for now
            avg_fields = "N/A"  # Would need detailed analysis
            table.add_row(resource_type, str(count), success_rate, avg_fields)
            
        # Add summary row
        table.add_row(
            "[bold]TOTAL[/bold]", 
            f"[bold]{total_resources}[/bold]", 
            "[bold]N/A[/bold]", 
            "[bold]N/A[/bold]"
        )
        
        return table
    
    def create_error_analysis(self, errors_data: Dict[str, Any]) -> str:
        """Create error analysis visualization."""
        error_patterns = errors_data.get('error_frequency', {})
        
        if not error_patterns:
            return Panel("✅ No errors detected!", title="🔍 Error Analysis", style="green")
            
        table = Table(title="⚠️ Error Analysis")
        table.add_column("Error Pattern", style="red")
        table.add_column("Frequency", justify="right", style="yellow")
        table.add_column("Impact", justify="center", style="magenta")
        
        for error, count in error_patterns.items():
            impact = "🔥 HIGH" if count > 5 else "⚠️ MEDIUM" if count > 2 else "🟡 LOW"
            table.add_row(error[:80] + "..." if len(error) > 80 else error, str(count), impact)
            
        return table
    
    def generate_workflow_report(self, results_data: Dict[str, Any]) -> str:
        """Generate comprehensive workflow report."""
        report_path = self.output_dir / f"workflow_report_{int(time.time())}.html"
        
        # Extract data
        summary = results_data.get('report', {}).get('summary', {})
        resource_analysis = results_data.get('report', {}).get('resource_analysis', {})
        error_analysis = results_data.get('report', {}).get('error_analysis', {})
        
        # Create comprehensive report
        console.print("\n" + "="*80)
        console.print(Panel.fit("🎯 COMPREHENSIVE WORKFLOW REPORT", style="bold blue"))
        console.print("="*80)
        
        # 1. DAG Visualization
        console.print("\n📊 [bold blue]WORKFLOW STRUCTURE[/bold blue]")
        console.print(self.create_workflow_dag())
        
        # 2. Performance Timeline
        console.print("\n⏱️ [bold blue]PERFORMANCE TIMELINE[/bold blue]")
        console.print(self.create_performance_timeline())
        
        # 3. Summary Statistics
        console.print("\n📈 [bold blue]EXECUTION SUMMARY[/bold blue]")
        summary_table = Table(title="Workflow Summary")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="yellow")
        summary_table.add_column("Status", justify="center")
        
        total_time = sum(m.duration for m in self.metrics)
        success_rate = summary.get('success_rate', 0) * 100
        
        summary_table.add_row("Total Records", str(summary.get('total_records', 0)), "📊")
        summary_table.add_row("Successful", str(summary.get('successful_records', 0)), "✅")
        summary_table.add_row("Failed", str(summary.get('failed_records', 0)), "❌")
        summary_table.add_row("Success Rate", f"{success_rate:.1f}%", "📈")
        summary_table.add_row("Total Time", f"{total_time:.2f}s", "⏱️")
        summary_table.add_row("Resources Created", str(resource_analysis.get('total_resources', 0)), "🏗️")
        
        console.print(summary_table)
        
        # 4. Resource Analysis
        console.print("\n🏥 [bold blue]RESOURCE ANALYSIS[/bold blue]")
        console.print(self.create_resource_analysis_chart(resource_analysis))
        
        # 5. Error Analysis
        console.print("\n🔍 [bold blue]ERROR ANALYSIS[/bold blue]")
        console.print(self.create_error_analysis(error_analysis))
        
        # 6. Performance Insights
        console.print("\n💡 [bold blue]PERFORMANCE INSIGHTS[/bold blue]")
        insights_panel = self._generate_insights(summary, resource_analysis, error_analysis)
        console.print(insights_panel)
        
        # Save HTML report
        html_content = console.export_html()
        with open(report_path, 'w') as f:
            f.write(html_content)
            
        console.print(f"\n📄 [bold green]Report saved to:[/bold green] {report_path}")
        return str(report_path)
    
    def _generate_insights(self, summary: Dict, resources: Dict, errors: Dict) -> Panel:
        """Generate performance insights and recommendations."""
        insights = []
        
        # Performance insights
        total_records = summary.get('total_records', 0)
        success_rate = summary.get('success_rate', 0)
        total_time = sum(m.duration for m in self.metrics)
        
        if success_rate > 0.8:
            insights.append("✅ Excellent success rate - workflow is performing well")
        elif success_rate > 0.5:
            insights.append("⚠️ Moderate success rate - consider error investigation")
        else:
            insights.append("🔥 Low success rate - immediate attention required")
            
        if total_time > 0 and total_records > 0:
            throughput = total_records / total_time
            insights.append(f"📊 Processing throughput: {throughput:.2f} records/second")
            
        # Resource insights
        resource_types = len(resources.get('types_created', []))
        if resource_types > 5:
            insights.append(f"🏥 Rich resource diversity: {resource_types} different types created")
        elif resource_types > 0:
            insights.append(f"🏥 Limited resource types: {resource_types} types (consider expanding)")
        else:
            insights.append("⚠️ No resources created - check workflow configuration")
            
        # Error insights
        error_count = len(errors.get('error_frequency', {}))
        if error_count == 0:
            insights.append("✅ Zero errors detected - excellent reliability")
        elif error_count < 3:
            insights.append(f"⚠️ {error_count} error patterns found - monitor closely")
        else:
            insights.append(f"🔥 {error_count} error patterns - requires investigation")
            
        insights_text = "\n".join([f"• {insight}" for insight in insights])
        return Panel(insights_text, title="💡 Key Insights & Recommendations", style="blue")
    
    def create_live_progress_monitor(self, total_records: int):
        """Create a live progress monitor for real-time feedback."""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        )
    
    def export_metrics_json(self) -> str:
        """Export detailed metrics to JSON."""
        metrics_path = self.output_dir / f"workflow_metrics_{int(time.time())}.json"
        
        metrics_data = {
            'workflow_start': self.start_time,
            'workflow_end': time.time(),
            'total_duration': time.time() - self.start_time,
            'stages': [asdict(metric) for metric in self.metrics],
            'summary': {
                'total_stages': len(self.metrics),
                'successful_stages': sum(1 for m in self.metrics if m.success),
                'failed_stages': sum(1 for m in self.metrics if not m.success),
                'total_resources_processed': sum(m.resources_processed for m in self.metrics),
                'total_resources_created': sum(m.resources_created for m in self.metrics),
                'avg_throughput': sum(m.throughput_per_sec for m in self.metrics) / len(self.metrics) if self.metrics else 0
            }
        }
        
        with open(metrics_path, 'w') as f:
            json.dump(metrics_data, f, indent=2, default=str)
            
        return str(metrics_path)


def create_sample_visualization():
    """Create a sample visualization to demonstrate capabilities."""
    visualizer = WorkflowVisualizer()
    
    # Simulate workflow stages
    stage_id = visualizer.log_stage_start("Dataset Loading")
    time.sleep(0.1)  # Simulate work
    visualizer.log_stage_end("Dataset Loading", stage_id, True, resources_processed=100)
    
    stage_id = visualizer.log_stage_start("Template Registration") 
    time.sleep(0.05)
    visualizer.log_stage_end("Template Registration", stage_id, True, resources_created=1)
    
    stage_id = visualizer.log_stage_start("Resource Processing")
    time.sleep(0.2)
    visualizer.log_stage_end("Resource Processing", stage_id, True, resources_processed=100, resources_created=25)
    
    # Generate sample report
    sample_data = {
        'report': {
            'summary': {
                'total_records': 100,
                'successful_records': 85,
                'failed_records': 15,
                'success_rate': 0.85
            },
            'resource_analysis': {
                'types_created': ['Patient', 'Observation', 'Condition'],
                'resource_counts': {'Patient': 25, 'Observation': 50, 'Condition': 30},
                'total_resources': 105
            },
            'error_analysis': {
                'unique_error_patterns': 2,
                'error_frequency': {
                    'Validation error in field X': 10,
                    'Database connection timeout': 5
                }
            }
        }
    }
    
    report_path = visualizer.generate_workflow_report(sample_data)
    metrics_path = visualizer.export_metrics_json()
    
    console.print(f"\n🎉 Sample visualization complete!")
    console.print(f"📊 Metrics: {metrics_path}")
    console.print(f"📄 Report: {report_path}")


if __name__ == "__main__":
    console.print("[bold blue]HF Ingestion Workflow Visualizer[/bold blue]")
    console.print("Generating sample visualization...")
    create_sample_visualization()
