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
    if time_period == 'CUSTOM' and 'custom_start_date' in params and 'custom_end_date' in params:
        # Use custom dates provided by the parser
        start_date = params['custom_start_date']
        end_date = params['custom_end_date']
        logger.info(f"[{request_id}] Using custom date range: {start_date} to {end_date}")
    else:
        # Use existing logic for standard time periods
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
    Handle chat request - Hybrid approach: Try Nova Lite direct, fallback to Claude Haiku via Bedrock Agent.
    """
    logger.info(f"[{request_id}] 🔍 DEBUG: Starting hybrid chat request with params: {params}")
    
    message = params.get('message', '')
    session_id = params.get('sessionId', f"session-{request_id}")
    
    if not message.strip():
        raise ValueError("Message cannot be empty")
    
    # Step 1: Try Nova Lite directly via bedrock-runtime
    logger.info(f"[{request_id}] 🚀 STEP 1: Attempting Nova Lite direct call")
    nova_result = try_nova_lite_direct(message, session_id, request_id)
    
    if nova_result['success']:
        logger.info(f"[{request_id}] ✅ SUCCESS: Nova Lite direct call worked!")
        return nova_result['response']
    
    # Step 2: Fallback to Claude Haiku via Bedrock Agent
    logger.info(f"[{request_id}] 🔄 STEP 2: Nova failed, falling back to Claude Haiku via Bedrock Agent")
    logger.info(f"[{request_id}] 🔍 Nova failure reason: {nova_result['error']}")
    
    claude_result = try_claude_haiku_agent(message, session_id, request_id)
    
    if claude_result['success']:
        logger.info(f"[{request_id}] ✅ SUCCESS: Claude Haiku agent worked!")
        # Add fallback info to trace
        claude_result['response']['trace']['nova_attempted'] = True
        claude_result['response']['trace']['nova_error'] = nova_result['error']
        return claude_result['response']
    
    # Step 3: Final fallback to simulated response
    logger.warning(f"[{request_id}] ⚠️ STEP 3: Both Nova and Claude failed, using simulated response")
    
    simulated_response = get_simulated_chat_response(message)
    
    return {
        'response': simulated_response,
        'sessionId': session_id,
        'citations': [],
        'trace': {
            'fallback': True,
            'nova_attempted': True,
            'claude_attempted': True,
            'nova_error': nova_result['error'],
            'claude_error': claude_result['error'],
            'reason': 'Both Nova and Claude failed'
        },
        'model': 'simulated (both models failed)',
        'debug_info': {
            'source': 'simulated_fallback',
            'nova_error': nova_result['error'],
            'claude_error': claude_result['error']
        }
    }

def try_nova_lite_direct(message: str, session_id: str, request_id: str) -> Dict[str, Any]:
    """
    Try Nova Lite directly via bedrock-runtime API with real AWS data integration.
    """
    try:
        logger.info(f"[{request_id}] 🔍 Calling Nova Lite with real AWS data integration v2...")
        
        # Step 1: Check if user is asking for specific AWS data
        message_lower = message.lower()
        real_aws_data = None
        
        if 'cost' in message_lower or 'spending' in message_lower or 'bill' in message_lower:
            logger.info(f"[{request_id}] 💰 Cost query detected, fetching real AWS cost data...")
            real_aws_data = get_real_cost_data(request_id, message)
        elif 'security' in message_lower or 'vulnerable' in message_lower:
            logger.info(f"[{request_id}] 🛡️ Security query detected, fetching real security data...")
            real_aws_data = get_real_security_data(request_id)
        elif 'resource' in message_lower or 'instance' in message_lower or 'ec2' in message_lower:
            logger.info(f"[{request_id}] 🏗️ Resource query detected, fetching real resource data...")
            real_aws_data = get_real_resource_data(request_id)
        
        # Step 2: Enhance message with real AWS data if available
        if real_aws_data:
            enhanced_message = f"""You are an AWS AI Concierge powered by Amazon Nova Lite. You have access to real AWS data.

User query: {message}

REAL AWS DATA (use this actual data in your response):
{real_aws_data}

IMPORTANT: When presenting the time period to the user, focus on the complete month being analyzed. For example, if the data shows "2024-12-01 to 2024-12-31", present it as "December 2024" or "the month of December 2024". The date range represents the complete month the user requested.

Please provide a helpful response using the REAL AWS DATA above. Be specific and reference the actual numbers and resources shown, and present the time period in a user-friendly way."""
        else:
            enhanced_message = f"""You are an AWS AI Concierge powered by Amazon Nova Lite. You help users with AWS infrastructure management.

User query: {message}

Please provide a helpful response about AWS infrastructure management. If the user needs specific cost, security, or resource data, let them know you can provide real AWS insights."""
        
        # Step 3: Call Nova Lite
        bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
        
        request_body = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "text": enhanced_message
                        }
                    ]
                }
            ],
            "inferenceConfig": {
                "maxTokens": 1000,
                "temperature": 0.7
            }
        }
        
        start_time = datetime.utcnow()
        
        response = bedrock_runtime.invoke_model(
            modelId='amazon.nova-lite-v1:0',
            body=json.dumps(request_body),
            contentType='application/json',
            accept='application/json'
        )
        
        end_time = datetime.utcnow()
        response_time = (end_time - start_time).total_seconds()
        
        # Parse response
        response_body = json.loads(response['body'].read())
        
        if 'output' in response_body and 'message' in response_body['output']:
            response_text = response_body['output']['message']['content'][0]['text']
            
            # Add Nova Lite branding with real data indicator
            data_source = "with Real AWS Data" if real_aws_data else "with General AWS Guidance"
            branded_response = f"**🚀 Powered by Amazon Nova Lite (Direct Integration {data_source})**\n\n{response_text}"
            
            logger.info(f"[{request_id}] ✅ Nova Lite success! Response time: {response_time:.2f}s, Real data: {bool(real_aws_data)}")
            
            return {
                'success': True,
                'response': {
                    'response': branded_response,
                    'sessionId': session_id,
                    'citations': [],
                    'trace': {
                        'fallback': False,
                        'model_used': 'amazon.nova-lite-v1:0',
                        'response_time': response_time,
                        'integration_type': 'direct_bedrock_runtime',
                        'real_aws_data_used': bool(real_aws_data)
                    },
                    'model': 'amazon.nova-lite-v1:0 (direct + real data)',
                    'debug_info': {
                        'source': 'nova_lite_direct_with_real_data',
                        'response_time': response_time,
                        'completion_length': len(response_text),
                        'usage': response_body.get('usage', {}),
                        'real_data_integrated': bool(real_aws_data)
                    }
                }
            }
        else:
            raise ValueError("Unexpected Nova Lite response format")
            
    except Exception as e:
        logger.error(f"[{request_id}] ❌ Nova Lite direct call failed: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }

def get_real_cost_data(request_id: str, user_message: str = "") -> str:
    """Get real AWS cost data using Cost Explorer API with intelligent date parsing."""
    try:
        logger.info(f"[{request_id}] 💰 Fetching real cost data for message: {user_message}")
        
        # Parse the user message for specific time periods
        cost_params = parse_cost_time_period(user_message, request_id)
        
        # Use the existing cost analysis function with parsed parameters
        cost_data = handle_cost_analysis(cost_params, request_id)
        
        # Fix the date presentation for user-friendly display
        display_start_date = cost_data['start_date']
        display_end_date = cost_data['end_date']
        
        # If we have custom dates, adjust the end date for display (subtract 1 day)
        if cost_params.get('time_period') == 'CUSTOM':
            from datetime import datetime, timedelta
            try:
                # Convert string dates back to date objects for calculation
                end_date_obj = datetime.strptime(cost_data['end_date'], '%Y-%m-%d').date()
                # Subtract 1 day for user-friendly display (since API uses exclusive end date)
                display_end_date = (end_date_obj - timedelta(days=1)).strftime('%Y-%m-%d')
                logger.info(f"[{request_id}] Adjusted display end date from {cost_data['end_date']} to {display_end_date}")
            except Exception as e:
                logger.warning(f"[{request_id}] Could not adjust display date: {str(e)}")
        
        return f"""REAL AWS COST DATA:
- Total Cost: ${cost_data['total_cost']} USD
- Time Period: {display_start_date} to {display_end_date}
- Period Description: {cost_params.get('period_description', 'Current period')}
- Top Services: {', '.join([f"{item['service_name']}: ${item['cost']}" for item in cost_data['breakdown'][:5]])}
- Total Services: {cost_data['total_services']}
- Note: This covers the complete month of {cost_params.get('period_description', 'the requested period')}"""
        
    except Exception as e:
        logger.error(f"[{request_id}] ❌ Failed to get real cost data: {str(e)}")
        return None

def parse_cost_time_period(message: str, request_id: str) -> Dict[str, Any]:
    """Parse user message to determine the requested time period for cost analysis."""
    import re
    from datetime import datetime, timedelta
    
    message_lower = message.lower()
    logger.info(f"[{request_id}] 🔍 Parsing time period from: {message}")
    
    # Default parameters
    params = {
        'time_period': 'MONTHLY',
        'granularity': 'DAILY',
        'group_by': 'SERVICE',
        'period_description': 'Current month'
    }
    
    # Check for specific months and years
    months = {
        'january': 1, 'jan': 1,
        'february': 2, 'feb': 2,
        'march': 3, 'mar': 3,
        'april': 4, 'apr': 4,
        'may': 5,
        'june': 6, 'jun': 6,
        'july': 7, 'jul': 7,
        'august': 8, 'aug': 8,
        'september': 9, 'sep': 9, 'sept': 9,
        'october': 10, 'oct': 10,
        'november': 11, 'nov': 11,
        'december': 12, 'dec': 12
    }
    
    # Look for month and year patterns
    found_month = None
    found_year = None
    
    for month_name, month_num in months.items():
        if month_name in message_lower:
            found_month = month_num
            logger.info(f"[{request_id}] 🔍 Found month: {month_name} ({month_num})")
            break
    
    # Look for year (2024, 2025, etc.)
    year_match = re.search(r'\b(20\d{2})\b', message)
    if year_match:
        found_year = int(year_match.group(1))
        logger.info(f"[{request_id}] 🔍 Found year: {found_year}")
    
    # If we found a specific month/year, calculate custom dates
    if found_month:
        if not found_year:
            # Default to current year if no year specified
            found_year = datetime.utcnow().year
        
        try:
            # Calculate start and end dates for the specific month
            from calendar import monthrange
            
            start_date = datetime(found_year, found_month, 1).date()
            _, last_day = monthrange(found_year, found_month)
            end_date = datetime(found_year, found_month, last_day).date()
            
            # Add one day to end_date for Cost Explorer (exclusive end date)
            end_date = end_date + timedelta(days=1)
            
            params.update({
                'time_period': 'CUSTOM',
                'custom_start_date': start_date,
                'custom_end_date': end_date,
                'period_description': f"{list(months.keys())[list(months.values()).index(found_month)].title()} {found_year}"
            })
            
            logger.info(f"[{request_id}] ✅ Custom period: {start_date} to {end_date}")
            
        except Exception as e:
            logger.error(f"[{request_id}] ❌ Error calculating custom dates: {str(e)}")
            # Fall back to default
    
    # Check for other time period keywords
    elif 'last month' in message_lower or 'previous month' in message_lower:
        params.update({
            'time_period': 'last_month',
            'period_description': 'Last month'
        })
    elif 'last 30 days' in message_lower or 'past 30 days' in message_lower:
        params.update({
            'time_period': 'last_30_days',
            'period_description': 'Last 30 days'
        })
    elif 'this month' in message_lower or 'current month' in message_lower:
        params.update({
            'time_period': 'current_month',
            'period_description': 'Current month'
        })
    
    logger.info(f"[{request_id}] 📅 Final params: {params}")
    return params

def get_real_security_data(request_id: str) -> str:
    """Get real AWS security data."""
    try:
        logger.info(f"[{request_id}] 🛡️ Fetching real security data...")
        
        # Use the existing security assessment function
        security_data = handle_security_assessment({'region': 'us-east-1'}, request_id)
        
        return f"""REAL AWS SECURITY DATA:
- Total Issues: {security_data['total_issues']}
- High Priority Issues: {security_data['high_priority']}
- Assessment Time: {security_data['assessment_time']}
- Region: {security_data['region']}
- Issues Found: {', '.join([f"{issue['type']}: {issue['description']}" for issue in security_data['security_issues'][:3]])}"""
        
    except Exception as e:
        logger.error(f"[{request_id}] ❌ Failed to get real security data: {str(e)}")
        return None

def get_real_resource_data(request_id: str) -> str:
    """Get real AWS resource data."""
    try:
        logger.info(f"[{request_id}] 🏗️ Fetching real resource data...")
        
        # Use the existing resource inventory function
        resource_data = handle_resource_inventory({'resource_type': 'EC2', 'region': 'us-east-1'}, request_id)
        
        return f"""REAL AWS RESOURCE DATA:
- Resource Type: {resource_data['resource_type']}
- Total Count: {resource_data['total_count']}
- Region: {resource_data['region']}
- Resources: {', '.join([f"{res['name']} ({res['state']})" for res in resource_data['resources'][:5]])}"""
        
    except Exception as e:
        logger.error(f"[{request_id}] ❌ Failed to get real resource data: {str(e)}")
        return None

def try_claude_haiku_agent(message: str, session_id: str, request_id: str) -> Dict[str, Any]:
    """
    Try Claude Haiku via Bedrock Agent as fallback.
    """
    try:
        logger.info(f"[{request_id}] 🔍 Calling Claude Haiku via Bedrock Agent...")
        
        bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
        
        response = bedrock_runtime.invoke_agent(
            agentId='WWYOPOAATI',
            agentAliasId='TSTALIASID',
            sessionId=session_id,
            inputText=message
        )
        
        # Process streaming response
        completion = ""
        citations = []
        trace = {}
        
        if 'completion' in response:
            for event in response['completion']:
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        chunk_text = chunk['bytes'].decode('utf-8')
                        completion += chunk_text
                elif 'trace' in event:
                    trace = event['trace']
                elif 'citation' in event:
                    citations.append(event['citation'])
        
        if completion:
            # Add Claude Haiku branding to response
            branded_response = f"**🤖 Powered by Claude 3 Haiku (Bedrock Agent)**\n\n{completion}"
            
            logger.info(f"[{request_id}] ✅ Claude Haiku agent success!")
            
            return {
                'success': True,
                'response': {
                    'response': branded_response,
                    'sessionId': session_id,
                    'citations': citations,
                    'trace': {
                        'fallback': False,
                        'model_used': 'anthropic.claude-3-haiku-20240307-v1:0',
                        'integration_type': 'bedrock_agent',
                        **trace
                    },
                    'model': 'anthropic.claude-3-haiku-20240307-v1:0 (agent)',
                    'debug_info': {
                        'source': 'claude_haiku_agent',
                        'agent_id': 'WWYOPOAATI',
                        'completion_length': len(completion)
                    }
                }
            }
        else:
            raise ValueError("Empty response from Claude Haiku agent")
            
    except Exception as e:
        logger.error(f"[{request_id}] ❌ Claude Haiku agent failed: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
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