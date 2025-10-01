"""
Validation script for enhanced error handling and audit logging
"""

import sys
import json
from datetime import datetime
from typing import Dict, Any

# Mock botocore for validation
class MockClientError(Exception):
    def __init__(self, error_response, operation_name):
        self.response = error_response
        self.operation_name = operation_name
        super().__init__(str(error_response))

# Import our modules
from utils.error_handler import ErrorHandler
from utils.audit_logger import AuditLogger, AuditEventType


def validate_error_handler():
    """Validate error handler functionality."""
    print("🔍 Validating Error Handler...")
    
    error_handler = ErrorHandler()
    request_id = 'validation-test-123'
    
    # Test 1: ValueError handling
    try:
        error = ValueError("Invalid time_period 'INVALID'. Must be one of: ['DAILY', 'MONTHLY', 'YEARLY']")
        result = error_handler.handle_error(error, request_id)
        
        assert result['request_id'] == request_id
        assert result['error_type'] == 'ValueError'
        assert 'Invalid input' in result['user_message']
        assert result['severity'] == 'error'
        assert not result['retry_suggested']
        print("✅ ValueError handling works correctly")
        
    except Exception as e:
        print(f"❌ ValueError handling failed: {e}")
        return False
    
    # Test 2: KeyError handling
    try:
        error = KeyError('required_parameter')
        result = error_handler.handle_error(error, request_id)
        
        assert result['error_type'] == 'KeyError'
        assert 'Missing required parameter' in result['user_message']
        assert 'required_parameter' in result['user_message']
        print("✅ KeyError handling works correctly")
        
    except Exception as e:
        print(f"❌ KeyError handling failed: {e}")
        return False
    
    # Test 3: Generic error handling
    try:
        error = RuntimeError("Something went wrong")
        result = error_handler.handle_error(error, request_id)
        
        assert result['error_type'] == 'RuntimeError'
        assert 'unexpected error' in result['user_message'].lower()
        assert result['retry_suggested']
        print("✅ Generic error handling works correctly")
        
    except Exception as e:
        print(f"❌ Generic error handling failed: {e}")
        return False
    
    return True


def validate_audit_logger():
    """Validate audit logger functionality."""
    print("\n🔍 Validating Audit Logger...")
    
    audit_logger = AuditLogger()
    request_id = 'validation-test-123'
    
    # Test 1: Parameter sanitization
    try:
        parameters = {
            'time_period': 'MONTHLY',
            'password': 'secret123',
            'api_key': 'key123',
            'normal_param': 'value'
        }
        
        sanitized = audit_logger._sanitize_parameters(parameters)
        
        assert sanitized['time_period'] == 'MONTHLY'
        assert sanitized['password'] == '[REDACTED]'
        assert sanitized['api_key'] == '[REDACTED]'
        assert sanitized['normal_param'] == 'value'
        print("✅ Parameter sanitization works correctly")
        
    except Exception as e:
        print(f"❌ Parameter sanitization failed: {e}")
        return False
    
    # Test 2: Execution time categorization
    try:
        assert audit_logger._categorize_execution_time(500) == 'fast'
        assert audit_logger._categorize_execution_time(2000) == 'normal'
        assert audit_logger._categorize_execution_time(8000) == 'slow'
        assert audit_logger._categorize_execution_time(20000) == 'very_slow'
        print("✅ Execution time categorization works correctly")
        
    except Exception as e:
        print(f"❌ Execution time categorization failed: {e}")
        return False
    
    # Test 3: Response size categorization
    try:
        assert audit_logger._categorize_response_size(500) == 'small'
        assert audit_logger._categorize_response_size(5000) == 'medium'
        assert audit_logger._categorize_response_size(50000) == 'large'
        assert audit_logger._categorize_response_size(200000) == 'very_large'
        print("✅ Response size categorization works correctly")
        
    except Exception as e:
        print(f"❌ Response size categorization failed: {e}")
        return False
    
    # Test 4: Region compliance checking
    try:
        assert audit_logger._check_region_compliance('us-east-1') == True
        assert audit_logger._check_region_compliance('eu-west-1') == True
        assert audit_logger._check_region_compliance('cn-north-1') == False  # Not in compliant list
        print("✅ Region compliance checking works correctly")
        
    except Exception as e:
        print(f"❌ Region compliance checking failed: {e}")
        return False
    
    return True


def validate_error_mappings():
    """Validate error mapping functionality."""
    print("\n🔍 Validating Error Mappings...")
    
    error_handler = ErrorHandler()
    
    # Test error mapping keys exist
    expected_mappings = [
        'AccessDenied', 'UnauthorizedOperation', 'Throttling', 
        'ThrottlingException', 'ServiceUnavailable', 'InternalError',
        'InvalidParameterValue', 'ValidationException'
    ]
    
    for error_code in expected_mappings:
        if error_code not in error_handler.error_mappings:
            print(f"❌ Missing error mapping for: {error_code}")
            return False
    
    print("✅ All expected error mappings are present")
    return True


def validate_audit_event_types():
    """Validate audit event types are properly defined."""
    print("\n🔍 Validating Audit Event Types...")
    
    expected_events = [
        'REQUEST_RECEIVED', 'TOOL_INVOCATION', 'AWS_API_CALL',
        'RESPONSE_SENT', 'ERROR_OCCURRED', 'SECURITY_CHECK',
        'COST_ANALYSIS', 'RESOURCE_ACCESS'
    ]
    
    for event_type in expected_events:
        if not hasattr(AuditEventType, event_type):
            print(f"❌ Missing audit event type: {event_type}")
            return False
    
    print("✅ All expected audit event types are defined")
    return True


def main():
    """Run all validation tests."""
    print("🚀 Starting Enhanced Error Handling and Audit Logging Validation\n")
    
    all_passed = True
    
    # Run validation tests
    tests = [
        validate_error_handler,
        validate_audit_logger,
        validate_error_mappings,
        validate_audit_event_types
    ]
    
    for test in tests:
        try:
            if not test():
                all_passed = False
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            all_passed = False
    
    print(f"\n{'='*60}")
    if all_passed:
        print("🎉 All validation tests passed! Enhanced error handling and audit logging is working correctly.")
        return 0
    else:
        print("❌ Some validation tests failed. Please check the implementation.")
        return 1


if __name__ == '__main__':
    sys.exit(main())