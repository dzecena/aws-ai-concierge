"""
AWS AI Concierge Lambda Function
Main handler for Bedrock Agent action group tools
"""

import json
import logging
import os
import time
from typing import Dict, Any, Optional
from datetime import datetime

from utils.error_handler import ErrorHandler
from utils.response_formatter import ResponseFormatter
from utils.aws_clients import AWSClientManager
from utils.audit_logger import AuditLogger
from tools.cost_analysis import CostAnalysisHandler
from tools.resource_discovery import ResourceDiscoveryHandler
from tools.security_assessment import SecurityAssessmentHandler

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))

# Initialize components
error_handler = ErrorHandler()
response_formatter = ResponseFormatter()
aws_clients = AWSClientManager()
audit_logger = AuditLogger()

# Initialize tool handlers
cost_handler = CostAnalysisHandler(aws_clients)
resource_handler = ResourceDiscoveryHandler(aws_clients)
security_handler = SecurityAssessmentHandler(aws_clients)

# Route mapping for different actions
TOOL_ROUTES = {
    'getCostAnalysis': cost_handler.get_cost_analysis,
    'getIdleResources': cost_handler.get_idle_resources,
    'getResourceInventory': resource_handler.get_resource_inventory,
    'getResourceDetails': resource_handler.get_resource_details,
    'getResourceHealth': resource_handler.get_resource_health_status,
    'getSecurityAssessment': security_handler.get_security_assessment,
    'checkEncryptionStatus': security_handler.check_encryption_status,
}


def handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Main Lambda handler for AWS AI Concierge tools.
    Supports both Bedrock Agent events and API Gateway events.
    
    Args:
        event: Lambda event containing the action and parameters
        context: Lambda context object
        
    Returns:
        Formatted response for Bedrock Agent or API Gateway
    """
    request_id = context.aws_request_id
    start_time = time.time()
    
    logger.info(f"[{request_id}] Processing request: {json.dumps(event, default=str)}")
    
    # DEBUG: Log the exact event structure for Bedrock Agent debugging
    if 'actionGroup' in event:
        logger.info(f"[{request_id}] DEBUG - Bedrock Agent Event Structure:")
        logger.info(f"[{request_id}] DEBUG - actionGroup: {event.get('actionGroup')}")
        logger.info(f"[{request_id}] DEBUG - apiPath: {event.get('apiPath')}")
        logger.info(f"[{request_id}] DEBUG - httpMethod: {event.get('httpMethod')}")
        logger.info(f"[{request_id}] DEBUG - function: {event.get('function')}")
        logger.info(f"[{request_id}] DEBUG - parameters: {event.get('parameters')}")
    
    try:
        # Detect event source (Bedrock Agent vs API Gateway)
        if 'actionGroup' in event:
            # Bedrock Agent event
            action = event.get('actionGroup', '')
            api_path = event.get('apiPath') if 'apiPath' in event else None
            http_method = event.get('httpMethod', 'POST')
            parameters = event.get('parameters', [])
            
            # Convert parameters list to dict for easier handling
            params_dict = {}
            if isinstance(parameters, list):
                for param in parameters:
                    if isinstance(param, dict) and 'name' in param and 'value' in param:
                        params_dict[param['name']] = param['value']
            elif isinstance(parameters, dict):
                params_dict = parameters
                
            logger.info(f"[{request_id}] Bedrock Agent - Action: {action}, API Path: {api_path}, Method: {http_method}")
            
            # Determine the operation - for Bedrock Agent, use the function name directly
            if 'function' in event and event['function']:
                operation = event['function']
            else:
                # Fallback to API path extraction for API Gateway calls
                operation = _extract_operation_from_path(api_path)
            
            # Log request received
            audit_logger.log_request_received(
                request_id=request_id,
                event_source='bedrock_agent',
                operation=operation,
                parameters=params_dict,
                user_context={'action_group': action, 'api_path': api_path}
            )
            
            if operation not in TOOL_ROUTES:
                raise ValueError(f"Unknown operation: {operation}")
                
            # Execute the appropriate tool handler with timing
            tool_start_time = time.time()
            tool_function = TOOL_ROUTES[operation]
            result = tool_function(params_dict, request_id)
            tool_execution_time = (time.time() - tool_start_time) * 1000
            
            # Log tool invocation
            audit_logger.log_tool_invocation(
                request_id=request_id,
                tool_name=operation,
                parameters=params_dict,
                execution_time_ms=tool_execution_time,
                success=True
            )
            
            # Format successful response for Bedrock Agent
            response = response_formatter.format_success_response(
                result, 
                operation, 
                request_id,
                api_path  # Pass the original API path from the request
            )
            
        elif 'httpMethod' in event or 'requestContext' in event:
            # API Gateway event
            path = event.get('path', '')
            http_method = event.get('httpMethod', 'POST')
            body = event.get('body', '{}')
            
            # Parse request body
            if isinstance(body, str):
                params_dict = json.loads(body) if body else {}
            else:
                params_dict = body or {}
                
            logger.info(f"[{request_id}] API Gateway - Path: {path}, Method: {http_method}")
            
            # Determine the operation based on path
            operation = _extract_operation_from_path(path)
            
            # Log request received
            audit_logger.log_request_received(
                request_id=request_id,
                event_source='api_gateway',
                operation=operation,
                parameters=params_dict,
                user_context={'path': path, 'method': http_method}
            )
            
            if operation not in TOOL_ROUTES:
                raise ValueError(f"Unknown operation: {operation}")
                
            # Execute the appropriate tool handler with timing
            tool_start_time = time.time()
            tool_function = TOOL_ROUTES[operation]
            result = tool_function(params_dict, request_id)
            tool_execution_time = (time.time() - tool_start_time) * 1000
            
            # Log tool invocation
            audit_logger.log_tool_invocation(
                request_id=request_id,
                tool_name=operation,
                parameters=params_dict,
                execution_time_ms=tool_execution_time,
                success=True
            )
            
            # Format successful response for API Gateway
            response_body = {
                'success': True,
                'operation': operation,
                'data': result,
                'metadata': {
                    'request_id': request_id,
                    'timestamp': datetime.utcnow().isoformat(),
                    'version': '1.0'
                }
            }
            
            response = {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type, X-Amz-Date, Authorization, X-Api-Key'
                },
                'body': json.dumps(response_body)
            }
            
        else:
            # Legacy/direct invocation
            action = event.get('action', 'unknown')
            response = {
                'statusCode': 200,
                'body': {
                    'message': f'AWS AI Concierge received action: {action}',
                    'timestamp': request_id,
                    'function_version': context.function_version
                }
            }
        
        # Log successful response
        processing_time = (time.time() - start_time) * 1000
        response_size = len(json.dumps(response, default=str).encode('utf-8'))
        
        audit_logger.log_response_sent(
            request_id=request_id,
            operation=operation if 'operation' in locals() else 'unknown',
            response_size_bytes=response_size,
            processing_time_ms=processing_time,
            success=True
        )
        
        logger.info(f"[{request_id}] Successfully processed request in {processing_time:.2f}ms")
        return response
        
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        logger.error(f"[{request_id}] Error processing request: {str(e)}", exc_info=True)
        
        # Format error response
        error_response = error_handler.handle_error(e, request_id)
        
        # Log error occurred
        operation = locals().get('operation', 'unknown')
        audit_logger.log_error_occurred(
            request_id=request_id,
            error_type=type(e).__name__,
            error_code=getattr(e, 'response', {}).get('Error', {}).get('Code'),
            operation=operation,
            severity=error_response.get('severity', 'error'),
            user_impact=error_response.get('user_message', str(e))
        )
        
        # Log failed tool invocation if we got that far
        if 'tool_start_time' in locals():
            tool_execution_time = (time.time() - tool_start_time) * 1000
            audit_logger.log_tool_invocation(
                request_id=request_id,
                tool_name=operation,
                parameters=locals().get('params_dict', {}),
                execution_time_ms=tool_execution_time,
                success=False
            )
        
        # Check if this is an API Gateway request for proper error formatting
        if 'httpMethod' in event or 'requestContext' in event:
            error_body = {
                'success': False,
                'error': error_response,
                'metadata': {
                    'request_id': request_id,
                    'timestamp': datetime.utcnow().isoformat(),
                    'version': '1.0'
                }
            }
            
            response = {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(error_body)
            }
            
            # Log error response
            response_size = len(json.dumps(response).encode('utf-8'))
            audit_logger.log_response_sent(
                request_id=request_id,
                operation=operation,
                response_size_bytes=response_size,
                processing_time_ms=processing_time,
                success=False
            )
            
            return response
        else:
            response = response_formatter.format_error_response(
                error_response, 
                request_id, 
                locals().get('api_path', ''),
                locals().get('operation')
            )
            
            # Log error response
            response_size = len(json.dumps(response, default=str).encode('utf-8'))
            audit_logger.log_response_sent(
                request_id=request_id,
                operation=operation,
                response_size_bytes=response_size,
                processing_time_ms=processing_time,
                success=False
            )
            
            return response


def _extract_operation_from_path(api_path: str) -> str:
    """
    Extract operation name from API path.
    
    Args:
        api_path: The API path from the event
        
    Returns:
        Operation name for routing
    """
    # Map API paths to operation names
    path_mapping = {
        '/cost-analysis': 'getCostAnalysis',
        '/idle-resources': 'getIdleResources',
        '/resource-inventory': 'getResourceInventory',
        '/resource-details': 'getResourceDetails',
        '/resource-health': 'getResourceHealth',
        '/security-assessment': 'getSecurityAssessment',
        '/encryption-status': 'checkEncryptionStatus',
    }
    
    return path_mapping.get(api_path, api_path.lstrip('/'))