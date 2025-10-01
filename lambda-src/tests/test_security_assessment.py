"""
Unit tests for security assessment functionality
"""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime
from botocore.exceptions import ClientError
from tools.security_assessment import SecurityAssessmentHandler


class TestSecurityAssessmentHandler(unittest.TestCase):
    
    def setUp(self):
        self.mock_aws_clients = Mock()
        self.handler = SecurityAssessmentHandler(self.mock_aws_clients)
        self.request_id = "test-request-123"
    
    def test_get_security_assessment_basic_success(self):
        """Test successful basic security assessment."""
        # Mock EC2 client for security groups
        mock_ec2_client = Mock()
        self.mock_aws_clients.get_ec2_client.return_value = mock_ec2_client
        
        # Mock S3 client for public access
        mock_s3_client = Mock()
        self.mock_aws_clients.get_s3_client.return_value = mock_s3_client
        
        # Mock security groups response with open access
        mock_sg_response = {
            'SecurityGroups': [
                {
                    'GroupId': 'sg-12345',
                    'GroupName': 'test-sg',
                    'IpPermissions': [
                        {
                            'FromPort': 22,
                            'ToPort': 22,
                            'IpProtocol': 'tcp',
                            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                        }
                    ]
                }
            ]
        }
        mock_ec2_client.describe_security_groups.return_value = mock_sg_response
        
        # Mock S3 buckets response
        mock_s3_response = {
            'Buckets': [
                {'Name': 'test-bucket', 'CreationDate': datetime.now()}
            ]
        }
        mock_s3_client.list_buckets.return_value = mock_s3_response
        
        # Mock public access block response (not configured)
        mock_s3_client.get_public_access_block.side_effect = ClientError(
            error_response={'Error': {'Code': 'NoSuchPublicAccessBlockConfiguration'}},
            operation_name='GetPublicAccessBlock'
        )
        
        # Test parameters
        params = {
            'region': 'us-east-1',
            'assessment_type': 'BASIC'
        }
        
        # Execute
        result = self.handler.get_security_assessment(params, self.request_id)
        
        # Verify
        self.assertEqual(result['region'], 'us-east-1')
        self.assertEqual(result['assessment_type'], 'BASIC')
        self.assertEqual(result['total_findings'], 2)  # 1 SG + 1 S3
        self.assertGreater(result['risk_score'], 0)
        self.assertGreater(len(result['recommendations']), 0)
        
        # Check security group finding
        sg_findings = [f for f in result['findings'] if f['resource_type'] == 'SecurityGroup']
        self.assertEqual(len(sg_findings), 1)
        self.assertEqual(sg_findings[0]['severity'], 'HIGH')  # SSH port 22 is high severity
        self.assertIn('public access on port 22', sg_findings[0]['title'])
        
        # Check S3 finding
        s3_findings = [f for f in result['findings'] if f['resource_type'] == 'S3Bucket']
        self.assertEqual(len(s3_findings), 1)
        self.assertEqual(s3_findings[0]['severity'], 'MEDIUM')
        self.assertIn('no public access block', s3_findings[0]['title'])
    
    def test_get_security_assessment_comprehensive(self):
        """Test comprehensive security assessment with IAM checks."""
        # Mock all clients
        mock_ec2_client = Mock()
        mock_s3_client = Mock()
        mock_iam_client = Mock()
        
        self.mock_aws_clients.get_ec2_client.return_value = mock_ec2_client
        self.mock_aws_clients.get_s3_client.return_value = mock_s3_client
        self.mock_aws_clients.get_iam_client.return_value = mock_iam_client
        
        # Mock empty responses for EC2 and S3
        mock_ec2_client.describe_security_groups.return_value = {'SecurityGroups': []}
        mock_s3_client.list_buckets.return_value = {'Buckets': []}
        
        # Mock IAM response with admin user
        mock_iam_response = {
            'Users': [
                {'UserName': 'admin-user'}
            ]
        }
        mock_iam_client.list_users.return_value = mock_iam_response
        
        mock_policies_response = {
            'AttachedPolicies': [
                {
                    'PolicyName': 'AdministratorAccess',
                    'PolicyArn': 'arn:aws:iam::aws:policy/AdministratorAccess'
                }
            ]
        }
        mock_iam_client.list_attached_user_policies.return_value = mock_policies_response
        
        # Test parameters
        params = {
            'region': 'us-east-1',
            'assessment_type': 'COMPREHENSIVE'
        }
        
        # Execute
        result = self.handler.get_security_assessment(params, self.request_id)
        
        # Verify IAM check was performed
        mock_iam_client.list_users.assert_called_once()
        mock_iam_client.list_attached_user_policies.assert_called_once_with(UserName='admin-user')
        
        # Check IAM finding
        iam_findings = [f for f in result['findings'] if f['resource_type'] == 'IAMUser']
        self.assertEqual(len(iam_findings), 1)
        self.assertEqual(iam_findings[0]['severity'], 'HIGH')
        self.assertIn('administrative access', iam_findings[0]['title'])
    
    def test_check_encryption_status_s3_success(self):
        """Test successful S3 encryption status check."""
        # Mock S3 client
        mock_s3_client = Mock()
        self.mock_aws_clients.get_s3_client.return_value = mock_s3_client
        
        # Mock S3 buckets response
        mock_s3_response = {
            'Buckets': [
                {'Name': 'encrypted-bucket', 'CreationDate': datetime.now()},
                {'Name': 'unencrypted-bucket', 'CreationDate': datetime.now()}
            ]
        }
        mock_s3_client.list_buckets.return_value = mock_s3_response
        
        # Mock encryption responses
        def mock_get_encryption(Bucket):
            if Bucket == 'encrypted-bucket':
                return {
                    'ServerSideEncryptionConfiguration': {
                        'Rules': [{'ApplyServerSideEncryptionByDefault': {'SSEAlgorithm': 'AES256'}}]
                    }
                }
            else:
                raise ClientError(
                    error_response={'Error': {'Code': 'ServerSideEncryptionConfigurationNotFoundError'}},
                    operation_name='GetBucketEncryption'
                )
        
        mock_s3_client.get_bucket_encryption.side_effect = mock_get_encryption
        
        # Test parameters
        params = {
            'resource_type': 'S3',
            'region': 'us-east-1'
        }
        
        # Execute
        result = self.handler.check_encryption_status(params, self.request_id)
        
        # Verify
        self.assertEqual(result['resource_type'], 'S3')
        self.assertEqual(result['total_resources'], 2)
        self.assertEqual(result['encrypted_resources'], 1)
        self.assertEqual(result['compliance_percentage'], 50.0)
        
        # Check individual bucket status
        encrypted_bucket = next(r for r in result['encryption_status'] if r['resource_id'] == 'encrypted-bucket')
        self.assertTrue(encrypted_bucket['encrypted'])
        self.assertEqual(encrypted_bucket['encryption_type'], 'server-side')
        
        unencrypted_bucket = next(r for r in result['encryption_status'] if r['resource_id'] == 'unencrypted-bucket')
        self.assertFalse(unencrypted_bucket['encrypted'])
        self.assertEqual(unencrypted_bucket['encryption_type'], 'none')
    
    def test_check_encryption_status_ebs_success(self):
        """Test successful EBS encryption status check."""
        # Mock EC2 client
        mock_ec2_client = Mock()
        self.mock_aws_clients.get_ec2_client.return_value = mock_ec2_client
        
        # Mock EBS volumes response
        mock_ebs_response = {
            'Volumes': [
                {
                    'VolumeId': 'vol-encrypted',
                    'Encrypted': True,
                    'KmsKeyId': 'arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012'
                },
                {
                    'VolumeId': 'vol-unencrypted',
                    'Encrypted': False
                }
            ]
        }
        mock_ec2_client.describe_volumes.return_value = mock_ebs_response
        
        # Test parameters
        params = {
            'resource_type': 'EBS',
            'region': 'us-east-1'
        }
        
        # Execute
        result = self.handler.check_encryption_status(params, self.request_id)
        
        # Verify
        self.assertEqual(result['total_resources'], 2)
        self.assertEqual(result['encrypted_resources'], 1)
        self.assertEqual(result['compliance_percentage'], 50.0)
        
        # Check individual volume status
        encrypted_volume = next(r for r in result['encryption_status'] if r['resource_id'] == 'vol-encrypted')
        self.assertTrue(encrypted_volume['encrypted'])
        self.assertEqual(encrypted_volume['encryption_type'], 'ebs')
        self.assertIsNotNone(encrypted_volume['encryption_details']['kms_key_id'])
        
        unencrypted_volume = next(r for r in result['encryption_status'] if r['resource_id'] == 'vol-unencrypted')
        self.assertFalse(unencrypted_volume['encrypted'])
        self.assertEqual(unencrypted_volume['encryption_type'], 'none')
    
    def test_check_encryption_status_rds_success(self):
        """Test successful RDS encryption status check."""
        # Mock RDS client
        mock_rds_client = Mock()
        self.mock_aws_clients.get_rds_client.return_value = mock_rds_client
        
        # Mock RDS instances response
        mock_rds_response = {
            'DBInstances': [
                {
                    'DBInstanceIdentifier': 'encrypted-db',
                    'StorageEncrypted': True,
                    'KmsKeyId': 'arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012'
                },
                {
                    'DBInstanceIdentifier': 'unencrypted-db',
                    'StorageEncrypted': False
                }
            ]
        }
        mock_rds_client.describe_db_instances.return_value = mock_rds_response
        
        # Test parameters
        params = {
            'resource_type': 'RDS',
            'region': 'us-east-1'
        }
        
        # Execute
        result = self.handler.check_encryption_status(params, self.request_id)
        
        # Verify
        self.assertEqual(result['total_resources'], 2)
        self.assertEqual(result['encrypted_resources'], 1)
        self.assertEqual(result['compliance_percentage'], 50.0)
        
        # Check individual DB status
        encrypted_db = next(r for r in result['encryption_status'] if r['resource_id'] == 'encrypted-db')
        self.assertTrue(encrypted_db['encrypted'])
        self.assertEqual(encrypted_db['encryption_type'], 'rds')
        
        unencrypted_db = next(r for r in result['encryption_status'] if r['resource_id'] == 'unencrypted-db')
        self.assertFalse(unencrypted_db['encrypted'])
        self.assertEqual(unencrypted_db['encryption_type'], 'none')
    
    def test_check_encryption_status_all_types(self):
        """Test encryption status check for all resource types."""
        # Mock all clients
        mock_s3_client = Mock()
        mock_ec2_client = Mock()
        mock_rds_client = Mock()
        
        self.mock_aws_clients.get_s3_client.return_value = mock_s3_client
        self.mock_aws_clients.get_ec2_client.return_value = mock_ec2_client
        self.mock_aws_clients.get_rds_client.return_value = mock_rds_client
        
        # Mock empty responses
        mock_s3_client.list_buckets.return_value = {'Buckets': []}
        mock_ec2_client.describe_volumes.return_value = {'Volumes': []}
        mock_rds_client.describe_db_instances.return_value = {'DBInstances': []}
        
        # Test parameters
        params = {
            'resource_type': 'ALL',
            'region': 'us-east-1'
        }
        
        # Execute
        result = self.handler.check_encryption_status(params, self.request_id)
        
        # Verify all clients were called
        mock_s3_client.list_buckets.assert_called_once()
        mock_ec2_client.describe_volumes.assert_called_once()
        mock_rds_client.describe_db_instances.assert_called_once()
        
        self.assertEqual(result['resource_type'], 'ALL')
        self.assertEqual(result['total_resources'], 0)
        self.assertEqual(result['compliance_percentage'], 100)  # 100% when no resources
    
    def test_calculate_risk_score(self):
        """Test risk score calculation."""
        # Test with no findings
        self.assertEqual(self.handler._calculate_risk_score([]), 0)
        
        # Test with mixed severity findings
        findings = [
            {'severity': 'HIGH'},
            {'severity': 'HIGH'},
            {'severity': 'MEDIUM'},
            {'severity': 'LOW'},
            {'severity': 'LOW'}
        ]
        expected_score = 30 + 30 + 15 + 5 + 5  # 85
        self.assertEqual(self.handler._calculate_risk_score(findings), 85)
        
        # Test score capping at 100
        high_findings = [{'severity': 'HIGH'} for _ in range(10)]  # Would be 300
        self.assertEqual(self.handler._calculate_risk_score(high_findings), 100)
    
    def test_generate_security_recommendations(self):
        """Test security recommendation generation."""
        # Test with no findings
        recommendations = self.handler._generate_security_recommendations([])
        self.assertIn("No security issues found", recommendations[0])
        
        # Test with high severity findings
        findings = [
            {'severity': 'HIGH', 'resource_type': 'SecurityGroup'},
            {'severity': 'MEDIUM', 'resource_type': 'S3Bucket'},
            {'severity': 'HIGH', 'resource_type': 'IAMUser'}
        ]
        recommendations = self.handler._generate_security_recommendations(findings)
        
        self.assertIn("2 high-severity security issues", recommendations[0])
        self.assertIn("1 medium-severity security issues", recommendations[1])
        self.assertIn("security group rules", recommendations[2])
        self.assertIn("S3 public access blocks", recommendations[3])
        self.assertIn("IAM user permissions", recommendations[4])
    
    def test_check_security_groups_no_issues(self):
        """Test security group check with no issues."""
        # Mock EC2 client
        mock_ec2_client = Mock()
        self.mock_aws_clients.get_ec2_client.return_value = mock_ec2_client
        
        # Mock security groups response with restricted access
        mock_sg_response = {
            'SecurityGroups': [
                {
                    'GroupId': 'sg-12345',
                    'GroupName': 'secure-sg',
                    'IpPermissions': [
                        {
                            'FromPort': 80,
                            'ToPort': 80,
                            'IpProtocol': 'tcp',
                            'IpRanges': [{'CidrIp': '10.0.0.0/8'}]  # Private IP range
                        }
                    ]
                }
            ]
        }
        mock_ec2_client.describe_security_groups.return_value = mock_sg_response
        
        # Execute
        findings = self.handler._check_security_groups('us-east-1', self.request_id)
        
        # Verify no findings for private IP ranges
        self.assertEqual(len(findings), 0)
    
    def test_check_s3_public_access_configured(self):
        """Test S3 public access check with properly configured buckets."""
        # Mock S3 client
        mock_s3_client = Mock()
        self.mock_aws_clients.get_s3_client.return_value = mock_s3_client
        
        # Mock S3 buckets response
        mock_s3_response = {
            'Buckets': [
                {'Name': 'secure-bucket', 'CreationDate': datetime.now()}
            ]
        }
        mock_s3_client.list_buckets.return_value = mock_s3_response
        
        # Mock properly configured public access block
        mock_public_access_response = {
            'PublicAccessBlockConfiguration': {
                'BlockPublicAcls': True,
                'IgnorePublicAcls': True,
                'BlockPublicPolicy': True,
                'RestrictPublicBuckets': True
            }
        }
        mock_s3_client.get_public_access_block.return_value = mock_public_access_response
        
        # Execute
        findings = self.handler._check_s3_public_access(self.request_id)
        
        # Verify no findings for properly configured bucket
        self.assertEqual(len(findings), 0)
    
    def test_security_assessment_client_error(self):
        """Test security assessment with AWS client error."""
        # Mock EC2 client to raise error
        mock_ec2_client = Mock()
        self.mock_aws_clients.get_ec2_client.return_value = mock_ec2_client
        
        mock_ec2_client.describe_security_groups.side_effect = ClientError(
            error_response={'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
            operation_name='DescribeSecurityGroups'
        )
        
        params = {
            'region': 'us-east-1',
            'assessment_type': 'BASIC'
        }
        
        # Should raise the ClientError
        with self.assertRaises(ClientError):
            self.handler.get_security_assessment(params, self.request_id)
    
    def test_encryption_status_client_error(self):
        """Test encryption status check with AWS client error."""
        # Mock S3 client to raise error
        mock_s3_client = Mock()
        self.mock_aws_clients.get_s3_client.return_value = mock_s3_client
        
        mock_s3_client.list_buckets.side_effect = ClientError(
            error_response={'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
            operation_name='ListBuckets'
        )
        
        params = {
            'resource_type': 'S3',
            'region': 'us-east-1'
        }
        
        # Should raise the ClientError
        with self.assertRaises(ClientError):
            self.handler.check_encryption_status(params, self.request_id)


if __name__ == '__main__':
    unittest.main()