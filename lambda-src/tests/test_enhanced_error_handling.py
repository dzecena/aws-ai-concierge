"""
Unit tests for enhanced error handling and audit logging
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime
from botocore.exceptions import ClientError

from utils.error_handler import ErrorHandler
from utils.audit_logger import AuditLogger, AuditEventType
from utils.aws_clients import AWSClientManager


class TestEnhancedErrorHandling(unittest.TestCase):
    """Test enhanced error handling functionality."""
    
    def setUp(self):
        self.error_handler = ErrorHandler()
        self.request_id = 'test-request-123'
    
    def test_handle_aws_client_error_access_denied(self):
        """Test handling of AWS access denied errors."""
        error = ClientError(
            error_response={
                'Error': {
                    'Code': 'AccessDenied',
                    'Message': 'User is not authorized to perform this action'
                }
            },
            operation_name='DescribeInstances'
        )
        
        result = self.error_handler.handle_error(error, self.request_id)
        
        self.assertEqual(result['request_id'], self.request_id)
        self.assertEqual(result['aws_error_code'], 'AccessDenied')
        self.assertIn('permission', result['user_message'].lower())
        self.assertEqual(result['severity'], 'error')
        self.assertFalse(result['retry_suggested'])
        self.assertEqual(result['action_required'], 'Check IAM permissions')
    
    def test_handle_aws_client_error_throttling(self):
        """Test handling of AWS throttling errors."""
        error = ClientError(
            error_response={
                'Error': {
                    'Code': 'Throttling',
                    'Message': 'Rate exceeded'
                }
            },
            operation_name='GetCostAndUsage'
        )
        
        result = self.error_handler.handle_error(error, self.request_id)
        
        self.assertEqual(result['aws_error_code'], 'Throttling')
        self.assertIn('rate limiting', result['user_message'].lower())
        self.assertEqual(result['severity'], 'warning')
        self.assertTrue(result['retry_suggested'])
        self.assertEqual(result['retry_delay_seconds'], 30)
    
    def test_handle_value_error(self):
        """Test handling of ValueError exceptions."""
        error = ValueError("Invalid time_period 'INVALID'. Must be one of: ['DAILY', 'MONTHLY', 'YEARLY']")
        
        result = self.error_handler.handle_error(error, self.request_id)
        
        self.assertEqual(result['error_type'], 'ValueError')
        self.assertIn('Invalid input', result['user_message'])
        self.assertEqual(result['severity'], 'error')
        self.assertFalse(result['retry_suggested'])
    
    def test_handle_key_error(self):
        """Test handling of KeyError exceptions."""
        error = KeyError('required_parameter')
        
        result = self.error_handler.handle_error(error, self.request_id)
        
        self.assertEqual(result['error_type'], 'KeyError')
        self.assertIn('Missing required parameter', result['user_message'])
        self.assertIn('required_parameter', result['user_message'])
        self.assertEqual(result['severity'], 'error')
        self.assertFalse(result['retry_suggested'])
    
    def test_handle_generic_error(self):
        """Test handling of generic exceptions."""
        error = RuntimeError("Something went wrong")
        
        result = self.error_handler.handle_error(error, self.request_id)
        
        self.assertEqual(result['error_type'], 'RuntimeError')
        self.assertIn('unexpected error', result['user_message'].lower())
        self.assertEqual(result['severity'], 'error')
        self.assertTrue(result['retry_suggested'])


class TestAuditLogger(unittest.TestCase):
    """Test audit logging functionality."""
    
    def setUp(self):
        self.audit_logger = AuditLogger()
        self.request_id = 'test-request-123'
    
    @patch('utils.audit_logger.logging.getLogger')
    def test_log_request_received(self, mock_get_logger):
        """Test logging of incoming requests."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        self.audit_logger.log_request_received(
            request_id=self.request_id,
            event_source='bedrock_agent',
            operation='getCostAnalysis',
            parameters={'time_period': 'MONTHLY'},
            user_context={'action_group': 'cost-tools'}
        )
        
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        self.assertIn('AUDIT_REQUEST:', call_args)
        
        # Parse the logged JSON
        json_part = call_args.split('AUDIT_REQUEST: ')[1]
        logged_data = json.loads(json_part)
        
        self.assertEqual(logged_data['event_type'], AuditEventType.REQUEST_RECEIVED.value)
        self.assertEqual(logged_data['request_id'], self.request_id)
        self.assertEqual(logged_data['event_source'], 'bedrock_agent')
        self.assertEqual(logged_data['operation'], 'getCostAnalysis')
    
    @patch('utils.audit_logger.logging.getLogger')
    def test_log_tool_invocation(self, mock_get_logger):
        """Test logging of tool invocations."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        self.audit_logger.log_tool_invocation(
            request_id=self.request_id,
            tool_name='getCostAnalysis',
            parameters={'time_period': 'MONTHLY'},
            execution_time_ms=2500.5,
            success=True
        )
        
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        self.assertIn('AUDIT_TOOL:', call_args)
        
        # Parse the logged JSON
        json_part = call_args.split('AUDIT_TOOL: ')[1]
        logged_data = json.loads(json_part)
        
        self.assertEqual(logged_data['event_type'], AuditEventType.TOOL_INVOCATION.value)
        self.assertEqual(logged_data['tool_name'], 'getCostAnalysis')
        self.assertEqual(logged_data['execution_time_ms'], 2500.5)
        self.assertTrue(logged_data['success'])
        self.assertTrue(logged_data['performance']['meets_sla'])
    
    @patch('utils.audit_logger.logging.getLogger')
    def test_log_aws_api_call_success(self, mock_get_logger):
        """Test logging of successful AWS API calls."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        self.audit_logger.log_aws_api_call(
            request_id=self.request_id,
            service='ce',
            operation='get_cost_and_usage',
            region='us-east-1',
            success=True,
            response_size_bytes=1024
        )
        
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        self.assertIn('AUDIT_AWS_SUCCESS:', call_args)
        
        # Parse the logged JSON
        json_part = call_args.split('AUDIT_AWS_SUCCESS: ')[1]
        logged_data = json.loads(json_part)
        
        self.assertEqual(logged_data['event_type'], AuditEventType.AWS_API_CALL.value)
        self.assertEqual(logged_data['aws_service'], 'ce')
        self.assertEqual(logged_data['aws_operation'], 'get_cost_and_usage')
        self.assertTrue(logged_data['success'])
        self.assertTrue(logged_data['compliance']['read_only_operation'])
    
    @patch('utils.audit_logger.logging.getLogger')
    def test_log_aws_api_call_failure(self, mock_get_logger):
        """Test logging of failed AWS API calls."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        self.audit_logger.log_aws_api_call(
            request_id=self.request_id,
            service='ec2',
            operation='describe_instances',
            region='us-west-2',
            success=False,
            error_code='AccessDenied'
        )
        
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args[0][0]
        self.assertIn('AUDIT_AWS_ERROR:', call_args)
        
        # Parse the logged JSON
        json_part = call_args.split('AUDIT_AWS_ERROR: ')[1]
        logged_data = json.loads(json_part)
        
        self.assertEqual(logged_data['aws_service'], 'ec2')
        self.assertFalse(logged_data['success'])
        self.assertEqual(logged_data['error_code'], 'AccessDenied')
    
    @patch('utils.audit_logger.logging.getLogger')
    def test_log_security_check(self, mock_get_logger):
        """Test logging of security assessments."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        self.audit_logger.log_security_check(
            request_id=self.request_id,
            check_type='security_groups',
            resource_id='us-east-1',
            findings_count=5,
            risk_score=75
        )
        
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        self.assertIn('AUDIT_SECURITY:', call_args)
        
        # Parse the logged JSON
        json_part = call_args.split('AUDIT_SECURITY: ')[1]
        logged_data = json.loads(json_part)
        
        self.assertEqual(logged_data['event_type'], AuditEventType.SECURITY_CHECK.value)
        self.assertEqual(logged_data['check_type'], 'security_groups')
        self.assertEqual(logged_data['findings_count'], 5)
        self.assertEqual(logged_data['risk_score'], 75)
        self.assertTrue(logged_data['security']['high_risk_detected'])
    
    def test_sanitize_parameters(self):
        """Test parameter sanitization for sensitive data."""
        parameters = {
            'time_period': 'MONTHLY',
            'password': 'secret123',
            'api_key': 'key123',
            'normal_param': 'value'
        }
        
        sanitized = self.audit_logger._sanitize_parameters(parameters)
        
        self.assertEqual(sanitized['time_period'], 'MONTHLY')
        self.assertEqual(sanitized['password'], '[REDACTED]')
        self.assertEqual(sanitized['api_key'], '[REDACTED]')
        self.assertEqual(sanitized['normal_param'], 'value')
    
    def test_categorize_execution_time(self):
        """Test execution time categorization."""
        self.assertEqual(self.audit_logger._categorize_execution_time(500), 'fast')
        self.assertEqual(self.audit_logger._categorize_execution_time(2000), 'normal')
        self.assertEqual(self.audit_logger._categorize_execution_time(8000), 'slow')
        self.assertEqual(self.audit_logger._categorize_execution_time(20000), 'very_slow')


class TestAWSClientManagerAuditLogging(unittest.TestCase):
    """Test AWS client manager audit logging functionality."""
    
    def setUp(self):
        self.aws_clients = AWSClientManager()
        self.request_id = 'test-request-123'
    
    @patch('utils.aws_clients.AuditLogger')
    def test_make_api_call_success(self, mock_audit_logger_class):
        """Test successful API call with audit logging."""
        mock_audit_logger = Mock()
        mock_audit_logger_class.return_value = mock_audit_logger
        
        # Mock client and response
        mock_client = Mock()
        mock_client._service_model.service_name = 'ec2'
        mock_client.meta.client.region_name = 'us-east-1'
        mock_response = {'Instances': []}
        
        # Mock the API method
        mock_method = Mock(return_value=mock_response)
        setattr(mock_client, 'describe_instances', mock_method)
        
        result = self.aws_clients.make_api_call(
            client=mock_client,
            operation='describe_instances',
            request_id=self.request_id,
            MaxResults=10
        )
        
        self.assertEqual(result, mock_response)
        mock_method.assert_called_once_with(MaxResults=10)
        mock_audit_logger.log_aws_api_call.assert_called_once_with(
            request_id=self.request_id,
            service='ec2',
            operation='describe_instances',
            region='us-east-1',
            success=True,
            response_size_bytes=unittest.mock.ANY
        )
    
    @patch('utils.aws_clients.AuditLogger')
    def test_make_api_call_client_error(self, mock_audit_logger_class):
        """Test API call failure with audit logging."""
        mock_audit_logger = Mock()
        mock_audit_logger_class.return_value = mock_audit_logger
        
        # Mock client
        mock_client = Mock()
        mock_client._service_model.service_name = 'ec2'
        mock_client.meta.client.region_name = 'us-east-1'
        
        # Mock the API method to raise ClientError
        error = ClientError(
            error_response={'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
            operation_name='describe_instances'
        )
        mock_method = Mock(side_effect=error)
        setattr(mock_client, 'describe_instances', mock_method)
        
        with self.assertRaises(ClientError):
            self.aws_clients.make_api_call(
                client=mock_client,
                operation='describe_instances',
                request_id=self.request_id
            )
        
        mock_audit_logger.log_aws_api_call.assert_called_once_with(
            request_id=self.request_id,
            service='ec2',
            operation='describe_instances',
            region='us-east-1',
            success=False,
            error_code='AccessDenied'
        )


if __name__ == '__main__':
    unittest.main()