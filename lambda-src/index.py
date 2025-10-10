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
    Supports Bedrock Agent function-based calls.
    
    Args:
        event: Lambda event containing the action and parameters
        context: Lambda context object
        
    Returns:
        Formatted response for Bedrock Agent
    """
    request_id = context.aws_request_id
    start_time = time.time()
    
    logger.info(f"[{request_id}] Processing Bedrock Agent request")
    logger.info(f"[{request_id}] Event: {json.dumps(event, default=str)}")
    
    try:
        # Extract Bedrock Agent event details
        action_group = event.get('actionGroup', 'aws-ai-concierge-tools')
        function_name = event.get('function', '')
        parameters = event.get('parameters', [])
        
        # Convert parameters list to dict for easier handling
        params_dict = {}
        if isinstance(parameters, list):
            for param in parameters:
                if isinstance(param, dict) and 'name' in param and 'value' in param:
                    params_dict[param['name']] = param['value']
        elif isinstance(parameters, dict):
            params_dict = parameters
        
        logger.info(f"[{request_id}] Function: {function_name}, Params: {params_dict}")
        
        # Route to appropriate handler
        if function_name not in TOOL_ROUTES:
            raise ValueError(f"Unknown function: {function_name}")
        
        # Execute the tool handler
        tool_start_time = time.time()
        tool_function = TOOL_ROUTES[function_name]
        result = tool_function(params_dict, request_id)
        tool_execution_time = (time.time() - tool_start_time) * 1000
        
        logger.info(f"[{request_id}] Tool executed successfully in {tool_execution_time:.2f}ms")
        
        # Format response for Bedrock Agent (function-based, no apiPath needed)
        response = {
            "messageVersion": "1.0",
            "response": {
                "actionGroup": action_group,
                "function": function_name,
                "functionResponse": {
                    "responseBody": {
                        "TEXT": {
                            "body": json.dumps({
                                "success": True,
                                "operation": function_name,
                                "data": result,
                                "metadata": {
                                    "request_id": request_id,
                                    "timestamp": datetime.utcnow().isoformat(),
                                    "version": "1.0"
                                }
                            })
                        }
                    }
                }
            }
        }
        
        processing_time = (time.time() - start_time) * 1000
        logger.info(f"[{request_id}] Request processed successfully in {processing_time:.2f}ms")
        
        return response
        
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        logger.error(f"[{request_id}] Error processing request: {str(e)}", exc_info=True)
        
        # Return error response for Bedrock Agent
        error_response = {
            "messageVersion": "1.0",
            "response": {
                "actionGroup": event.get('actionGroup', 'aws-ai-concierge-tools'),
                "function": event.get('function', ''),
                "functionResponse": {
                    "responseBody": {
                        "TEXT": {
                            "body": json.dumps({
                                "success": False,
                                "error": {
                                    "message": str(e),
                                    "type": type(e).__name__
                                },
                                "metadata": {
                                    "request_id": request_id,
                                    "timestamp": datetime.utcnow().isoformat(),
                                    "version": "1.0"
                                }
                            })
                        }
                    }
                }
            }
        }
        
        return error_response


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
        '/getCostAnalysis': 'getCostAnalysis',
        '/getIdleResources': 'getIdleResources',
        '/getResourceInventory': 'getResourceInventory',
        '/getResourceDetails': 'getResourceDetails',
        '/getResourceHealth': 'getResourceHealth',
        '/getSecurityAssessment': 'getSecurityAssessment',
        '/checkEncryptionStatus': 'checkEncryptionStatus',
    }
    
    return path_mapping.get(api_path, api_path.lstrip('/'))