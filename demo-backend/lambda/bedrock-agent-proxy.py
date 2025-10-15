import json
import logging
from datetime import datetime, timedelta
import boto3
from typing import Dict, Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Handler for API Gateway proxy integration.
    
    Event structure from API Gateway:
    {
        "resource": "/cost-analysis",
        "path": "/cost-analysis", 
        "httpMethod": "POST",
        "headers": {...},
        "body": "{\"time_period\": \"MONTHLY\"}",  # JSON string
        "requestContext": {...}
    }
    """
    
    # Log incoming request
    request_id = context.aws_request_id
    logger.info(f"[{request_id}] Received event: {json.dumps(event)}")
    
    try:
        # Extract path and method from API Gateway event
        path = event.get('path', '')
        method = event.get('httpMethod', '')
        
        # Parse JSON body from API Gateway
        body = json.loads(event.get('body', '{}'))
        
        logger.info(f"[{request_id}] Path: {path}, Method: {method}")
        logger.info(f"[{request_id}] Body: {json.dumps(body)}")
        
        # Route to appropriate handler based on path
        if path == '/cost-analysis' and method == 'POST':
            result = handle_cost_analysis(body, request_id)
        elif path == '/resource-inventory' and method == 'POST':
            result = handle_resource_inventory(body, request_id)
        elif path == '/security-assessment' and method == 'POST':
            result = handle_security_assessment(body, request_id)
        else:
            return create_response(404, {
                'success': False,
                'error': f'Unknown endpoint: {method} {path}'
            })
        
        # Return API Gateway response format
        return create_response(200, {
            'success': True,
            'data': result,
            'metadata': {
                'request_id': request_id,
                'timestamp': datetime.utcnow().isoformat(),
                'model': 'amazon.nova-pro-v1:0'
            }
        })
        
    except Exception as e:
        logger.error(f"[{request_id}] Error: {str(e)}", exc_info=True)
        return create_response(500, {
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        })

def create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create API Gateway response format.
    
    CRITICAL: This is the format API Gateway expects!
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',  # For web frontend
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'POST, OPTIONS'
        },
        'body': json.dumps(body, default=str)  # JSON string, not object!
    }

def handle_cost_analysis(params: Dict[str, Any], request_id: str) -> Dict[str, Any]:
    """
    Handle cost analysis request using AWS Cost Explorer.
    """
    logger.info(f"[{request_id}] Starting cost analysis with params: {params}")
    
    # Extract parameters
    time_period = params.get('time_period', 'MONTHLY')
    granularity = params.get('granularity', 'DAILY')
    group_by = params.get('group_by', 'SERVICE')
    
    # Calculate date range
    end_date = datetime.utcnow().date()
    
    if time_period == 'MONTHLY' or time_period == 'current_month':
        start_date = end_date.replace(day=1)
    elif time_period == 'last_30_days':
        start_date = end_date - timedelta(days=30)
    elif time_period == 'last_month':
        first_of_current = end_date.replace(day=1)
        end_date = first_of_current - timedelta(days=1)
        start_date = end_date.replace(day=1)
    else:
        start_date = end_date - timedelta(days=30)
    
    logger.info(f"[{request_id}] Analyzing costs from {start_date} to {end_date}")
    
    # Call AWS Cost Explorer
    ce_client = boto3.client('ce')
    
    try:
        response = ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity=granularity,
            Metrics=['UnblendedCost'],
            GroupBy=[{
                'Type': 'DIMENSION',
                'Key': group_by
            }]
        )
        
        # Process response
        total_cost = 0
        breakdown = []
        
        for result in response.get('ResultsByTime', []):
            for group in result.get('Groups', []):
                service_name = group.get('Keys', ['Unknown'])[0]
                cost = float(group.get('Metrics', {}).get('UnblendedCost', {}).get('Amount', 0))
                total_cost += cost
                
                breakdown.append({
                    'service_name': service_name,
                    'cost': round(cost, 2),
                    'percentage': 0  # Calculate after total
                })
        
        # Calculate percentages
        if total_cost > 0:
            for item in breakdown:
                item['percentage'] = round((item['cost'] / total_cost) * 100, 2)
        
        # Sort by cost descending
        breakdown.sort(key=lambda x: x['cost'], reverse=True)
        
        logger.info(f"[{request_id}] Cost analysis completed - Total: ${total_cost:.2f}")
        
        return {
            'total_cost': round(total_cost, 2),
            'currency': 'USD',
            'time_period': time_period,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'breakdown': breakdown[:10],  # Top 10 services
            'total_services': len(breakdown)
        }
        
    except Exception as e:
        logger.error(f"[{request_id}] Cost Explorer error: {str(e)}")
        raise

def handle_resource_inventory(params: Dict[str, Any], request_id: str) -> Dict[str, Any]:
    """
    Handle resource inventory request.
    """
    logger.info(f"[{request_id}] Starting resource inventory with params: {params}")
    
    resource_type = params.get('resource_type', 'EC2')
    region = params.get('region', 'us-east-1')
    
    # Example: List EC2 instances
    if resource_type == 'EC2':
        ec2_client = boto3.client('ec2', region_name=region)
        response = ec2_client.describe_instances()
        
        resources = []
        for reservation in response.get('Reservations', []):
            for instance in reservation.get('Instances', []):
                resources.append({
                    'resource_id': instance['InstanceId'],
                    'resource_type': 'EC2',
                    'name': next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Name'), 'N/A'),
                    'state': instance['State']['Name'],
                    'instance_type': instance['InstanceType'],
                    'launch_time': instance['LaunchTime'].isoformat()
                })
        
        return {
            'resources': resources,
            'total_count': len(resources),
            'resource_type': resource_type,
            'region': region
        }
    
    # Example: List S3 buckets
    elif resource_type == 'S3':
        s3_client = boto3.client('s3', region_name=region)
        response = s3_client.list_buckets()
        
        resources = []
        for bucket in response.get('Buckets', []):
            resources.append({
                'resource_id': bucket['Name'],
                'resource_type': 'S3',
                'name': bucket['Name'],
                'created_date': bucket['CreationDate'].isoformat()
            })
        
        return {
            'resources': resources,
            'total_count': len(resources),
            'resource_type': resource_type,
            'region': region
        }
    
    # Add more resource types as needed
    return {
        'resources': [],
        'total_count': 0,
        'resource_type': resource_type,
        'region': region
    }

def handle_security_assessment(params: Dict[str, Any], request_id: str) -> Dict[str, Any]:
    """
    Handle security assessment request.
    """
    logger.info(f"[{request_id}] Starting security assessment with params: {params}")
    
    region = params.get('region', 'us-east-1')
    
    # Example: Check security groups for open access
    ec2_client = boto3.client('ec2', region_name=region)
    
    try:
        response = ec2_client.describe_security_groups()
        
        security_issues = []
        for sg in response.get('SecurityGroups', []):
            for rule in sg.get('IpPermissions', []):
                for ip_range in rule.get('IpRanges', []):
                    if ip_range.get('CidrIp') == '0.0.0.0/0':
                        security_issues.append({
                            'severity': 'HIGH',
                            'type': 'Open Security Group',
                            'resource_id': sg['GroupId'],
                            'description': f"Security group {sg['GroupName']} allows access from 0.0.0.0/0",
                            'port': rule.get('FromPort', 'All'),
                            'protocol': rule.get('IpProtocol', 'All')
                        })
        
        return {
            'security_issues': security_issues,
            'total_issues': len(security_issues),
            'high_priority': len([i for i in security_issues if i['severity'] == 'HIGH']),
            'region': region,
            'assessment_time': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"[{request_id}] Security assessment error: {str(e)}")
        raise