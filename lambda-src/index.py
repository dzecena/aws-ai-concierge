"""
AWS AI Concierge Lambda Function
Main handler for Bedrock Agent action group tools
"""

import json
import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime

from utils.error_handler import ErrorHandler
from utils.response_formatter import ResponseFormatter
from utils.aws_clients import AWSClientManager
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
    
    Args:
        event: Lambda event containing the action and parameters
        context: Lambda context object
        
    Returns:
        Formatted response for Bedrock Agent
    """
    request_id = context.aws_request_id
    logger.info(f"[{request_id}] Processing request: {json.dumps(event, default=str)}")
    
    try:
        # Extract action from event
        action = event.get('actionGroup', '')
        api_path = event.get('apiPath', '')
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
            
        logger.info(f"[{request_id}] Action: {action}, API Path: {api_path}, Method: {http_method}")
        logger.info(f"[{request_id}] Parameters: {params_dict}")
        
        # Determine the operation based on API path
        operation = _extract_operation_from_path(api_path)
        
        if operation not in TOOL_ROUTES:
            raise ValueError(f"Unknown operation: {operation}")
            
        # Execute the appropriate tool handler
        tool_function = TOOL_ROUTES[operation]
        result = tool_function(params_dict, request_id)
        
        # Format successful response
        response = response_formatter.format_success_response(
            result, 
            operation, 
            request_id
        )
        
        logger.info(f"[{request_id}] Successfully processed {operation}")
        return response
        
    except Exception as e:
        logger.error(f"[{request_id}] Error processing request: {str(e)}", exc_info=True)
        
        # Format error response
        error_response = error_handler.handle_error(e, request_id)
        return response_formatter.format_error_response(error_response, request_id)


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