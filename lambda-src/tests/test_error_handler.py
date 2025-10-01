"""
Unit tests for error handling utilities
"""

import unittest
from unittest.mock import Mock
from botocore.exceptions import ClientError
from utils.error_handler import ErrorHandler


class TestErrorHandler(unittest.TestCase):
    
    def setUp(self):
        self.error_handler = ErrorHandler()
        self.request_id = "test-request-123"
    
    def test_handle_access_denied_error(self):
        """Test handling of AccessDenied errors."""
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
        self.assertIn("don't have permission", result['user_message'])
        self.assertEqual(result['severity'], 'error')
        self.assertFalse(result['retry_suggested'])
    
    def test_handle_throttling_error(self):
        """Test handling of throttling errors."""
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
        self.assertIn("rate limiting", result['user_message'])
        self.assertEqual(result['severity'], 'warning')
        self.assertTrue(result['retry_suggested'])
        self.assertEqual(result['retry_delay_seconds'], 30)
    
    def test_handle_value_error(self):
        """Test handling of ValueError exceptions."""
        error = ValueError("Invalid parameter value")
        
        result = self.error_handler.handle_error(error, self.request_id)
        
        self.assertEqual(result['error_type'], 'ValueError')
        self.assertIn("Invalid input", result['user_message'])
        self.assertEqual(result['severity'], 'error')
        self.assertFalse(result['retry_suggested'])
    
    def test_handle_key_error(self):
        """Test handling of KeyError exceptions."""
        error = KeyError("required_parameter")
        
        result = self.error_handler.handle_error(error, self.request_id)
        
        self.assertEqual(result['error_type'], 'KeyError')
        self.assertIn("Missing required parameter", result['user_message'])
        self.assertIn("required_parameter", result['user_message'])
        self.assertEqual(result['severity'], 'error')
        self.assertFalse(result['retry_suggested'])
    
    def test_handle_generic_error(self):
        """Test handling of generic exceptions."""
        error = RuntimeError("Something went wrong")
        
        result = self.error_handler.handle_error(error, self.request_id)
        
        self.assertEqual(result['error_type'], 'RuntimeError')
        self.assertIn("unexpected error", result['user_message'])
        self.assertEqual(result['severity'], 'error')
        self.assertTrue(result['retry_suggested'])


if __name__ == '__main__':
    unittest.main()