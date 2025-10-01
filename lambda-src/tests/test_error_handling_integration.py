"""
Integration tests for error handling and audit logging
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import time
from datetime import datetime
from botocore.exceptions import ClientError

# Import the main handler
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from index import handler


class TestErrorHandlingIntegration(unittest.TestCase):
    """Integration tests for error handling and audit logging."""
    
    def setUp(self):
        self.context = Mock()
        self.context.aws_request_id = 'test-request-123'
        self.context.function_version = '$LATEST'
    
    @patch('index.audit_logger')
    @patch('index.cost_handler')
    def test_bedrock_agent_success_with_audit_logging(self, mock_cost_handler, mock_audit_logger):
        """Test successful Bedrock Agent request with complete audit logging."""
        # Mock successful cost analysis
        mock_result = {
            'total_cost': 150.75,
            'cost_breakdown': [{'service': 'EC2', 'cost': 100.50}],
            'optimization_recommendations': ['Stop idle instances']
        }
        mock_cost_handler.get_cost_analysis.return_value = mock_result
        
        # Bedrock Agent event
        event = {
            'actionGroup': 'cost-tools',
            'apiPath': '/cost-analysis',
            'httpMethod': 'POST',
            'parameters': [
                {'name': 'time_period', 'value': 'MONTHLY'},
                {'name': 'granularity', 'value': 'DAILY'}
            ]
        }
        
        result = handler(event, self.context)
        
        # Verify the handler was called
        mock_cost_handler.get_cost_analysis.assert_called_once()
        
        # Verify audit logging calls
        mock_audit_logger.log_request_received.assert_called_once_with(
            request_id='test-request-123',
            event_source='bedrock_agent',
            operation='getCostAnalysis',
            parameters={'time_period': 'MONTHLY', 'granularity': 'DAILY'},
            user_context={'action_group': 'cost-tools', 'api_path': '/cost-analysis'}
        )
        
        mock_audit_logger.log_tool_invocation.assert_called_once()
        tool_call_args = mock_audit_logger.log_tool_invocation.call_args[1]
        self.assertEqual(tool_call_args['request_id'], 'test-request-123')
        self.assertEqual(tool_call_args['tool_name'], 'getCostAnalysis')
        self.assertTrue(tool_call_args['success'])
        
        mock_audit_logger.log_response_sent.assert_called_once()
        response_call_args = mock_audit_logger.log_response_sent.call_args[1]
        self.assertEqual(response_call_args['request_id'], 'test-request-123')
        self.assertTrue(response_call_args['success'])
        
        # Verify response structure
        self.assertIn('messageVersion', result)
        self.assertIn('response', result)
    
    @patch('index.audit_logger')
    @patch('index.cost_handler')
    def test_api_gateway_success_with_audit_logging(self, mock_cost_handler, mock_audit_logger):
        """Test successful API Gateway request with complete audit logging."""
        # Mock successful cost analysis
        mock_result = {
            'total_cost': 150.75,
            'cost_breakdown': [{'service': 'EC2', 'cost': 100.50}]
        }
        mock_cost_handler.get_cost_analysis.return_value = mock_result
        
        # API Gateway event
        event = {
            'httpMethod': 'POST',
            'path': '/cost-analysis',
            'body': json.dumps({
                'time_period': 'MONTHLY',
                'granularity': 'DAILY'
            })
        }
        
        result = handler(event, self.context)
        
        # Verify response structure
        self.assertEqual(result['statusCode'], 200)
        self.assertIn('application/json', result['headers']['Content-Type'])
        
        body = json.loads(result['body'])
        self.assertTrue(body['success'])
        self.assertEqual(body['operation'], 'getCostAnalysis')
        self.assertEqual(body['data'], mock_result)
        
        # Verify audit logging
        mock_audit_logger.log_request_received.assert_called_once_with(
            request_id='test-request-123',
            event_source='api_gateway',
            operation='getCostAnalysis',
            parameters={'time_period': 'MONTHLY', 'granularity': 'DAILY'},
            user_context={'path': '/cost-analysis', 'method': 'POST'}
        )
    
    @patch('index.audit_logger')
    @patch('index.error_handler')
    @patch('index.cost_handler')
    def test_bedrock_agent_error_with_audit_logging(self, mock_cost_handler, mock_error_handler, mock_audit_logger):
        """Test Bedrock Agent error handling with complete audit logging."""
        # Mock error from cost handler
        error = ClientError(
            error_response={
                'Error': {
                    'Code': 'AccessDenied',
                    'Message': 'User is not authorized'
                }
            },
            operation_name='GetCostAndUsage'
        )
        mock_cost_handler.get_cost_analysis.side_effect = error
        
        # Mock error handler response
        mock_error_response = {
            'request_id': 'test-request-123',
            'error_type': 'ClientError',
            'aws_error_code': 'AccessDenied',
            'user_message': 'I don\'t have permission to access Cost Explorer',
            'severity': 'error',
            'retry_suggested': False
        }
        mock_error_handler.handle_error.return_value = mock_error_response
        
        # Bedrock Agent event
        event = {
            'actionGroup': 'cost-tools',
            'apiPath': '/cost-analysis',
            'httpMethod': 'POST',
            'parameters': [{'name': 'time_period', 'value': 'MONTHLY'}]
        }
        
        result = handler(event, self.context)
        
        # Verify error handling was called
        mock_error_handler.handle_error.assert_called_once_with(error, 'test-request-123')
        
        # Verify audit logging for error
        mock_audit_logger.log_error_occurred.assert_called_once()
        error_call_args = mock_audit_logger.log_error_occurred.call_args[1]
        self.assertEqual(error_call_args['request_id'], 'test-request-123')
        self.assertEqual(error_call_args['error_type'], 'ClientError')
        self.assertEqual(error_call_args['error_code'], 'AccessDenied')
        self.assertEqual(error_call_args['severity'], 'error')
        
        # Verify failed tool invocation logging
        mock_audit_logger.log_tool_invocation.assert_called_once()
        tool_call_args = mock_audit_logger.log_tool_invocation.call_args[1]
        self.assertFalse(tool_call_args['success'])
        
        # Verify error response logging
        mock_audit_logger.log_response_sent.assert_called_once()
        response_call_args = mock_audit_logger.log_response_sent.call_args[1]
        self.assertFalse(response_call_args['success'])
    
    @patch('index.audit_logger')
    @patch('index.error_handler')
    @patch('index.cost_handler')
    def test_api_gateway_error_with_audit_logging(self, mock_cost_handler, mock_error_handler, mock_audit_logger):
        """Test API Gateway error handling with complete audit logging."""
        # Mock validation error
        error = ValueError("Invalid time_period 'INVALID'. Must be one of: ['DAILY', 'MONTHLY', 'YEARLY']")
        mock_cost_handler.get_cost_analysis.side_effect = error
        
        # Mock error handler response
        mock_error_response = {
            'request_id': 'test-request-123',
            'error_type': 'ValueError',
            'user_message': 'Invalid input: Invalid time_period \'INVALID\'',
            'severity': 'error',
            'retry_suggested': False
        }
        mock_error_handler.handle_error.return_value = mock_error_response
        
        # API Gateway event
        event = {
            'httpMethod': 'POST',
            'path': '/cost-analysis',
            'body': json.dumps({'time_period': 'INVALID'})
        }
        
        result = handler(event, self.context)
        
        # Verify error response structure
        self.assertEqual(result['statusCode'], 500)
        self.assertIn('application/json', result['headers']['Content-Type'])
        
        body = json.loads(result['body'])
        self.assertFalse(body['success'])
        self.assertEqual(body['error'], mock_error_response)
        
        # Verify audit logging
        mock_audit_logger.log_error_occurred.assert_called_once()
        mock_audit_logger.log_response_sent.assert_called_once()
    
    @patch('index.audit_logger')
    def test_unknown_operation_error(self, mock_audit_logger):
        """Test handling of unknown operation with audit logging."""
        # Bedrock Agent event with unknown operation
        event = {
            'actionGroup': 'unknown-tools',
            'apiPath': '/unknown-operation',
            'httpMethod': 'POST',
            'parameters': []
        }
        
        result = handler(event, self.context)
        
        # Should still log the request
        mock_audit_logger.log_request_received.assert_called_once()
        
        # Should log the error
        mock_audit_logger.log_error_occurred.assert_called_once()
        error_call_args = mock_audit_logger.log_error_occurred.call_args[1]
        self.assertEqual(error_call_args['error_type'], 'ValueError')
        self.assertIn('Unknown operation', error_call_args['user_impact'])
    
    @patch('index.audit_logger')
    @patch('index.cost_handler')
    def test_performance_monitoring(self, mock_cost_handler, mock_audit_logger):
        """Test performance monitoring through audit logging."""
        # Mock slow operation
        def slow_operation(*args, **kwargs):
            time.sleep(0.1)  # Simulate 100ms operation
            return {'total_cost': 100.0}
        
        mock_cost_handler.get_cost_analysis.side_effect = slow_operation
        
        # API Gateway event
        event = {
            'httpMethod': 'POST',
            'path': '/cost-analysis',
            'body': json.dumps({'time_period': 'MONTHLY'})
        }
        
        start_time = time.time()
        result = handler(event, self.context)
        end_time = time.time()
        
        # Verify response
        self.assertEqual(result['statusCode'], 200)
        
        # Verify performance logging
        mock_audit_logger.log_tool_invocation.assert_called_once()
        tool_call_args = mock_audit_logger.log_tool_invocation.call_args[1]
        self.assertGreater(tool_call_args['execution_time_ms'], 90)  # Should be > 90ms
        
        mock_audit_logger.log_response_sent.assert_called_once()
        response_call_args = mock_audit_logger.log_response_sent.call_args[1]
        self.assertGreater(response_call_args['processing_time_ms'], 90)  # Should be > 90ms


if __name__ == '__main__':
    unittest.main()