"""
Unit tests for resource discovery functionality
"""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime
from botocore.exceptions import ClientError
from tools.resource_discovery import ResourceDiscoveryHandler


class TestResourceDiscoveryHandler(unittest.TestCase):
    
    def setUp(self):
        self.mock_aws_clients = Mock()
        self.handler = ResourceDiscoveryHandler(self.mock_aws_clients)
        self.request_id = "test-request-123"
    
    def test_get_resource_inventory_ec2_success(self):
        """Test successful EC2 resource inventory."""
        # Mock EC2 client
        mock_ec2_client = Mock()
        self.mock_aws_clients.get_ec2_client.return_value = mock_ec2_client
        
        # Mock EC2 response
        mock_ec2_response = {
            'Reservations': [
                {
                    'Instances': [
                        {
                            'InstanceId': 'i-1234567890abcdef0',
                            'InstanceType': 't3.medium',
                            'State': {'Name': 'running'},
                            'LaunchTime': datetime(2023, 1, 1, 12, 0, 0),
                            'Placement': {'AvailabilityZone': 'us-east-1a'},
                            'VpcId': 'vpc-12345',
                            'SubnetId': 'subnet-12345',
                            'SecurityGroups': [{'GroupName': 'default', 'GroupId': 'sg-12345'}],
                            'PublicIpAddress': '1.2.3.4',
                            'PrivateIpAddress': '10.0.1.100',
                            'Tags': [
                                {'Key': 'Name', 'Value': 'Test Instance'},
                                {'Key': 'Environment', 'Value': 'test'}
                            ]
                        }
                    ]
                }
            ]
        }
        mock_ec2_client.describe_instances.return_value = mock_ec2_response
        
        # Test parameters
        params = {
            'resource_type': 'EC2',
            'region': 'us-east-1'
        }
        
        # Execute
        result = self.handler.get_resource_inventory(params, self.request_id)
        
        # Verify
        self.assertEqual(result['resource_type'], 'EC2')
        self.assertEqual(result['region'], 'us-east-1')
        self.assertEqual(result['total_count'], 1)
        self.assertEqual(len(result['resources']), 1)
        
        resource = result['resources'][0]
        self.assertEqual(resource['resource_id'], 'i-1234567890abcdef0')
        self.assertEqual(resource['resource_type'], 'EC2')
        self.assertEqual(resource['name'], 'Test Instance')
        self.assertEqual(resource['status'], 'running')
        self.assertEqual(resource['instance_type'], 't3.medium')
        self.assertEqual(resource['availability_zone'], 'us-east-1a')
        self.assertEqual(resource['tags']['Name'], 'Test Instance')
        self.assertEqual(resource['tags']['Environment'], 'test')
    
    def test_get_resource_inventory_s3_success(self):
        """Test successful S3 resource inventory."""
        # Mock S3 client
        mock_s3_client = Mock()
        self.mock_aws_clients.get_s3_client.return_value = mock_s3_client
        
        # Mock S3 list buckets response
        mock_s3_response = {
            'Buckets': [
                {
                    'Name': 'my-test-bucket',
                    'CreationDate': datetime(2023, 1, 1, 12, 0, 0)
                },
                {
                    'Name': 'another-bucket',
                    'CreationDate': datetime(2023, 2, 1, 12, 0, 0)
                }
            ]
        }
        mock_s3_client.list_buckets.return_value = mock_s3_response
        
        # Mock bucket location responses
        mock_s3_client.get_bucket_location.side_effect = [
            {'LocationConstraint': 'us-west-2'},
            {'LocationConstraint': None}  # us-east-1 returns None
        ]
        
        # Test parameters
        params = {
            'resource_type': 'S3',
            'region': 'us-east-1'
        }
        
        # Execute
        result = self.handler.get_resource_inventory(params, self.request_id)
        
        # Verify
        self.assertEqual(result['resource_type'], 'S3')
        self.assertEqual(result['total_count'], 2)
        self.assertEqual(len(result['resources']), 2)
        
        # Check first bucket
        bucket1 = result['resources'][0]
        self.assertEqual(bucket1['resource_id'], 'my-test-bucket')
        self.assertEqual(bucket1['resource_type'], 'S3')
        self.assertEqual(bucket1['name'], 'my-test-bucket')
        self.assertEqual(bucket1['status'], 'active')
        self.assertEqual(bucket1['region'], 'us-west-2')
        
        # Check second bucket (us-east-1)
        bucket2 = result['resources'][1]
        self.assertEqual(bucket2['resource_id'], 'another-bucket')
        self.assertEqual(bucket2['region'], 'us-east-1')
    
    def test_get_resource_inventory_all_types(self):
        """Test resource inventory for all resource types."""
        # Mock all clients
        mock_ec2_client = Mock()
        mock_s3_client = Mock()
        mock_rds_client = Mock()
        mock_lambda_client = Mock()
        
        self.mock_aws_clients.get_ec2_client.return_value = mock_ec2_client
        self.mock_aws_clients.get_s3_client.return_value = mock_s3_client
        self.mock_aws_clients.get_rds_client.return_value = mock_rds_client
        self.mock_aws_clients.get_lambda_client.return_value = mock_lambda_client
        
        # Mock responses (empty for simplicity)
        mock_ec2_client.describe_instances.return_value = {'Reservations': []}
        mock_s3_client.list_buckets.return_value = {'Buckets': []}
        mock_rds_client.describe_db_instances.return_value = {'DBInstances': []}
        mock_lambda_client.list_functions.return_value = {'Functions': []}
        
        # Test parameters
        params = {
            'resource_type': 'ALL',
            'region': 'us-east-1'
        }
        
        # Execute
        result = self.handler.get_resource_inventory(params, self.request_id)
        
        # Verify all clients were called
        mock_ec2_client.describe_instances.assert_called_once()
        mock_s3_client.list_buckets.assert_called_once()
        mock_rds_client.describe_db_instances.assert_called_once()
        mock_lambda_client.list_functions.assert_called_once()
        
        self.assertEqual(result['resource_type'], 'ALL')
        self.assertEqual(result['total_count'], 0)
    
    def test_get_resource_details_ec2_success(self):
        """Test successful EC2 resource details retrieval."""
        # Mock EC2 client
        mock_ec2_client = Mock()
        self.mock_aws_clients.get_ec2_client.return_value = mock_ec2_client
        
        # Mock EC2 describe instances response
        mock_ec2_response = {
            'Reservations': [
                {
                    'Instances': [
                        {
                            'InstanceId': 'i-1234567890abcdef0',
                            'InstanceType': 't3.medium',
                            'State': {'Name': 'running', 'Code': 16},
                            'LaunchTime': datetime(2023, 1, 1, 12, 0, 0),
                            'Placement': {'AvailabilityZone': 'us-east-1a', 'GroupName': ''},
                            'SecurityGroups': [{'GroupName': 'default', 'GroupId': 'sg-12345'}],
                            'NetworkInterfaces': [],
                            'BlockDeviceMappings': [],
                            'Tags': [{'Key': 'Name', 'Value': 'Test Instance'}],
                            'Monitoring': {'State': 'disabled'},
                            'Architecture': 'x86_64',
                            'Hypervisor': 'xen',
                            'VirtualizationType': 'hvm'
                        }
                    ]
                }
            ]
        }
        mock_ec2_client.describe_instances.return_value = mock_ec2_response
        
        # Test parameters
        params = {
            'resource_id': 'i-1234567890abcdef0',
            'resource_type': 'EC2',
            'region': 'us-east-1'
        }
        
        # Execute
        result = self.handler.get_resource_details(params, self.request_id)
        
        # Verify
        self.assertEqual(result['resource_id'], 'i-1234567890abcdef0')
        self.assertEqual(result['resource_type'], 'EC2')
        self.assertEqual(result['region'], 'us-east-1')
        
        details = result['details']
        self.assertEqual(details['instance_id'], 'i-1234567890abcdef0')
        self.assertEqual(details['instance_type'], 't3.medium')
        self.assertEqual(details['state']['Name'], 'running')
        self.assertEqual(details['architecture'], 'x86_64')
    
    def test_get_resource_details_s3_success(self):
        """Test successful S3 resource details retrieval."""
        # Mock S3 client
        mock_s3_client = Mock()
        self.mock_aws_clients.get_s3_client.return_value = mock_s3_client
        
        # Mock S3 responses
        mock_s3_client.get_bucket_location.return_value = {'LocationConstraint': 'us-west-2'}
        mock_s3_client.get_bucket_versioning.return_value = {'Status': 'Enabled'}
        mock_s3_client.get_bucket_encryption.return_value = {
            'ServerSideEncryptionConfiguration': {
                'Rules': [{'ApplyServerSideEncryptionByDefault': {'SSEAlgorithm': 'AES256'}}]
            }
        }
        
        # Test parameters
        params = {
            'resource_id': 'my-test-bucket',
            'resource_type': 'S3',
            'region': 'us-east-1'
        }
        
        # Execute
        result = self.handler.get_resource_details(params, self.request_id)
        
        # Verify
        self.assertEqual(result['resource_id'], 'my-test-bucket')
        self.assertEqual(result['resource_type'], 'S3')
        
        details = result['details']
        self.assertEqual(details['bucket_name'], 'my-test-bucket')
        self.assertEqual(details['region'], 'us-west-2')
        self.assertEqual(details['versioning'], 'Enabled')
        self.assertIn('ServerSideEncryptionConfiguration', details['encryption'])
    
    def test_get_resource_details_missing_parameters(self):
        """Test resource details with missing parameters."""
        # Test missing resource_id
        params = {
            'resource_type': 'EC2',
            'region': 'us-east-1'
        }
        
        with self.assertRaises(ValueError) as context:
            self.handler.get_resource_details(params, self.request_id)
        
        self.assertIn("resource_id and resource_type are required", str(context.exception))
        
        # Test missing resource_type
        params = {
            'resource_id': 'i-123',
            'region': 'us-east-1'
        }
        
        with self.assertRaises(ValueError) as context:
            self.handler.get_resource_details(params, self.request_id)
        
        self.assertIn("resource_id and resource_type are required", str(context.exception))
    
    def test_get_resource_details_unsupported_type(self):
        """Test resource details with unsupported resource type."""
        params = {
            'resource_id': 'test-resource',
            'resource_type': 'UNSUPPORTED',
            'region': 'us-east-1'
        }
        
        with self.assertRaises(ValueError) as context:
            self.handler.get_resource_details(params, self.request_id)
        
        self.assertIn("Unsupported resource type: UNSUPPORTED", str(context.exception))
    
    def test_get_resource_details_not_found(self):
        """Test resource details when resource is not found."""
        # Mock EC2 client
        mock_ec2_client = Mock()
        self.mock_aws_clients.get_ec2_client.return_value = mock_ec2_client
        
        # Mock empty response
        mock_ec2_client.describe_instances.return_value = {'Reservations': []}
        
        params = {
            'resource_id': 'i-nonexistent',
            'resource_type': 'EC2',
            'region': 'us-east-1'
        }
        
        with self.assertRaises(ValueError) as context:
            self.handler.get_resource_details(params, self.request_id)
        
        self.assertIn("Instance i-nonexistent not found", str(context.exception))
    
    def test_get_resource_name_from_tags(self):
        """Test extracting resource name from tags."""
        # Test with Name tag
        tags = [
            {'Key': 'Environment', 'Value': 'prod'},
            {'Key': 'Name', 'Value': 'My Resource'},
            {'Key': 'Owner', 'Value': 'team'}
        ]
        name = self.handler._get_resource_name(tags)
        self.assertEqual(name, 'My Resource')
        
        # Test without Name tag
        tags = [
            {'Key': 'Environment', 'Value': 'prod'},
            {'Key': 'Owner', 'Value': 'team'}
        ]
        name = self.handler._get_resource_name(tags)
        self.assertIsNone(name)
        
        # Test empty tags
        name = self.handler._get_resource_name([])
        self.assertIsNone(name)
    
    def test_get_rds_resources_success(self):
        """Test successful RDS resource discovery."""
        # Mock RDS client
        mock_rds_client = Mock()
        self.mock_aws_clients.get_rds_client.return_value = mock_rds_client
        
        # Mock RDS response
        mock_rds_response = {
            'DBInstances': [
                {
                    'DBInstanceIdentifier': 'my-database',
                    'DBInstanceStatus': 'available',
                    'Engine': 'mysql',
                    'EngineVersion': '8.0.35',
                    'DBInstanceClass': 'db.t3.micro',
                    'InstanceCreateTime': datetime(2023, 1, 1, 12, 0, 0),
                    'AvailabilityZone': 'us-east-1a',
                    'AllocatedStorage': 20,
                    'StorageType': 'gp2',
                    'MultiAZ': False,
                    'PubliclyAccessible': False,
                    'DBSubnetGroup': {'VpcId': 'vpc-12345'}
                }
            ]
        }
        mock_rds_client.describe_db_instances.return_value = mock_rds_response
        
        # Execute
        resources = self.handler._get_rds_resources('us-east-1', self.request_id)
        
        # Verify
        self.assertEqual(len(resources), 1)
        resource = resources[0]
        self.assertEqual(resource['resource_id'], 'my-database')
        self.assertEqual(resource['resource_type'], 'RDS')
        self.assertEqual(resource['status'], 'available')
        self.assertEqual(resource['engine'], 'mysql')
        self.assertEqual(resource['instance_class'], 'db.t3.micro')
        self.assertEqual(resource['metadata']['allocated_storage'], 20)
        self.assertEqual(resource['metadata']['multi_az'], False)
    
    def test_get_lambda_resources_success(self):
        """Test successful Lambda resource discovery."""
        # Mock Lambda client
        mock_lambda_client = Mock()
        self.mock_aws_clients.get_lambda_client.return_value = mock_lambda_client
        
        # Mock Lambda response
        mock_lambda_response = {
            'Functions': [
                {
                    'FunctionName': 'my-function',
                    'Runtime': 'python3.9',
                    'Handler': 'index.handler',
                    'State': 'Active',
                    'LastModified': '2023-01-01T12:00:00.000+0000',
                    'MemorySize': 128,
                    'Timeout': 30,
                    'CodeSize': 1024,
                    'Role': 'arn:aws:iam::123456789012:role/lambda-role',
                    'VpcConfig': {}
                }
            ]
        }
        mock_lambda_client.list_functions.return_value = mock_lambda_response
        
        # Execute
        resources = self.handler._get_lambda_resources('us-east-1', self.request_id)
        
        # Verify
        self.assertEqual(len(resources), 1)
        resource = resources[0]
        self.assertEqual(resource['resource_id'], 'my-function')
        self.assertEqual(resource['resource_type'], 'LAMBDA')
        self.assertEqual(resource['status'], 'Active')
        self.assertEqual(resource['runtime'], 'python3.9')
        self.assertEqual(resource['handler'], 'index.handler')
        self.assertEqual(resource['metadata']['memory_size'], 128)
        self.assertEqual(resource['metadata']['timeout'], 30)
    
    def test_resource_inventory_client_error(self):
        """Test resource inventory with AWS client error."""
        # Mock EC2 client to raise error
        mock_ec2_client = Mock()
        self.mock_aws_clients.get_ec2_client.return_value = mock_ec2_client
        
        mock_ec2_client.describe_instances.side_effect = ClientError(
            error_response={'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
            operation_name='DescribeInstances'
        )
        
        params = {
            'resource_type': 'EC2',
            'region': 'us-east-1'
        }
        
        # Should raise the ClientError
        with self.assertRaises(ClientError):
            self.handler.get_resource_inventory(params, self.request_id)


if __name__ == '__main__':
    unittest.main()