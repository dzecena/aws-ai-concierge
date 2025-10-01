"""
AWS client management utilities for AWS AI Concierge
"""

import boto3
import logging
import time
from typing import Dict, Any, Optional, Callable
from botocore.config import Config
from botocore.exceptions import ClientError
from functools import lru_cache

logger = logging.getLogger(__name__)


class AWSClientManager:
    """Manages AWS service clients with proper configuration and retry logic."""
    
    def __init__(self):
        # Configure boto3 with retry logic
        self.config = Config(
            retries={
                'max_attempts': 3,
                'mode': 'adaptive'
            },
            max_pool_connections=50
        )
        
        # Cache for clients to avoid recreating them
        self._clients = {}
    
    @lru_cache(maxsize=32)
    def get_client(self, service_name: str, region: Optional[str] = None) -> Any:
        """
        Get or create an AWS service client.
        
        Args:
            service_name: AWS service name (e.g., 'ec2', 's3', 'ce')
            region: AWS region (optional, uses default if not specified)
            
        Returns:
            Boto3 client for the specified service
        """
        client_key = f"{service_name}_{region or 'default'}"
        
        if client_key not in self._clients:
            try:
                if region:
                    client = boto3.client(
                        service_name,
                        region_name=region,
                        config=self.config
                    )
                else:
                    client = boto3.client(
                        service_name,
                        config=self.config
                    )
                
                self._clients[client_key] = client
                logger.debug(f"Created {service_name} client for region {region or 'default'}")
                
            except Exception as e:
                logger.error(f"Failed to create {service_name} client: {str(e)}")
                raise
        
        return self._clients[client_key]
    
    def get_cost_explorer_client(self) -> Any:
        """Get Cost Explorer client (always us-east-1)."""
        return self.get_client('ce', 'us-east-1')
    
    def get_ec2_client(self, region: str) -> Any:
        """Get EC2 client for specified region."""
        return self.get_client('ec2', region)
    
    def get_s3_client(self, region: Optional[str] = None) -> Any:
        """Get S3 client."""
        return self.get_client('s3', region)
    
    def get_cloudwatch_client(self, region: str) -> Any:
        """Get CloudWatch client for specified region."""
        return self.get_client('cloudwatch', region)
    
    def get_iam_client(self) -> Any:
        """Get IAM client (global service)."""
        return self.get_client('iam')
    
    def get_rds_client(self, region: str) -> Any:
        """Get RDS client for specified region."""
        return self.get_client('rds', region)
    
    def get_lambda_client(self, region: str) -> Any:
        """Get Lambda client for specified region."""
        return self.get_client('lambda', region)
    
    def get_support_client(self) -> Any:
        """Get Support client (us-east-1 only)."""
        return self.get_client('support', 'us-east-1')
    
    def get_organizations_client(self) -> Any:
        """Get Organizations client (global service)."""
        return self.get_client('organizations')
    
    def get_available_regions(self, service_name: str) -> list:
        """
        Get list of available regions for a service.
        
        Args:
            service_name: AWS service name
            
        Returns:
            List of region names
        """
        try:
            session = boto3.Session()
            return session.get_available_regions(service_name)
        except Exception as e:
            logger.error(f"Failed to get regions for {service_name}: {str(e)}")
            # Return common regions as fallback
            return [
                'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
                'eu-west-1', 'eu-west-2', 'eu-central-1',
                'ap-southeast-1', 'ap-southeast-2', 'ap-northeast-1'
            ]
    
    def test_client_permissions(self, service_name: str, region: Optional[str] = None) -> Dict[str, Any]:
        """
        Test if the client has basic permissions for a service.
        
        Args:
            service_name: AWS service name
            region: AWS region (optional)
            
        Returns:
            Dictionary with test results
        """
        try:
            client = self.get_client(service_name, region)
            
            # Service-specific permission tests
            if service_name == 'ec2':
                client.describe_regions()
            elif service_name == 's3':
                client.list_buckets()
            elif service_name == 'ce':
                # Cost Explorer requires specific date range
                from datetime import datetime, timedelta
                end_date = datetime.now().date()
                start_date = end_date - timedelta(days=1)
                client.get_cost_and_usage(
                    TimePeriod={
                        'Start': start_date.strftime('%Y-%m-%d'),
                        'End': end_date.strftime('%Y-%m-%d')
                    },
                    Granularity='DAILY',
                    Metrics=['BlendedCost']
                )
            elif service_name == 'cloudwatch':
                client.list_metrics(MaxRecords=1)
            elif service_name == 'iam':
                client.get_account_summary()
            
            return {
                'service': service_name,
                'region': region,
                'has_permissions': True,
                'error': None
            }
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            return {
                'service': service_name,
                'region': region,
                'has_permissions': False,
                'error': error_code,
                'message': str(e)
            }
        except Exception as e:
            return {
                'service': service_name,
                'region': region,
                'has_permissions': False,
                'error': 'UnknownError',
                'message': str(e)
            }
    
    def make_api_call(self, client: Any, operation: str, request_id: str, **kwargs) -> Any:
        """
        Make an AWS API call with audit logging.
        
        Args:
            client: Boto3 client
            operation: API operation name
            request_id: Request ID for tracking
            **kwargs: API call parameters
            
        Returns:
            API response
        """
        # Import here to avoid circular imports
        from utils.audit_logger import AuditLogger
        audit_logger = AuditLogger()
        
        service_name = client._service_model.service_name
        region = client.meta.region_name if hasattr(client, 'meta') and hasattr(client.meta, 'region_name') else None
        
        try:
            # Make the API call
            start_time = time.time()
            method = getattr(client, operation)
            response = method(**kwargs)
            
            # Calculate response size (approximate)
            response_size = len(str(response).encode('utf-8')) if response else 0
            
            # Log successful API call
            audit_logger.log_aws_api_call(
                request_id=request_id,
                service=service_name,
                operation=operation,
                region=region,
                success=True,
                response_size_bytes=response_size
            )
            
            return response
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            
            # Log failed API call
            audit_logger.log_aws_api_call(
                request_id=request_id,
                service=service_name,
                operation=operation,
                region=region,
                success=False,
                error_code=error_code
            )
            
            raise
        except Exception as e:
            # Log failed API call
            audit_logger.log_aws_api_call(
                request_id=request_id,
                service=service_name,
                operation=operation,
                region=region,
                success=False,
                error_code='UnknownError'
            )
            
            raise
    
    def clear_client_cache(self):
        """Clear the client cache (useful for testing)."""
        self._clients.clear()
        self.get_client.cache_clear()
        logger.info("Cleared AWS client cache")