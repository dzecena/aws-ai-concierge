"""
Security assessment tools for AWS AI Concierge
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from botocore.exceptions import ClientError
from utils.audit_logger import AuditLogger

logger = logging.getLogger(__name__)


class SecurityAssessmentHandler:
    """Handles security assessment and compliance checks."""
    
    def __init__(self, aws_clients):
        self.aws_clients = aws_clients
        self.audit_logger = AuditLogger()
    
    def get_security_assessment(self, params: Dict[str, Any], request_id: str) -> Dict[str, Any]:
        """
        Perform security assessment of AWS resources.
        
        Args:
            params: Parameters including region, assessment_type
            request_id: Request ID for tracking
            
        Returns:
            Security assessment results
        """
        logger.info(f"[{request_id}] Starting security assessment with params: {params}")
        
        try:
            region = params.get('region', 'us-east-1')
            assessment_type = params.get('assessment_type', 'BASIC')
            
            findings = []
            
            # Check security groups
            sg_findings = self._check_security_groups(region, request_id)
            findings.extend(sg_findings)
            
            # Check S3 bucket public access
            s3_findings = self._check_s3_public_access(request_id)
            findings.extend(s3_findings)
            
            if assessment_type == 'COMPREHENSIVE':
                # Additional checks for comprehensive assessment
                iam_findings = self._check_iam_policies(request_id)
                findings.extend(iam_findings)
            
            # Calculate risk score
            risk_score = self._calculate_risk_score(findings)
            
            # Generate recommendations
            recommendations = self._generate_security_recommendations(findings)
            
            result = {
                'region': region,
                'assessment_type': assessment_type,
                'findings': findings,
                'total_findings': len(findings),
                'risk_score': risk_score,
                'recommendations': recommendations,
                'assessment_date': datetime.utcnow().isoformat()
            }
            
            # Log security assessment activity
            self.audit_logger.log_security_check(
                request_id=request_id,
                check_type=assessment_type,
                resource_id=region,
                findings_count=len(findings),
                risk_score=risk_score
            )
            
            logger.info(f"[{request_id}] Security assessment completed with {len(findings)} findings")
            return result
            
        except ClientError as e:
            logger.error(f"[{request_id}] AWS error in security assessment: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"[{request_id}] Error in security assessment: {str(e)}")
            raise
    
    def check_encryption_status(self, params: Dict[str, Any], request_id: str) -> Dict[str, Any]:
        """
        Check encryption status of storage resources.
        
        Args:
            params: Parameters including resource_type, region
            request_id: Request ID for tracking
            
        Returns:
            Encryption status results
        """
        logger.info(f"[{request_id}] Checking encryption status with params: {params}")
        
        try:
            resource_type = params.get('resource_type', 'ALL')
            region = params.get('region', 'us-east-1')
            
            encryption_status = []
            
            if resource_type in ['S3', 'ALL']:
                s3_encryption = self._check_s3_encryption(request_id)
                encryption_status.extend(s3_encryption)
            
            if resource_type in ['EBS', 'ALL']:
                ebs_encryption = self._check_ebs_encryption(region, request_id)
                encryption_status.extend(ebs_encryption)
            
            if resource_type in ['RDS', 'ALL']:
                rds_encryption = self._check_rds_encryption(region, request_id)
                encryption_status.extend(rds_encryption)
            
            # Calculate encryption compliance
            total_resources = len(encryption_status)
            encrypted_resources = len([r for r in encryption_status if r.get('encrypted', False)])
            compliance_percentage = (encrypted_resources / total_resources * 100) if total_resources > 0 else 100
            
            result = {
                'resource_type': resource_type,
                'region': region,
                'encryption_status': encryption_status,
                'total_resources': total_resources,
                'encrypted_resources': encrypted_resources,
                'compliance_percentage': round(compliance_percentage, 2),
                'check_date': datetime.utcnow().isoformat()
            }
            
            logger.info(f"[{request_id}] Encryption check completed: {compliance_percentage:.1f}% compliance")
            return result
            
        except ClientError as e:
            logger.error(f"[{request_id}] AWS error in encryption check: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"[{request_id}] Error in encryption check: {str(e)}")
            raise
    
    def _check_security_groups(self, region: str, request_id: str) -> List[Dict[str, Any]]:
        """Check security groups for overly permissive rules."""
        try:
            ec2_client = self.aws_clients.get_ec2_client(region)
            response = ec2_client.describe_security_groups()
            
            findings = []
            
            for sg in response['SecurityGroups']:
                sg_id = sg['GroupId']
                sg_name = sg['GroupName']
                
                # Check inbound rules
                for rule in sg.get('IpPermissions', []):
                    # Check for 0.0.0.0/0 access
                    for ip_range in rule.get('IpRanges', []):
                        if ip_range.get('CidrIp') == '0.0.0.0/0':
                            severity = 'HIGH' if rule.get('FromPort') in [22, 3389, 80, 443] else 'MEDIUM'
                            
                            finding = {
                                'finding_id': f"sg-{sg_id}-open-{rule.get('FromPort', 'all')}",
                                'severity': severity,
                                'title': f"Security Group allows public access on port {rule.get('FromPort', 'all')}",
                                'description': f"Security Group {sg_name} ({sg_id}) allows inbound traffic from 0.0.0.0/0",
                                'resource_id': sg_id,
                                'resource_type': 'SecurityGroup',
                                'region': region,
                                'remediation_steps': [
                                    f"Review security group {sg_name} ({sg_id})",
                                    "Restrict source IP ranges to specific networks",
                                    "Consider using AWS Systems Manager Session Manager for SSH access"
                                ]
                            }
                            findings.append(finding)
            
            return findings
            
        except Exception as e:
            logger.warning(f"[{request_id}] Could not check security groups in {region}: {str(e)}")
            return []
    
    def _check_s3_public_access(self, request_id: str) -> List[Dict[str, Any]]:
        """Check S3 buckets for public access."""
        try:
            s3_client = self.aws_clients.get_s3_client()
            response = s3_client.list_buckets()
            
            findings = []
            
            for bucket in response.get('Buckets', []):
                bucket_name = bucket['Name']
                
                try:
                    # Check public access block
                    public_access_response = s3_client.get_public_access_block(Bucket=bucket_name)
                    public_access_config = public_access_response.get('PublicAccessBlockConfiguration', {})
                    
                    if not all([
                        public_access_config.get('BlockPublicAcls', False),
                        public_access_config.get('IgnorePublicAcls', False),
                        public_access_config.get('BlockPublicPolicy', False),
                        public_access_config.get('RestrictPublicBuckets', False)
                    ]):
                        finding = {
                            'finding_id': f"s3-{bucket_name}-public-access",
                            'severity': 'HIGH',
                            'title': f"S3 bucket may allow public access",
                            'description': f"S3 bucket {bucket_name} does not have all public access blocks enabled",
                            'resource_id': bucket_name,
                            'resource_type': 'S3Bucket',
                            'remediation_steps': [
                                f"Enable all public access blocks for bucket {bucket_name}",
                                "Review bucket policy and ACLs",
                                "Ensure only necessary access is granted"
                            ]
                        }
                        findings.append(finding)
                
                except ClientError as e:
                    if e.response['Error']['Code'] != 'NoSuchPublicAccessBlockConfiguration':
                        # If no public access block is configured, it's a finding
                        finding = {
                            'finding_id': f"s3-{bucket_name}-no-public-access-block",
                            'severity': 'MEDIUM',
                            'title': f"S3 bucket has no public access block configuration",
                            'description': f"S3 bucket {bucket_name} does not have public access block configured",
                            'resource_id': bucket_name,
                            'resource_type': 'S3Bucket',
                            'remediation_steps': [
                                f"Configure public access block for bucket {bucket_name}",
                                "Enable all four public access block settings"
                            ]
                        }
                        findings.append(finding)
            
            return findings
            
        except Exception as e:
            logger.warning(f"[{request_id}] Could not check S3 public access: {str(e)}")
            return []
    
    def _check_iam_policies(self, request_id: str) -> List[Dict[str, Any]]:
        """Check IAM policies for overly permissive access."""
        try:
            iam_client = self.aws_clients.get_iam_client()
            findings = []
            
            # Check for users with admin access
            response = iam_client.list_users()
            
            for user in response.get('Users', []):
                user_name = user['UserName']
                
                # Get attached policies
                policies_response = iam_client.list_attached_user_policies(UserName=user_name)
                
                for policy in policies_response.get('AttachedPolicies', []):
                    if 'Admin' in policy['PolicyName'] or policy['PolicyArn'].endswith('AdministratorAccess'):
                        finding = {
                            'finding_id': f"iam-user-{user_name}-admin-access",
                            'severity': 'HIGH',
                            'title': f"IAM user has administrative access",
                            'description': f"IAM user {user_name} has administrative policy {policy['PolicyName']} attached",
                            'resource_id': user_name,
                            'resource_type': 'IAMUser',
                            'remediation_steps': [
                                f"Review if user {user_name} requires administrative access",
                                "Consider using IAM roles instead of direct user permissions",
                                "Implement principle of least privilege"
                            ]
                        }
                        findings.append(finding)
            
            return findings
            
        except Exception as e:
            logger.warning(f"[{request_id}] Could not check IAM policies: {str(e)}")
            return []
    
    def _check_s3_encryption(self, request_id: str) -> List[Dict[str, Any]]:
        """Check S3 bucket encryption status."""
        try:
            s3_client = self.aws_clients.get_s3_client()
            response = s3_client.list_buckets()
            
            encryption_status = []
            
            for bucket in response.get('Buckets', []):
                bucket_name = bucket['Name']
                
                try:
                    encryption_response = s3_client.get_bucket_encryption(Bucket=bucket_name)
                    encryption_config = encryption_response.get('ServerSideEncryptionConfiguration', {})
                    
                    status = {
                        'resource_id': bucket_name,
                        'resource_type': 'S3Bucket',
                        'encrypted': True,
                        'encryption_type': 'server-side',
                        'encryption_details': encryption_config
                    }
                    
                except ClientError as e:
                    if e.response['Error']['Code'] == 'ServerSideEncryptionConfigurationNotFoundError':
                        status = {
                            'resource_id': bucket_name,
                            'resource_type': 'S3Bucket',
                            'encrypted': False,
                            'encryption_type': 'none',
                            'encryption_details': {}
                        }
                    else:
                        continue
                
                encryption_status.append(status)
            
            return encryption_status
            
        except Exception as e:
            logger.warning(f"[{request_id}] Could not check S3 encryption: {str(e)}")
            return []
    
    def _check_ebs_encryption(self, region: str, request_id: str) -> List[Dict[str, Any]]:
        """Check EBS volume encryption status."""
        try:
            ec2_client = self.aws_clients.get_ec2_client(region)
            response = ec2_client.describe_volumes()
            
            encryption_status = []
            
            for volume in response.get('Volumes', []):
                status = {
                    'resource_id': volume['VolumeId'],
                    'resource_type': 'EBSVolume',
                    'encrypted': volume.get('Encrypted', False),
                    'encryption_type': 'ebs' if volume.get('Encrypted') else 'none',
                    'encryption_details': {
                        'kms_key_id': volume.get('KmsKeyId') if volume.get('Encrypted') else None
                    }
                }
                encryption_status.append(status)
            
            return encryption_status
            
        except Exception as e:
            logger.warning(f"[{request_id}] Could not check EBS encryption in {region}: {str(e)}")
            return []
    
    def _check_rds_encryption(self, region: str, request_id: str) -> List[Dict[str, Any]]:
        """Check RDS instance encryption status."""
        try:
            rds_client = self.aws_clients.get_rds_client(region)
            response = rds_client.describe_db_instances()
            
            encryption_status = []
            
            for db_instance in response.get('DBInstances', []):
                status = {
                    'resource_id': db_instance['DBInstanceIdentifier'],
                    'resource_type': 'RDSInstance',
                    'encrypted': db_instance.get('StorageEncrypted', False),
                    'encryption_type': 'rds' if db_instance.get('StorageEncrypted') else 'none',
                    'encryption_details': {
                        'kms_key_id': db_instance.get('KmsKeyId') if db_instance.get('StorageEncrypted') else None
                    }
                }
                encryption_status.append(status)
            
            return encryption_status
            
        except Exception as e:
            logger.warning(f"[{request_id}] Could not check RDS encryption in {region}: {str(e)}")
            return []
    
    def _calculate_risk_score(self, findings: List[Dict[str, Any]]) -> int:
        """Calculate overall risk score based on findings."""
        if not findings:
            return 0
        
        score = 0
        for finding in findings:
            severity = finding.get('severity', 'LOW')
            if severity == 'HIGH':
                score += 30
            elif severity == 'MEDIUM':
                score += 15
            elif severity == 'LOW':
                score += 5
        
        # Cap at 100
        return min(score, 100)
    
    def _generate_security_recommendations(self, findings: List[Dict[str, Any]]) -> List[str]:
        """Generate security recommendations based on findings."""
        recommendations = []
        
        high_findings = [f for f in findings if f.get('severity') == 'HIGH']
        medium_findings = [f for f in findings if f.get('severity') == 'MEDIUM']
        
        if high_findings:
            recommendations.append(f"Address {len(high_findings)} high-severity security issues immediately")
        
        if medium_findings:
            recommendations.append(f"Review and remediate {len(medium_findings)} medium-severity security issues")
        
        # Specific recommendations based on finding types
        sg_findings = [f for f in findings if f.get('resource_type') == 'SecurityGroup']
        if sg_findings:
            recommendations.append("Review security group rules and restrict public access where possible")
        
        s3_findings = [f for f in findings if f.get('resource_type') == 'S3Bucket']
        if s3_findings:
            recommendations.append("Enable S3 public access blocks and review bucket policies")
        
        iam_findings = [f for f in findings if f.get('resource_type') == 'IAMUser']
        if iam_findings:
            recommendations.append("Review IAM user permissions and implement principle of least privilege")
        
        if not findings:
            recommendations.append("No security issues found in this assessment")
        
        return recommendations