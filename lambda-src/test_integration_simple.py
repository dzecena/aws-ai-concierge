"""
Simple integration test for enhanced error handling and audit logging
"""

import json
from unittest.mock import Mock, patch
import sys
import os

# Add the lambda-src directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from index import handler


def test_successful_request():
    """Test successful request with audit logging."""
    print("🔍 Testing successful request...")
    
    # Mock context
    context = Mock()
    context.aws_request_id = 'test-request-123'
    context.function_version = '$LATEST'
    
    # Mock successful cost analysis
    with patch('index.cost_handler') as mock_cost_handler:
        mock_result = {
            'total_cost': 150.75,
            'cost_breakdown': [{'service': 'EC2', 'cost': 100.50}],
            'optimization_recommendations': ['Stop idle instances']
        }
        mock_cost_handler.get_cost_analysis.return_value = mock_result
        
        # API Gateway event
        event = {
            'httpMethod': 'POST',
            'path': '/cost-analysis',
            'body': json.dumps({
                'time_period': 'MONTHLY',
                'granularity': 'DAILY'
            })
        }
        
        result = handler(event, context)
        
        # Verify response
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['success'] == True
        assert body['operation'] == 'getCostAnalysis'
        assert body['data'] == mock_result
        
        print("✅ Successful request test passed")
        return True


def test_error_handling():
    """Test error handling with audit logging."""
    print("🔍 Testing error handling...")
    
    # Mock context
    context = Mock()
    context.aws_request_id = 'test-request-456'
    context.function_version = '$LATEST'
    
    # Mock error from cost handler
    with patch('index.cost_handler') as mock_cost_handler:
        mock_cost_handler.get_cost_analysis.side_effect = ValueError("Invalid time_period 'INVALID'")
        
        # API Gateway event with invalid data
        event = {
            'httpMethod': 'POST',
            'path': '/cost-analysis',
            'body': json.dumps({'time_period': 'INVALID'})
        }
        
        result = handler(event, context)
        
        # Verify error response
        assert result['statusCode'] == 500
        body = json.loads(result['body'])
        assert body['success'] == False
        assert 'error' in body
        assert body['error']['error_type'] == 'ValueError'
        assert 'Invalid input' in body['error']['user_message']
        
        print("✅ Error handling test passed")
        return True


def test_unknown_operation():
    """Test unknown operation handling."""
    print("🔍 Testing unknown operation handling...")
    
    # Mock context
    context = Mock()
    context.aws_request_id = 'test-request-789'
    context.function_version = '$LATEST'
    
    # API Gateway event with unknown path
    event = {
        'httpMethod': 'POST',
        'path': '/unknown-operation',
        'body': json.dumps({})
    }
    
    result = handler(event, context)
    
    # Verify error response
    assert result['statusCode'] == 500
    body = json.loads(result['body'])
    assert body['success'] == False
    assert 'Unknown operation' in body['error']['user_message']
    
    print("✅ Unknown operation test passed")
    return True


def test_bedrock_agent_request():
    """Test Bedrock Agent request format."""
    print("🔍 Testing Bedrock Agent request...")
    
    # Mock context
    context = Mock()
    context.aws_request_id = 'test-request-bedrock'
    context.function_version = '$LATEST'
    
    # Mock successful cost analysis
    with patch('index.cost_handler') as mock_cost_handler:
        mock_result = {'total_cost': 200.0}
        mock_cost_handler.get_cost_analysis.return_value = mock_result
        
        # Bedrock Agent event
        event = {
            'actionGroup': 'cost-tools',
            'apiPath': '/cost-analysis',
            'httpMethod': 'POST',
            'parameters': [
                {'name': 'time_period', 'value': 'MONTHLY'}
            ]
        }
        
        result = handler(event, context)
        
        # Verify Bedrock Agent response format
        assert 'messageVersion' in result
        assert 'response' in result
        
        print("✅ Bedrock Agent request test passed")
        return True


def main():
    """Run all integration tests."""
    print("🚀 Starting Enhanced Error Handling Integration Tests\n")
    
    tests = [
        test_successful_request,
        test_error_handling,
        test_unknown_operation,
        test_bedrock_agent_request
    ]
    
    all_passed = True
    
    for test in tests:
        try:
            if not test():
                all_passed = False
        except Exception as e:
            print(f"❌ Test {test.__name__} failed: {e}")
            all_passed = False
    
    print(f"\n{'='*60}")
    if all_passed:
        print("🎉 All integration tests passed! Enhanced error handling is working correctly.")
        return 0
    else:
        print("❌ Some integration tests failed.")
        return 1


if __name__ == '__main__':
    exit(main())