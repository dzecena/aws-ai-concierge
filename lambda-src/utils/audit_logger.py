"""
Audit logging utilities for AWS AI Concierge
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of audit events."""
    REQUEST_RECEIVED = "REQUEST_RECEIVED"
    TOOL_INVOCATION = "TOOL_INVOCATION"
    AWS_API_CALL = "AWS_API_CALL"
    RESPONSE_SENT = "RESPONSE_SENT"
    ERROR_OCCURRED = "ERROR_OCCURRED"
    SECURITY_CHECK = "SECURITY_CHECK"
    COST_ANALYSIS = "COST_ANALYSIS"
    RESOURCE_ACCESS = "RESOURCE_ACCESS"


class AuditLogger:
    """Structured audit logging for compliance and debugging."""
    
    def __init__(self):
        self.logger = logging.getLogger('audit')
        self.logger.setLevel(logging.INFO)
    
    def log_request_received(self, request_id: str, event_source: str, operation: str, 
                           parameters: Dict[str, Any], user_context: Optional[Dict[str, Any]] = None):
        """Log incoming request for audit trail."""
        audit_event = {
            'event_type': AuditEventType.REQUEST_RECEIVED.value,
            'request_id': request_id,
            'timestamp': datetime.utcnow().isoformat(),
            'event_source': event_source,  # 'bedrock_agent', 'api_gateway', 'direct'
            'operation': operation,
            'parameters': self._sanitize_parameters(parameters),
            'user_context': user_context or {},
            'compliance': {
                'data_classification': 'internal',
                'retention_required': True
            }
        }
        
        self.logger.info(f"AUDIT_REQUEST: {json.dumps(audit_event)}")
    
    def log_tool_invocation(self, request_id: str, tool_name: str, parameters: Dict[str, Any], 
                          execution_time_ms: float, success: bool):
        """Log tool invocation for performance and audit tracking."""
        audit_event = {
            'event_type': AuditEventType.TOOL_INVOCATION.value,
            'request_id': request_id,
            'timestamp': datetime.utcnow().isoformat(),
            'tool_name': tool_name,
            'parameters': self._sanitize_parameters(parameters),
            'execution_time_ms': round(execution_time_ms, 2),
            'success': success,
            'performance': {
                'execution_time_category': self._categorize_execution_time(execution_time_ms),
                'meets_sla': execution_time_ms < 15000  # 15 second SLA
            }
        }
        
        self.logger.info(f"AUDIT_TOOL: {json.dumps(audit_event)}")
    
    def log_aws_api_call(self, request_id: str, service: str, operation: str, 
                        region: Optional[str], success: bool, error_code: Optional[str] = None,
                        response_size_bytes: Optional[int] = None):
        """Log AWS API calls for audit and compliance."""
        audit_event = {
            'event_type': AuditEventType.AWS_API_CALL.value,
            'request_id': request_id,
            'timestamp': datetime.utcnow().isoformat(),
            'aws_service': service,
            'aws_operation': operation,
            'aws_region': region,
            'success': success,
            'error_code': error_code,
            'response_size_bytes': response_size_bytes,
            'compliance': {
                'read_only_operation': True,  # All our operations are read-only
                'data_access_logged': True,
                'region_compliance': self._check_region_compliance(region)
            }
        }
        
        if success:
            self.logger.info(f"AUDIT_AWS_SUCCESS: {json.dumps(audit_event)}")
        else:
            self.logger.warning(f"AUDIT_AWS_ERROR: {json.dumps(audit_event)}")
    
    def log_response_sent(self, request_id: str, operation: str, response_size_bytes: int, 
                         processing_time_ms: float, success: bool):
        """Log response sent to user."""
        audit_event = {
            'event_type': AuditEventType.RESPONSE_SENT.value,
            'request_id': request_id,
            'timestamp': datetime.utcnow().isoformat(),
            'operation': operation,
            'response_size_bytes': response_size_bytes,
            'processing_time_ms': round(processing_time_ms, 2),
            'success': success,
            'performance': {
                'meets_response_time_sla': processing_time_ms < 5000,  # 5 second SLA for simple queries
                'response_size_category': self._categorize_response_size(response_size_bytes)
            }
        }
        
        self.logger.info(f"AUDIT_RESPONSE: {json.dumps(audit_event)}")
    
    def log_error_occurred(self, request_id: str, error_type: str, error_code: Optional[str], 
                          operation: str, severity: str, user_impact: str):
        """Log errors for debugging and monitoring."""
        audit_event = {
            'event_type': AuditEventType.ERROR_OCCURRED.value,
            'request_id': request_id,
            'timestamp': datetime.utcnow().isoformat(),
            'error_type': error_type,
            'error_code': error_code,
            'operation': operation,
            'severity': severity,
            'user_impact': user_impact,
            'monitoring': {
                'alert_required': severity in ['error', 'critical'],
                'escalation_required': severity == 'critical'
            }
        }
        
        if severity in ['error', 'critical']:
            self.logger.error(f"AUDIT_ERROR: {json.dumps(audit_event)}")
        else:
            self.logger.warning(f"AUDIT_WARNING: {json.dumps(audit_event)}")
    
    def log_security_check(self, request_id: str, check_type: str, resource_id: str, 
                          findings_count: int, risk_score: int):
        """Log security assessment activities."""
        audit_event = {
            'event_type': AuditEventType.SECURITY_CHECK.value,
            'request_id': request_id,
            'timestamp': datetime.utcnow().isoformat(),
            'check_type': check_type,
            'resource_id': resource_id,
            'findings_count': findings_count,
            'risk_score': risk_score,
            'security': {
                'high_risk_detected': risk_score > 70,
                'compliance_check': True,
                'audit_trail_complete': True
            }
        }
        
        self.logger.info(f"AUDIT_SECURITY: {json.dumps(audit_event)}")
    
    def log_cost_analysis(self, request_id: str, time_period: str, total_cost: float, 
                         currency: str, optimization_opportunities: int):
        """Log cost analysis activities."""
        audit_event = {
            'event_type': AuditEventType.COST_ANALYSIS.value,
            'request_id': request_id,
            'timestamp': datetime.utcnow().isoformat(),
            'time_period': time_period,
            'total_cost': total_cost,
            'currency': currency,
            'optimization_opportunities': optimization_opportunities,
            'cost_governance': {
                'cost_tracking_enabled': True,
                'optimization_recommendations_provided': optimization_opportunities > 0
            }
        }
        
        self.logger.info(f"AUDIT_COST: {json.dumps(audit_event)}")
    
    def log_resource_access(self, request_id: str, resource_type: str, resource_count: int, 
                           regions: List[str], sensitive_data_accessed: bool = False):
        """Log resource access for compliance."""
        audit_event = {
            'event_type': AuditEventType.RESOURCE_ACCESS.value,
            'request_id': request_id,
            'timestamp': datetime.utcnow().isoformat(),
            'resource_type': resource_type,
            'resource_count': resource_count,
            'regions_accessed': regions,
            'sensitive_data_accessed': sensitive_data_accessed,
            'compliance': {
                'read_only_access': True,
                'cross_region_access': len(regions) > 1,
                'data_residency_compliant': self._check_data_residency_compliance(regions)
            }
        }
        
        self.logger.info(f"AUDIT_RESOURCE: {json.dumps(audit_event)}")
    
    def _sanitize_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive information from parameters for logging."""
        sanitized = {}
        sensitive_keys = ['password', 'secret', 'key', 'token', 'credential']
        
        for key, value in parameters.items():
            if any(sensitive_key in key.lower() for sensitive_key in sensitive_keys):
                sanitized[key] = '[REDACTED]'
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _categorize_execution_time(self, execution_time_ms: float) -> str:
        """Categorize execution time for performance monitoring."""
        if execution_time_ms < 1000:
            return 'fast'
        elif execution_time_ms < 5000:
            return 'normal'
        elif execution_time_ms < 15000:
            return 'slow'
        else:
            return 'very_slow'
    
    def _categorize_response_size(self, size_bytes: int) -> str:
        """Categorize response size for monitoring."""
        if size_bytes < 1024:  # < 1KB
            return 'small'
        elif size_bytes < 10240:  # < 10KB
            return 'medium'
        elif size_bytes < 102400:  # < 100KB
            return 'large'
        else:
            return 'very_large'
    
    def _check_region_compliance(self, region: Optional[str]) -> bool:
        """Check if region meets compliance requirements."""
        if not region:
            return True
        
        # Define compliant regions (example - adjust based on your requirements)
        compliant_regions = [
            'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
            'eu-west-1', 'eu-west-2', 'eu-central-1'
        ]
        
        return region in compliant_regions
    
    def _check_data_residency_compliance(self, regions: List[str]) -> bool:
        """Check if data residency requirements are met."""
        # All regions should be compliant
        return all(self._check_region_compliance(region) for region in regions)