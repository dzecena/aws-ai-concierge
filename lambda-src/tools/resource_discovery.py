"""
Resource discovery tools for AWS AI Concierge
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class ResourceDiscoveryHandler:
    """Handles AWS resource discovery and inventory."""
    
    def __init__(self, aws_clients):
        self.aws_clients = aws_clients
    
    def get_resource_inventory(self, params: Dict[str, Any], request_id: str) -> Dict[str, Any]:
        """
        Get inventory of AWS resources.
        
        Args:
            params: Parameters including resource_type, region
            request_id: Request ID for tracking
            
        Returns:
            Resource inventory results
        """
        logger.info(f"[{request_id}] Starting resource inventory with params: {params}")
        
        try:
            resource_type = params.get('resource_type', 'ALL')
            region = params.get('region', 'us-east-1')
            
            resources = []
            
            if resource_type in ['EC2', 'ALL']:
                ec2_resources = self._get_ec2_resources(region, request_id)
                resources.extend(ec2_resources)
            
            if resource_type in ['S3', 'ALL']:
                s3_resources = self._get_s3_resources(request_id)
                resources.extend(s3_resources)
            
            if resource_type in ['RDS', 'ALL']:
                rds_resources = self._get_rds_resources(region, request_id)
                resources.extend(rds_resources)
            
            if resource_type in ['LAMBDA', 'ALL']:
                lambda_resources = self._get_lambda_resources(region, request_id)
                resources.extend(lambda_resources)
            
            result = {
                'resource_type': resource_type,
                'region': region,
                'resources': resources,
                'total_count': len(resources),
                'inventory_date': datetime.utcnow().isoformat()
            }
            
            logger.info(f"[{request_id}] Found {len(resources)} resources")
            return result
            
        except ClientError as e:
            logger.error(f"[{request_id}] AWS error in resource inventory: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"[{request_id}] Error in resource inventory: {str(e)}")
            raise
    
    def get_resource_details(self, params: Dict[str, Any], request_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific resource.
        
        Args:
            params: Parameters including resource_id, resource_type, region
            request_id: Request ID for tracking
            
        Returns:
            Detailed resource information
        """
        logger.info(f"[{request_id}] Getting resource details with params: {params}")
        
        try:
            resource_id = params.get('resource_id')
            resource_type = params.get('resource_type')
            region = params.get('region', 'us-east-1')
            
            if not resource_id or not resource_type:
                raise ValueError("resource_id and resource_type are required")
            
            if resource_type == 'EC2':
                details = self._get_ec2_instance_details(resource_id, region, request_id)
            elif resource_type == 'S3':
                details = self._get_s3_bucket_details(resource_id, request_id)
            elif resource_type == 'RDS':
                details = self._get_rds_instance_details(resource_id, region, request_id)
            elif resource_type == 'LAMBDA':
                details = self._get_lambda_function_details(resource_id, region, request_id)
            else:
                raise ValueError(f"Unsupported resource type: {resource_type}")
            
            result = {
                'resource_id': resource_id,
                'resource_type': resource_type,
                'region': region,
                'details': details,
                'retrieved_at': datetime.utcnow().isoformat()
            }
            
            logger.info(f"[{request_id}] Retrieved details for {resource_type} {resource_id}")
            return result
            
        except ClientError as e:
            logger.error(f"[{request_id}] AWS error getting resource details: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"[{request_id}] Error getting resource details: {str(e)}")
            raise
    
    def _get_ec2_resources(self, region: str, request_id: str) -> List[Dict[str, Any]]:
        """Get EC2 instances in the specified region."""
        try:
            ec2_client = self.aws_clients.get_ec2_client(region)
            response = ec2_client.describe_instances()
            
            resources = []
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    resource = {
                        'resource_id': instance['InstanceId'],
                        'resource_type': 'EC2',
                        'name': self._get_resource_name(instance.get('Tags', [])),
                        'status': instance['State']['Name'],
                        'instance_type': instance['InstanceType'],
                        'launch_time': instance.get('LaunchTime', '').isoformat() if instance.get('LaunchTime') else None,
                        'region': region,
                        'availability_zone': instance.get('Placement', {}).get('AvailabilityZone'),
                        'tags': {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])},
                        'metadata': {
                            'vpc_id': instance.get('VpcId'),
                            'subnet_id': instance.get('SubnetId'),
                            'security_groups': [sg['GroupName'] for sg in instance.get('SecurityGroups', [])],
                            'public_ip': instance.get('PublicIpAddress'),
                            'private_ip': instance.get('PrivateIpAddress')
                        }
                    }
                    resources.append(resource)
            
            return resources
            
        except Exception as e:
            logger.warning(f"[{request_id}] Could not get EC2 resources in {region}: {str(e)}")
            return []
    
    def _get_s3_resources(self, request_id: str) -> List[Dict[str, Any]]:
        """Get S3 buckets (global service)."""
        try:
            s3_client = self.aws_clients.get_s3_client()
            response = s3_client.list_buckets()
            
            resources = []
            for bucket in response.get('Buckets', []):
                # Get bucket location
                try:
                    location_response = s3_client.get_bucket_location(Bucket=bucket['Name'])
                    region = location_response.get('LocationConstraint') or 'us-east-1'
                except:
                    region = 'unknown'
                
                resource = {
                    'resource_id': bucket['Name'],
                    'resource_type': 'S3',
                    'name': bucket['Name'],
                    'status': 'active',
                    'created_date': bucket.get('CreationDate', '').isoformat() if bucket.get('CreationDate') else None,
                    'region': region,
                    'tags': {},  # Would need separate API call to get tags
                    'metadata': {
                        'bucket_type': 'standard'
                    }
                }
                resources.append(resource)
            
            return resources
            
        except Exception as e:
            logger.warning(f"[{request_id}] Could not get S3 resources: {str(e)}")
            return []
    
    def _get_rds_resources(self, region: str, request_id: str) -> List[Dict[str, Any]]:
        """Get RDS instances in the specified region."""
        try:
            rds_client = self.aws_clients.get_rds_client(region)
            response = rds_client.describe_db_instances()
            
            resources = []
            for db_instance in response.get('DBInstances', []):
                resource = {
                    'resource_id': db_instance['DBInstanceIdentifier'],
                    'resource_type': 'RDS',
                    'name': db_instance['DBInstanceIdentifier'],
                    'status': db_instance['DBInstanceStatus'],
                    'engine': db_instance['Engine'],
                    'engine_version': db_instance['EngineVersion'],
                    'instance_class': db_instance['DBInstanceClass'],
                    'created_date': db_instance.get('InstanceCreateTime', '').isoformat() if db_instance.get('InstanceCreateTime') else None,
                    'region': region,
                    'availability_zone': db_instance.get('AvailabilityZone'),
                    'tags': {},  # Would need separate API call to get tags
                    'metadata': {
                        'allocated_storage': db_instance.get('AllocatedStorage'),
                        'storage_type': db_instance.get('StorageType'),
                        'multi_az': db_instance.get('MultiAZ'),
                        'publicly_accessible': db_instance.get('PubliclyAccessible'),
                        'vpc_id': db_instance.get('DBSubnetGroup', {}).get('VpcId')
                    }
                }
                resources.append(resource)
            
            return resources
            
        except Exception as e:
            logger.warning(f"[{request_id}] Could not get RDS resources in {region}: {str(e)}")
            return []
    
    def _get_lambda_resources(self, region: str, request_id: str) -> List[Dict[str, Any]]:
        """Get Lambda functions in the specified region."""
        try:
            lambda_client = self.aws_clients.get_lambda_client(region)
            response = lambda_client.list_functions()
            
            resources = []
            for function in response.get('Functions', []):
                resource = {
                    'resource_id': function['FunctionName'],
                    'resource_type': 'LAMBDA',
                    'name': function['FunctionName'],
                    'status': function.get('State', 'Active'),
                    'runtime': function['Runtime'],
                    'handler': function['Handler'],
                    'last_modified': function.get('LastModified'),
                    'region': region,
                    'tags': {},  # Would need separate API call to get tags
                    'metadata': {
                        'memory_size': function.get('MemorySize'),
                        'timeout': function.get('Timeout'),
                        'code_size': function.get('CodeSize'),
                        'role': function.get('Role'),
                        'vpc_config': function.get('VpcConfig')
                    }
                }
                resources.append(resource)
            
            return resources
            
        except Exception as e:
            logger.warning(f"[{request_id}] Could not get Lambda resources in {region}: {str(e)}")
            return []
    
    def _get_ec2_instance_details(self, instance_id: str, region: str, request_id: str) -> Dict[str, Any]:
        """Get detailed information about an EC2 instance."""
        ec2_client = self.aws_clients.get_ec2_client(region)
        response = ec2_client.describe_instances(InstanceIds=[instance_id])
        
        if not response['Reservations']:
            raise ValueError(f"Instance {instance_id} not found")
        
        instance = response['Reservations'][0]['Instances'][0]
        
        return {
            'instance_id': instance['InstanceId'],
            'instance_type': instance['InstanceType'],
            'state': instance['State'],
            'launch_time': instance.get('LaunchTime', '').isoformat() if instance.get('LaunchTime') else None,
            'placement': instance.get('Placement', {}),
            'security_groups': instance.get('SecurityGroups', []),
            'network_interfaces': instance.get('NetworkInterfaces', []),
            'block_device_mappings': instance.get('BlockDeviceMappings', []),
            'tags': {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])},
            'monitoring': instance.get('Monitoring', {}),
            'platform': instance.get('Platform'),
            'architecture': instance.get('Architecture'),
            'hypervisor': instance.get('Hypervisor'),
            'virtualization_type': instance.get('VirtualizationType')
        }
    
    def _get_s3_bucket_details(self, bucket_name: str, request_id: str) -> Dict[str, Any]:
        """Get detailed information about an S3 bucket."""
        s3_client = self.aws_clients.get_s3_client()
        
        details = {'bucket_name': bucket_name}
        
        try:
            # Get bucket location
            location_response = s3_client.get_bucket_location(Bucket=bucket_name)
            details['region'] = location_response.get('LocationConstraint') or 'us-east-1'
        except:
            details['region'] = 'unknown'
        
        try:
            # Get bucket versioning
            versioning_response = s3_client.get_bucket_versioning(Bucket=bucket_name)
            details['versioning'] = versioning_response.get('Status', 'Disabled')
        except:
            details['versioning'] = 'unknown'
        
        try:
            # Get bucket encryption
            encryption_response = s3_client.get_bucket_encryption(Bucket=bucket_name)
            details['encryption'] = encryption_response.get('ServerSideEncryptionConfiguration', {})
        except:
            details['encryption'] = 'none'
        
        return details
    
    def _get_rds_instance_details(self, db_identifier: str, region: str, request_id: str) -> Dict[str, Any]:
        """Get detailed information about an RDS instance."""
        rds_client = self.aws_clients.get_rds_client(region)
        response = rds_client.describe_db_instances(DBInstanceIdentifier=db_identifier)
        
        if not response['DBInstances']:
            raise ValueError(f"RDS instance {db_identifier} not found")
        
        db_instance = response['DBInstances'][0]
        return db_instance
    
    def _get_lambda_function_details(self, function_name: str, region: str, request_id: str) -> Dict[str, Any]:
        """Get detailed information about a Lambda function."""
        lambda_client = self.aws_clients.get_lambda_client(region)
        response = lambda_client.get_function(FunctionName=function_name)
        
        return response
    
    def _get_resource_name(self, tags: List[Dict[str, str]]) -> Optional[str]:
        """Extract resource name from tags."""
        for tag in tags:
            if tag.get('Key') == 'Name':
                return tag.get('Value')
        return None