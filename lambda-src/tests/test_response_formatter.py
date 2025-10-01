"""
Unit tests for response formatting utilities
"""

import unittest
import json
from utils.response_formatter import ResponseFormatter


class TestResponseFormatter(unittest.TestCase):
    
    def setUp(self):
        self.formatter = ResponseFormatter()
        self.request_id = "test-request-123"
    
    def test_format_success_response(self):
        """Test formatting of successful responses."""
        data = {
            'total_cost': 150.75,
            'currency': 'USD',
            'breakdown': [
                {'service_name': 'EC2', 'cost': 100.50},
                {'service_name': 'S3', 'cost': 50.25}
            ]
        }
        operation = 'getCostAnalysis'
        
        result = self.formatter.format_success_response(data, operation, self.request_id)
        
        self.assertEqual(result['messageVersion'], '1.0')
        self.assertEqual(result['response']['httpStatusCode'], 200)
        self.assertEqual(result['response']['apiPath'], '/cost-analysis')
        
        response_body = json.loads(result['response']['responseBody']['application/json']['body'])
        self.assertTrue(response_body['success'])
        self.assertEqual(response_body['operation'], operation)
        self.assertEqual(response_body['data'], data)
        self.assertEqual(response_body['metadata']['request_id'], self.request_id)
    
    def test_format_error_response(self):
        """Test formatting of error responses."""
        error_info = {
            'user_message': 'Access denied to EC2 service',
            'error_type': 'ClientError',
            'severity': 'error',
            'retry_suggested': False,
            'aws_error_code': 'AccessDenied'
        }
        
        result = self.formatter.format_error_response(error_info, self.request_id)
        
        self.assertEqual(result['messageVersion'], '1.0')
        self.assertEqual(result['response']['httpStatusCode'], 403)  # AccessDenied -> 403
        self.assertEqual(result['response']['apiPath'], '/error')
        
        response_body = json.loads(result['response']['responseBody']['application/json']['body'])
        self.assertFalse(response_body['success'])
        self.assertEqual(response_body['error']['message'], error_info['user_message'])
        self.assertEqual(response_body['error']['type'], error_info['error_type'])
        self.assertEqual(response_body['metadata']['request_id'], self.request_id)
    
    def test_get_http_status_for_error(self):
        """Test HTTP status code mapping for different error types."""
        # Test AccessDenied -> 403
        error_info = {'aws_error_code': 'AccessDenied'}
        status = self.formatter._get_http_status_for_error(error_info)
        self.assertEqual(status, 403)
        
        # Test Throttling -> 429
        error_info = {'aws_error_code': 'Throttling'}
        status = self.formatter._get_http_status_for_error(error_info)
        self.assertEqual(status, 429)
        
        # Test ValueError -> 400
        error_info = {'error_type': 'ValueError'}
        status = self.formatter._get_http_status_for_error(error_info)
        self.assertEqual(status, 400)
        
        # Test ServiceUnavailable -> 503
        error_info = {'aws_error_code': 'ServiceUnavailable'}
        status = self.formatter._get_http_status_for_error(error_info)
        self.assertEqual(status, 503)
        
        # Test unknown error -> 500
        error_info = {'error_type': 'UnknownError'}
        status = self.formatter._get_http_status_for_error(error_info)
        self.assertEqual(status, 500)
    
    def test_format_cost_data(self):
        """Test business-friendly formatting of cost data."""
        data = {
            'total_cost': 150.75,
            'currency': 'USD',
            'time_period': 'current month',
            'breakdown': [
                {'service_name': 'EC2', 'cost': 100.50, 'percentage': 66.8},
                {'service_name': 'S3', 'cost': 50.25, 'percentage': 33.2}
            ]
        }
        
        result = self.formatter._format_cost_data(data)
        
        self.assertIn('Total cost for current month: USD 150.75', result)
        self.assertIn('EC2: USD 100.50 (66.8%)', result)
        self.assertIn('S3: USD 50.25 (33.2%)', result)
    
    def test_format_security_data(self):
        """Test business-friendly formatting of security data."""
        data = {
            'risk_score': 75,
            'findings': [
                {'severity': 'HIGH', 'title': 'Security group allows public SSH access'},
                {'severity': 'HIGH', 'title': 'S3 bucket is publicly accessible'},
                {'severity': 'MEDIUM', 'title': 'EBS volume is not encrypted'}
            ]
        }
        
        result = self.formatter._format_security_data(data)
        
        self.assertIn('Security Risk Score: 75/100', result)
        self.assertIn('High Risk Issues (2)', result)
        self.assertIn('Medium Risk Issues (1)', result)
        self.assertIn('Security group allows public SSH access', result)
    
    def test_format_resource_data(self):
        """Test business-friendly formatting of resource data."""
        data = {
            'total_count': 5,
            'region': 'us-east-1',
            'resources': [
                {'resource_type': 'EC2', 'resource_id': 'i-123'},
                {'resource_type': 'EC2', 'resource_id': 'i-456'},
                {'resource_type': 'S3', 'resource_id': 'my-bucket'},
                {'resource_type': 'RDS', 'resource_id': 'my-db'},
                {'resource_type': 'RDS', 'resource_id': 'my-db-2'}
            ]
        }
        
        result = self.formatter._format_resource_data(data)
        
        self.assertIn('Found 5 resources in us-east-1', result)
        self.assertIn('EC2: 2 resources', result)
        self.assertIn('S3: 1 resources', result)
        self.assertIn('RDS: 2 resources', result)


if __name__ == '__main__':
    unittest.main()