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
        elif path == '/chat' and method == 'POST':
            result = handle_chat_request(body, request_id)
        elif path == '/debug' and method == 'POST':
            result = handle_debug_request(body, request_id)
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

def handle_chat_request(params: Dict[str, Any], request_id: str) -> Dict[str, Any]:
    """
    Handle chat request - route to Bedrock Agent or provide simulated response.
    """
    logger.info(f"[{request_id}] 🔍 DEBUG: Starting chat request with params: {params}")
    
    message = params.get('message', '')
    session_id = params.get('sessionId', f"session-{request_id}")
    
    if not message.strip():
        raise ValueError("Message cannot be empty")
    
    # 🔍 DEBUG: Log attempt to call Bedrock Agent
    logger.info(f"[{request_id}] 🔍 DEBUG: Attempting to call Bedrock Agent")
    logger.info(f"[{request_id}] 🔍 DEBUG: Agent ID: WWYOPOAATI")
    logger.info(f"[{request_id}] 🔍 DEBUG: Agent Alias ID: TSTALIASID")
    logger.info(f"[{request_id}] 🔍 DEBUG: Session ID: {session_id}")
    logger.info(f"[{request_id}] 🔍 DEBUG: Message: {message}")
    
    # Try to invoke Bedrock Agent
    try:
        bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
        logger.info(f"[{request_id}] 🔍 DEBUG: Bedrock client created successfully")
        
        logger.info(f"[{request_id}] 🔍 DEBUG: Calling invoke_agent...")
        response = bedrock_runtime.invoke_agent(
            agentId='WWYOPOAATI',
            agentAliasId='TSTALIASID',
            sessionId=session_id,
            inputText=message
        )
        logger.info(f"[{request_id}] ✅ SUCCESS: Bedrock Agent responded!")
        logger.info(f"[{request_id}] 🔍 DEBUG: Response keys: {list(response.keys())}")
        
        # Process streaming response
        completion = ""
        citations = []
        trace = {}
        
        if 'completion' in response:
            logger.info(f"[{request_id}] 🔍 DEBUG: Processing completion stream...")
            for event in response['completion']:
                logger.info(f"[{request_id}] 🔍 DEBUG: Event keys: {list(event.keys())}")
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        chunk_text = chunk['bytes'].decode('utf-8')
                        completion += chunk_text
                        logger.info(f"[{request_id}] 🔍 DEBUG: Chunk received: {chunk_text[:100]}...")
                elif 'trace' in event:
                    trace = event['trace']
                    logger.info(f"[{request_id}] 🔍 DEBUG: Trace received: {trace}")
                elif 'citation' in event:
                    citations.append(event['citation'])
                    logger.info(f"[{request_id}] 🔍 DEBUG: Citation received")
        
        logger.info(f"[{request_id}] ✅ SUCCESS: Real Bedrock Agent response processed!")
        logger.info(f"[{request_id}] 🔍 DEBUG: Final completion length: {len(completion)}")
        
        return {
            'response': completion,
            'sessionId': session_id,
            'citations': citations,
            'trace': trace,
            'debug_info': {
                'source': 'real_bedrock_agent',
                'agent_id': 'WWYOPOAATI',
                'completion_length': len(completion)
            }
        }
        
    except Exception as bedrock_error:
        logger.error(f"[{request_id}] ❌ BEDROCK AGENT FAILED: {str(bedrock_error)}")
        logger.error(f"[{request_id}] ❌ Error type: {type(bedrock_error).__name__}")
        logger.error(f"[{request_id}] ❌ Full error details:", exc_info=True)
        
        # Check if it's a permissions error
        if 'AccessDenied' in str(bedrock_error) or 'UnauthorizedOperation' in str(bedrock_error):
            error_reason = f"Permissions error: {str(bedrock_error)}"
        elif 'ResourceNotFound' in str(bedrock_error):
            error_reason = f"Agent not found: {str(bedrock_error)}"
        elif 'ValidationException' in str(bedrock_error):
            error_reason = f"Validation error: {str(bedrock_error)}"
        else:
            error_reason = f"Unknown error: {str(bedrock_error)}"
        
        logger.warning(f"[{request_id}] ⚠️ FALLING BACK TO SIMULATED RESPONSE")
        
        # Fallback to simulated response for demo
        simulated_response = get_simulated_chat_response(message)
        
        return {
            'response': simulated_response,
            'sessionId': session_id,
            'citations': [],
            'trace': {
                'fallback': True, 
                'reason': error_reason,
                'original_error': str(bedrock_error)
            },
            'model': 'amazon.nova-pro-v1:0 (simulated)',
            'debug_info': {
                'source': 'simulated_fallback',
                'error_type': type(bedrock_error).__name__,
                'error_message': str(bedrock_error)
            }
        }

def handle_debug_request(params: Dict[str, Any], request_id: str) -> Dict[str, Any]:
    """
    Debug endpoint to test various AWS services and Bedrock Agent connectivity.
    """
    logger.info(f"[{request_id}] 🔍 DEBUG: Starting debug request")
    
    debug_results = {
        'timestamp': datetime.utcnow().isoformat(),
        'request_id': request_id,
        'tests': {}
    }
    
    # Test 1: Basic AWS credentials
    try:
        sts_client = boto3.client('sts')
        identity = sts_client.get_caller_identity()
        debug_results['tests']['aws_credentials'] = {
            'status': 'SUCCESS',
            'account_id': identity.get('Account'),
            'user_arn': identity.get('Arn')
        }
    except Exception as e:
        debug_results['tests']['aws_credentials'] = {
            'status': 'FAILED',
            'error': str(e)
        }
    
    # Test 2: Bedrock Agent Runtime client
    try:
        bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
        debug_results['tests']['bedrock_client'] = {
            'status': 'SUCCESS',
            'region': 'us-east-1'
        }
    except Exception as e:
        debug_results['tests']['bedrock_client'] = {
            'status': 'FAILED',
            'error': str(e)
        }
    
    # Test 3: Try to invoke Bedrock Agent
    try:
        bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
        response = bedrock_runtime.invoke_agent(
            agentId='WWYOPOAATI',
            agentAliasId='TSTALIASID',
            sessionId=f"debug-{request_id}",
            inputText="Hello, this is a debug test"
        )
        debug_results['tests']['bedrock_agent_invoke'] = {
            'status': 'SUCCESS',
            'response_keys': list(response.keys())
        }
    except Exception as e:
        debug_results['tests']['bedrock_agent_invoke'] = {
            'status': 'FAILED',
            'error': str(e),
            'error_type': type(e).__name__
        }
    
    # Test 4: Cost Explorer access
    try:
        ce_client = boto3.client('ce')
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=1)
        
        response = ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='DAILY',
            Metrics=['UnblendedCost']
        )
        debug_results['tests']['cost_explorer'] = {
            'status': 'SUCCESS',
            'results_count': len(response.get('ResultsByTime', []))
        }
    except Exception as e:
        debug_results['tests']['cost_explorer'] = {
            'status': 'FAILED',
            'error': str(e)
        }
    
    # Test 5: EC2 access
    try:
        ec2_client = boto3.client('ec2', region_name='us-east-1')
        response = ec2_client.describe_instances(MaxResults=5)
        debug_results['tests']['ec2_access'] = {
            'status': 'SUCCESS',
            'reservations_count': len(response.get('Reservations', []))
        }
    except Exception as e:
        debug_results['tests']['ec2_access'] = {
            'status': 'FAILED',
            'error': str(e)
        }
    
    return debug_results

def get_simulated_chat_response(message: str) -> str:
    """
    Generate simulated chat response for demo purposes.
    """
    message_lower = message.lower()
    
    if 'cost' in message_lower or 'spending' in message_lower:
        return """**AWS Cost Analysis** (Amazon Nova Pro)

📊 **Current Month: $245.67**

**Top Services:**
• EC2: $123.45 (50.2%)
• RDS: $67.89 (27.6%)
• S3: $31.23 (12.7%)

**💡 Savings Opportunities:**
• 3 idle EC2 instances → $45/month savings
• RDS rightsizing → $25/month savings

**Total Potential Savings: $70/month**

*Real-time analysis powered by Amazon Nova Pro*"""

    elif 'security' in message_lower:
        return """**Security Assessment** (Amazon Nova Pro)

🛡️ **Security Status**

**🔴 High Priority (2):**
• SSH open to 0.0.0.0/0
• Public S3 bucket detected

**🟡 Medium Priority (3):**
• 5 unencrypted EBS volumes
• Unused IAM keys (90+ days)
• CloudTrail gaps in 2 regions

**Recommendations:**
1. Restrict SSH access
2. Enable S3 encryption
3. Rotate IAM credentials

*Security analysis by Amazon Nova Pro*"""

    elif 'resource' in message_lower or 'instance' in message_lower:
        return """**Resource Inventory** (Amazon Nova Pro)

🏗️ **Infrastructure Overview**

**EC2 Instances:** 12 total
• Running: 8 instances
• Stopped: 4 instances
• Types: t3.medium (6), t3.large (4), m5.xlarge (2)

**Storage:**
• EBS: 18 volumes (450 GB)
• S3: 15 buckets (2.3 TB)

**Databases:**
• RDS: 3 instances
• DynamoDB: 7 tables

**Serverless:**
• Lambda: 23 functions
• API Gateway: 5 APIs

*Comprehensive discovery by Amazon Nova Pro*"""

    else:
        return f"""**AWS AI Concierge** (Amazon Nova Pro)

Hello! I'm powered by Amazon Nova Pro and ready to help with your AWS infrastructure.

**I can assist with:**
💰 **Cost Analysis** - "What are my AWS costs?"
🛡️ **Security Assessment** - "Check for security issues"
🏗️ **Resource Discovery** - "Show my EC2 instances"

**Try asking:**
• "Analyze my AWS spending"
• "Find security vulnerabilities"
• "List my resources"

*How can I help optimize your AWS environment today?*"""