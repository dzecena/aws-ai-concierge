"""
AWS AI Concierge CloudWatch Dashboards
Comprehensive monitoring dashboards for system health and performance
"""

import json
import boto3
from typing import Dict, List, Any, Optional

cla
ss CloudWatchDashboardManager:
    """Manages CloudWatch dashboards for AWS AI Concierge monitoring."""
    
    def __init__(self, region: str = 'us-east-1'):
        """Initialize the dashboard manager.
        
        Args:
            region: AWS region for CloudWatch resources
        """
        self.region = region
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
    
    def create_dashboard(self, dashboard_name: str, dashboard_body: Dict[str, Any]) -> bool:
        """Create or update a CloudWatch dashboard.
        
        Args:
            dashboard_name: Name of the dashboard
            dashboard_body: Dashboard configuration as dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.cloudwatch.put_dashboard(
                DashboardName=dashboard_name,
                DashboardBody=json.dumps(dashboard_body)
            )
            return True
        except Exception as e:
            print(f"Error creating dashboard {dashboard_name}: {e}")
            return False
    
    def get_dashboard(self, dashboard_name: str) -> Optional[Dict[str, Any]]:
        """Get dashboard configuration.
        
        Args:
            dashboard_name: Name of the dashboard
            
        Returns:
            Dashboard configuration or None if not found
        """
        try:
            response = self.cloudwatch.get_dashboard(DashboardName=dashboard_name)
            return json.loads(response['DashboardBody'])
        except Exception as e:
            print(f"Error getting dashboard {dashboard_name}: {e}")
            return None
    
    def list_dashboards(self) -> List[str]:
        """List all dashboard names.
        
        Returns:
            List of dashboard names
        """
        try:
            response = self.cloudwatch.list_dashboards()
            return [dashboard['DashboardName'] for dashboard in response['DashboardEntries']]
        except Exception as e:
            print(f"Error listing dashboards: {e}")
            return []
    
    def delete_dashboard(self, dashboard_name: str) -> bool:
        """Delete a dashboard.
        
        Args:
            dashboard_name: Name of the dashboard to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.cloudwatch.delete_dashboards(DashboardNames=[dashboard_name])
            return True
        except Exception as e:
            print(f"Error deleting dashboard {dashboard_name}: {e}")
            return False


def create_ai_concierge_dashboard(environment: str = 'dev') -> Dict[str, Any]:
    """Create dashboard configuration for AWS AI Concierge monitoring.
    
    Args:
        environment: Environment name (dev, staging, prod)
        
    Returns:
        Dashboard configuration dictionary
    """
    lambda_function_name = f"aws-ai-concierge-tools-{environment}"
    
    dashboard_config = {
        "widgets": [
            {
                "type": "metric",
                "x": 0,
                "y": 0,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/Lambda", "Duration", "FunctionName", lambda_function_name],
                        [".", "Errors", ".", "."],
                        [".", "Invocations", ".", "."]
                    ],
                    "period": 300,
                    "stat": "Average",
                    "region": "us-east-1",
                    "title": f"Lambda Function Metrics - {environment}"
                }
            },
            {
                "type": "log",
                "x": 0,
                "y": 6,
                "width": 24,
                "height": 6,
                "properties": {
                    "query": f"SOURCE '/aws/lambda/{lambda_function_name}'\n| fields @timestamp, @message\n| filter @message like /ERROR/\n| sort @timestamp desc\n| limit 20",
                    "region": "us-east-1",
                    "title": f"Recent Errors - {environment}"
                }
            }
        ]
    }
    
    return dashboard_config


if __name__ == "__main__":
    # Example usage
    manager = CloudWatchDashboardManager()
    
    # Create dashboard for dev environment
    dashboard_config = create_ai_concierge_dashboard("dev")
    success = manager.create_dashboard("AWS-AI-Concierge-Dev", dashboard_config)
    
    if success:
        print("Dashboard created successfully!")
    else:
        print("Failed to create dashboard.")