"""
Response formatting utilities for AWS AI Concierge
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ResponseFormatter:
    """Formats responses for Bedrock Agent consumption."""
    
    def format_success_response(self, data: Dict[str, Any], operation: str, request_id: str, api_path: str = None) -> Dict[str, Any]:
        """
        Format a successful response for Bedrock Agent.
        
        Args:
            data: The response data from the tool
            operation: The operation that was performed
            request_id: Request ID for tracking
            api_path: The API path from the request (if any)
            
        Returns:
            Formatted response dictionary
        """
        # CRITICAL: apiPath must ALWAYS be present and match the request
        if api_path is None:
            raise ValueError(f"api_path is required for Bedrock Agent response. Operation: {operation}")
        
        response_data = {
            'actionGroup': 'aws-ai-concierge-tools',
            'apiPath': api_path,  # MUST be present and match request
            'httpMethod': 'POST',
            'httpStatusCode': 200,
            'responseBody': {
                'application/json': {
                    'body': json.dumps({
                        'success': True,
                        'operation': operation,
                        'data': data,
                        'metadata': {
                            'request_id': request_id,
                            'timestamp': datetime.utcnow().isoformat(),
                            'version': '1.0'
                        }
                    })
                }
            }
        }
        
        response = {
            'messageVersion': '1.0',
            'response': response_data
        }
        
        logger.debug(f"[{request_id}] Formatted success response for {operation} with apiPath: {api_path}")
        return response
    
    def format_error_response(self, error_info: Dict[str, Any], request_id: str, api_path: str = None, operation: str = None) -> Dict[str, Any]:
        """
        Format an error response for Bedrock Agent.
        
        Args:
            error_info: Error information from ErrorHandler
            request_id: Request ID for tracking
            
        Returns:
            Formatted error response dictionary
        """
        http_status = self._get_http_status_for_error(error_info)
        
        # CRITICAL: apiPath must ALWAYS be present
        if api_path is None:
            logger.error(f"[{request_id}] Missing api_path in error response")
            # Use empty string as fallback, but this indicates a bug
            api_path = ""
        
        response_data = {
            'actionGroup': 'aws-ai-concierge-tools',
            'apiPath': api_path,  # MUST be present
            'httpMethod': 'POST',
            'httpStatusCode': http_status,
            'responseBody': {
                'application/json': {
                    'body': json.dumps({
                        'success': False,
                        'error': {
                            'message': error_info.get('user_message', 'An error occurred'),
                            'type': error_info.get('error_type', 'Unknown'),
                            'severity': error_info.get('severity', 'error'),
                            'retry_suggested': error_info.get('retry_suggested', False),
                            'retry_delay_seconds': error_info.get('retry_delay_seconds'),
                            'action_required': error_info.get('action_required')
                        },
                        'metadata': {
                            'request_id': request_id,
                            'timestamp': datetime.utcnow().isoformat(),
                            'version': '1.0'
                        }
                    })
                }
            }
        }
        
        response = {
            'messageVersion': '1.0',
            'response': response_data
        }
        
        logger.debug(f"[{request_id}] Formatted error response: {error_info.get('user_message')}")
        return response
    
    def format_business_friendly_response(self, data: Dict[str, Any], context: str) -> str:
        """
        Format data into business-friendly language.
        
        Args:
            data: Raw data to format
            context: Context for formatting (cost, security, resources, etc.)
            
        Returns:
            Business-friendly formatted string
        """
        if context == 'cost':
            return self._format_cost_data(data)
        elif context == 'security':
            return self._format_security_data(data)
        elif context == 'resources':
            return self._format_resource_data(data)
        else:
            return json.dumps(data, indent=2, default=str)
    
    def _get_api_path_for_operation(self, operation: str) -> str:
        """Map operation names to API paths."""
        path_mapping = {
            'getCostAnalysis': '/getCostAnalysis',
            'getIdleResources': '/getIdleResources',
            'getResourceInventory': '/getResourceInventory',
            'getResourceDetails': '/getResourceDetails',
            'getResourceHealth': '/getResourceHealth',
            'getSecurityAssessment': '/getSecurityAssessment',
            'checkEncryptionStatus': '/checkEncryptionStatus',
        }
        return path_mapping.get(operation, f'/{operation}')
    
    def _get_http_status_for_error(self, error_info: Dict[str, Any]) -> int:
        """Determine appropriate HTTP status code for error."""
        error_type = error_info.get('error_type', '')
        aws_error_code = error_info.get('aws_error_code', '')
        
        if aws_error_code in ['AccessDenied', 'UnauthorizedOperation']:
            return 403
        elif aws_error_code in ['Throttling', 'ThrottlingException']:
            return 429
        elif aws_error_code in ['InvalidParameterValue', 'ValidationException']:
            return 400
        elif error_type in ['ValueError', 'KeyError']:
            return 400
        elif aws_error_code in ['ServiceUnavailable']:
            return 503
        else:
            return 500
    
    def _format_cost_data(self, data: Dict[str, Any]) -> str:
        """Format cost analysis data for business users."""
        if 'total_cost' in data:
            total = data['total_cost']
            currency = data.get('currency', 'USD')
            period = data.get('time_period', 'current period')
            
            result = f"Total cost for {period}: {currency} {total:.2f}\n"
            
            if 'breakdown' in data and data['breakdown']:
                result += "\nCost breakdown by service:\n"
                for item in data['breakdown'][:10]:  # Top 10 services
                    service = item.get('service_name', 'Unknown')
                    cost = item.get('cost', 0)
                    percentage = item.get('percentage', 0)
                    result += f"• {service}: {currency} {cost:.2f} ({percentage:.1f}%)\n"
            
            return result
        
        return json.dumps(data, indent=2, default=str)
    
    def _format_security_data(self, data: Dict[str, Any]) -> str:
        """Format security assessment data for business users."""
        if 'findings' in data:
            findings = data['findings']
            risk_score = data.get('risk_score', 0)
            
            result = f"Security Risk Score: {risk_score}/100\n"
            
            if findings:
                high_risk = [f for f in findings if f.get('severity') == 'HIGH']
                medium_risk = [f for f in findings if f.get('severity') == 'MEDIUM']
                
                if high_risk:
                    result += f"\n🔴 High Risk Issues ({len(high_risk)}):\n"
                    for finding in high_risk[:5]:  # Top 5 high risk
                        result += f"• {finding.get('title', 'Security Issue')}\n"
                
                if medium_risk:
                    result += f"\n🟡 Medium Risk Issues ({len(medium_risk)}):\n"
                    for finding in medium_risk[:3]:  # Top 3 medium risk
                        result += f"• {finding.get('title', 'Security Issue')}\n"
            
            return result
        
        return json.dumps(data, indent=2, default=str)
    
    def _format_resource_data(self, data: Dict[str, Any]) -> str:
        """Format resource inventory data for business users."""
        if 'resources' in data:
            resources = data['resources']
            total_count = data.get('total_count', len(resources))
            region = data.get('region', 'multiple regions')
            
            result = f"Found {total_count} resources in {region}\n"
            
            # Group by resource type
            by_type = {}
            for resource in resources:
                res_type = resource.get('resource_type', 'Unknown')
                if res_type not in by_type:
                    by_type[res_type] = []
                by_type[res_type].append(resource)
            
            result += "\nResource breakdown:\n"
            for res_type, res_list in by_type.items():
                result += f"• {res_type}: {len(res_list)} resources\n"
            
            return result
        
        return json.dumps(data, indent=2, default=str)