"""
Error handling utilities for AWS AI Concierge
"""

import logging
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError, BotoCoreError
from datetime import datetime

logger = logging.getLogger(__name__)


class ErrorHandler:
    """Handles and translates various types of errors into user-friendly messages."""
    
    def __init__(self):
        self.error_mappings = {
            'AccessDenied': self._handle_access_denied,
            'UnauthorizedOperation': self._handle_access_denied,
            'Throttling': self._handle_throttling,
            'ThrottlingException': self._handle_throttling,
            'ServiceUnavailable': self._handle_service_unavailable,
            'InternalError': self._handle_internal_error,
            'InvalidParameterValue': self._handle_invalid_parameter,
            'ValidationException': self._handle_validation_error,
        }
    
    def handle_error(self, error: Exception, request_id: str) -> Dict[str, Any]:
        """
        Handle and translate errors into user-friendly responses.
        
        Args:
            error: The exception that occurred
            request_id: Request ID for tracking
            
        Returns:
            Error response dictionary
        """
        error_info = {
            'request_id': request_id,
            'timestamp': datetime.utcnow().isoformat(),
            'error_type': type(error).__name__,
            'original_message': str(error)
        }
        
        if isinstance(error, ClientError):
            return self._handle_aws_client_error(error, error_info)
        elif isinstance(error, BotoCoreError):
            return self._handle_boto_core_error(error, error_info)
        elif isinstance(error, ValueError):
            return self._handle_value_error(error, error_info)
        elif isinstance(error, KeyError):
            return self._handle_key_error(error, error_info)
        else:
            return self._handle_generic_error(error, error_info)
    
    def _handle_aws_client_error(self, error: ClientError, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """Handle AWS service client errors."""
        error_code = error.response.get('Error', {}).get('Code', 'Unknown')
        error_message = error.response.get('Error', {}).get('Message', str(error))
        
        error_info.update({
            'aws_error_code': error_code,
            'aws_error_message': error_message,
            'service': error.operation_name if hasattr(error, 'operation_name') else 'Unknown'
        })
        
        # Use specific handler if available
        if error_code in self.error_mappings:
            return self.error_mappings[error_code](error_info)
        
        # Default AWS error handling
        return {
            **error_info,
            'user_message': f"AWS service error: {error_message}",
            'severity': 'error',
            'retry_suggested': error_code in ['Throttling', 'ServiceUnavailable', 'InternalError']
        }
    
    def _handle_boto_core_error(self, error: BotoCoreError, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """Handle boto3 core errors."""
        return {
            **error_info,
            'user_message': "There was a problem connecting to AWS services. Please try again.",
            'severity': 'error',
            'retry_suggested': True
        }
    
    def _handle_access_denied(self, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """Handle access denied errors."""
        service = error_info.get('service', 'AWS service')
        return {
            **error_info,
            'user_message': f"I don't have permission to access {service}. Please ensure the IAM role has the necessary permissions.",
            'severity': 'error',
            'retry_suggested': False,
            'action_required': 'Check IAM permissions'
        }
    
    def _handle_throttling(self, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """Handle throttling errors."""
        return {
            **error_info,
            'user_message': "AWS is currently rate limiting requests. Please try again in a few moments.",
            'severity': 'warning',
            'retry_suggested': True,
            'retry_delay_seconds': 30
        }
    
    def _handle_service_unavailable(self, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """Handle service unavailable errors."""
        service = error_info.get('service', 'AWS service')
        return {
            **error_info,
            'user_message': f"The {service} is temporarily unavailable. You can check AWS service status at https://status.aws.amazon.com/",
            'severity': 'error',
            'retry_suggested': True,
            'retry_delay_seconds': 300
        }
    
    def _handle_internal_error(self, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """Handle internal AWS errors."""
        return {
            **error_info,
            'user_message': "AWS encountered an internal error. Please try again.",
            'severity': 'error',
            'retry_suggested': True
        }
    
    def _handle_invalid_parameter(self, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """Handle invalid parameter errors."""
        return {
            **error_info,
            'user_message': "One of the parameters provided is invalid. Please check your request and try again.",
            'severity': 'error',
            'retry_suggested': False
        }
    
    def _handle_validation_error(self, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """Handle validation errors."""
        return {
            **error_info,
            'user_message': "The request parameters failed validation. Please check the format and try again.",
            'severity': 'error',
            'retry_suggested': False
        }
    
    def _handle_value_error(self, error: ValueError, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """Handle ValueError exceptions."""
        return {
            **error_info,
            'user_message': f"Invalid input: {str(error)}",
            'severity': 'error',
            'retry_suggested': False
        }
    
    def _handle_key_error(self, error: KeyError, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """Handle KeyError exceptions."""
        missing_key = str(error).strip("'\"")
        return {
            **error_info,
            'user_message': f"Missing required parameter: {missing_key}",
            'severity': 'error',
            'retry_suggested': False
        }
    
    def _handle_generic_error(self, error: Exception, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """Handle generic exceptions."""
        return {
            **error_info,
            'user_message': "An unexpected error occurred. Please try again or contact support if the problem persists.",
            'severity': 'error',
            'retry_suggested': True
        }