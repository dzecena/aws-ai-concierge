"""
Unit tests for cost analysis functionality
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
from tools.cost_analysis import CostAnalysisHandler


class TestCostAnalysisHandler(unittest.TestCase):
    
    def setUp(self):
        self.mock_aws_clients = Mock()
        self.handler = CostAnalysisHandler(self.mock_aws_clients)
        self.request_id = "test-request-123"
    
    def test_get_cost_analysis_success(self):
        """Test successful cost analysis."""
        # Mock Cost Explorer client
        mock_ce_client = Mock()
        self.mock_aws_clients.get_cost_explorer_client.return_value = mock_ce_client
        
        # Mock Cost Explorer response
        mock_response = {
            'ResultsByTime': [
                {
                    'Groups': [
                        {
                            'Keys': ['EC2-Instance'],
                            'Metrics': {
                                'BlendedCost': {'Amount': '100.50', 'Unit': 'USD'},
                                'UsageQuantity': {'Amount': '720', 'Unit': 'Hrs'}
                            }
                        },
                        {
                            'Keys': ['S3'],
                            'Metrics': {
                                'BlendedCost': {'Amount': '25.75', 'Unit': 'USD'},
                                'UsageQuantity': {'Amount': '1000', 'Unit': 'GB'}
                            }
                        }
                    ]
                }
            ]
        }
        mock_ce_client.get_cost_and_usage.return_value = mock_response
        
        # Test parameters
        params = {
            'time_period': 'MONTHLY',
            'granularity': 'DAILY',
            'group_by': 'SERVICE'
        }
        
        # Execute
        result = self.handler.get_cost_analysis(params, self.request_id)
        
        # Verify
        self.assertEqual(result['total_cost'], 126.25)
        self.assertEqual(result['currency'], 'USD')
        self.assertEqual(result['time_period'], 'MONTHLY')
        self.assertEqual(len(result['breakdown']), 2)
        
        # Verify breakdown is sorted by cost (descending)
        self.assertEqual(result['breakdown'][0]['service_name'], 'EC2-Instance')
        self.assertEqual(result['breakdown'][0]['cost'], 100.50)
        self.assertEqual(result['breakdown'][1]['service_name'], 'S3')
        self.assertEqual(result['breakdown'][1]['cost'], 25.75)
    
    def test_get_cost_analysis_client_error(self):
        """Test cost analysis with AWS client error."""
        # Mock Cost Explorer client to raise error
        mock_ce_client = Mock()
        self.mock_aws_clients.get_cost_explorer_client.return_value = mock_ce_client
        
        mock_ce_client.get_cost_and_usage.side_effect = ClientError(
            error_response={'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
            operation_name='GetCostAndUsage'
        )
        
        params = {'time_period': 'MONTHLY'}
        
        # Should raise the ClientError
        with self.assertRaises(ClientError):
            self.handler.get_cost_analysis(params, self.request_id)
    
    def test_get_idle_resources_success(self):
        """Test successful idle resource detection."""
        # Mock EC2 client
        mock_ec2_client = Mock()
        self.mock_aws_clients.get_ec2_client.return_value = mock_ec2_client
        
        # Mock CloudWatch client
        mock_cw_client = Mock()
        self.mock_aws_clients.get_cloudwatch_client.return_value = mock_cw_client
        
        # Mock EC2 response
        mock_ec2_response = {
            'Reservations': [
                {
                    'Instances': [
                        {
                            'InstanceId': 'i-1234567890abcdef0',
                            'InstanceType': 't3.medium',
                            'State': {'Name': 'running'},
                            'LaunchTime': datetime.now() - timedelta(days=5),
                            'Tags': [{'Key': 'Name', 'Value': 'Test Instance'}]
                        }
                    ]
                }
            ]
        }
        mock_ec2_client.describe_instances.return_value = mock_ec2_response
        
        # Mock CloudWatch response (low CPU utilization)
        mock_cw_response = {
            'Datapoints': [
                {'Average': 2.5, 'Timestamp': datetime.now()},
                {'Average': 3.0, 'Timestamp': datetime.now()},
                {'Average': 1.8, 'Timestamp': datetime.now()}
            ]
        }
        mock_cw_client.get_metric_statistics.return_value = mock_cw_response
        
        # Test parameters
        params = {
            'region': 'us-east-1',
            'cpu_threshold': 5.0,
            'days': 7
        }
        
        # Execute
        result = self.handler.get_idle_resources(params, self.request_id)
        
        # Verify
        self.assertEqual(result['region'], 'us-east-1')
        self.assertEqual(result['total_idle_instances'], 1)
        self.assertEqual(len(result['idle_instances']), 1)
        
        idle_instance = result['idle_instances'][0]
        self.assertEqual(idle_instance['instance_id'], 'i-1234567890abcdef0')
        self.assertEqual(idle_instance['instance_type'], 't3.medium')
        self.assertLess(idle_instance['average_cpu_utilization'], 5.0)
        self.assertGreater(result['potential_monthly_savings'], 0)
    
    def test_get_idle_resources_no_idle_instances(self):
        """Test idle resource detection when no instances are idle."""
        # Mock EC2 client
        mock_ec2_client = Mock()
        self.mock_aws_clients.get_ec2_client.return_value = mock_ec2_client
        
        # Mock CloudWatch client
        mock_cw_client = Mock()
        self.mock_aws_clients.get_cloudwatch_client.return_value = mock_cw_client
        
        # Mock EC2 response
        mock_ec2_response = {
            'Reservations': [
                {
                    'Instances': [
                        {
                            'InstanceId': 'i-1234567890abcdef0',
                            'InstanceType': 't3.medium',
                            'State': {'Name': 'running'},
                            'LaunchTime': datetime.now() - timedelta(days=5),
                            'Tags': []
                        }
                    ]
                }
            ]
        }
        mock_ec2_client.describe_instances.return_value = mock_ec2_response
        
        # Mock CloudWatch response (high CPU utilization)
        mock_cw_response = {
            'Datapoints': [
                {'Average': 75.5, 'Timestamp': datetime.now()},
                {'Average': 80.0, 'Timestamp': datetime.now()},
                {'Average': 65.8, 'Timestamp': datetime.now()}
            ]
        }
        mock_cw_client.get_metric_statistics.return_value = mock_cw_response
        
        # Test parameters
        params = {
            'region': 'us-east-1',
            'cpu_threshold': 5.0,
            'days': 7
        }
        
        # Execute
        result = self.handler.get_idle_resources(params, self.request_id)
        
        # Verify
        self.assertEqual(result['total_idle_instances'], 0)
        self.assertEqual(len(result['idle_instances']), 0)
        self.assertEqual(result['potential_monthly_savings'], 0)
    
    def test_estimate_instance_cost(self):
        """Test instance cost estimation."""
        # Test known instance types
        self.assertEqual(self.handler._estimate_instance_cost('t3.medium'), 30.40)
        self.assertEqual(self.handler._estimate_instance_cost('m5.large'), 70.00)
        self.assertEqual(self.handler._estimate_instance_cost('c5.xlarge'), 124.00)
        
        # Test unknown instance type (should return default)
        self.assertEqual(self.handler._estimate_instance_cost('unknown.type'), 50.0)
    
    def test_get_average_cpu_utilization_no_data(self):
        """Test CPU utilization calculation when no data is available."""
        mock_cw_client = Mock()
        mock_cw_client.get_metric_statistics.return_value = {'Datapoints': []}
        
        result = self.handler._get_average_cpu_utilization(mock_cw_client, 'i-123', 7)
        
        self.assertIsNone(result)
    
    def test_get_average_cpu_utilization_with_data(self):
        """Test CPU utilization calculation with data."""
        mock_cw_client = Mock()
        mock_cw_response = {
            'Datapoints': [
                {'Average': 10.0},
                {'Average': 20.0},
                {'Average': 30.0}
            ]
        }
        mock_cw_client.get_metric_statistics.return_value = mock_cw_response
        
        result = self.handler._get_average_cpu_utilization(mock_cw_client, 'i-123', 7)
        
        self.assertEqual(result, 20.0)  # (10 + 20 + 30) / 3
    
    def test_process_cost_response_empty(self):
        """Test processing empty cost response."""
        empty_response = {'ResultsByTime': []}
        
        result = self.handler._process_cost_response(empty_response, 'MONTHLY', 'SERVICE')
        
        self.assertEqual(result['total_cost'], 0.0)
        self.assertEqual(result['currency'], 'USD')
        self.assertEqual(result['time_period'], 'MONTHLY')
        self.assertEqual(result['group_by'], 'SERVICE')
        self.assertEqual(len(result['breakdown']), 0)


if __name__ == '__main__':
    unittest.main()