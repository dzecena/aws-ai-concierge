#!/usr/bin/env python3
"""
Test improved error handling for future dates and edge cases
"""

import boto3
import json

def test_improved_error_handling():
    """Test the improved error handling"""
    
    print("🧪 Testing improved error handling...")
    
    try:
        lambda_client = boto3.client('lambda', region_name='us-east-1')
        
        # Test cases for different scenarios
        test_cases = [
            {
                "name": "Future Date (December 2024)",
                "payload": {
                    "function": "getCostAnalysis",
                    "parameters": {
                        "time_period": "december_2024"
                    }
                }
            },
            {
                "name": "Valid Historical (August 2025)",
                "payload": {
                    "function": "getCostAnalysis",
                    "parameters": {
                        "time_period": "august_2025"
                    }
                }
            },
            {
                "name": "Current Month (October 2025)",
                "payload": {
                    "function": "getCostAnalysis",
                    "parameters": {
                        "time_period": "october_2025"
                    }
                }
            }
        ]
        
        for test_case in test_cases:
            print(f"\n📤 Testing: {test_case['name']}")
            
            try:
                # Invoke Lambda
                response = lambda_client.invoke(
                    FunctionName='aws-ai-concierge-tools-dev',
                    InvocationType='RequestResponse',
                    Payload=json.dumps(test_case['payload'])
                )
                
                # Parse response
                response_payload = json.loads(response['Payload'].read())
                
                if 'response' in response_payload:
                    function_response = response_payload['response']['functionResponse']['responseBody']['TEXT']['body']
                    data = json.loads(function_response)
                    
                    if data.get('success'):
                        result_data = data.get('data', {})
                        total_cost = result_data.get('total_cost', 0)
                        message = result_data.get('message', '')
                        error_type = result_data.get('error_type', '')
                        
                        print(f"✅ SUCCESS: {test_case['name']}")
                        print(f"   Total Cost: ${total_cost:.2f}")
                        if message:
                            print(f"   Message: {message}")
                        if error_type:
                            print(f"   Error Type: {error_type}")
                    else:
                        print(f"❌ FAILED: {data.get('error', 'Unknown error')}")
                else:
                    print(f"❌ Unexpected response format")
                    
            except Exception as e:
                print(f"❌ Error testing {test_case['name']}: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Improved Error Handling Test")
    print("=" * 50)
    
    success = test_improved_error_handling()
    
    if success:
        print(f"\n🎉 Error handling test completed!")
    else:
        print(f"\n❌ Error handling test failed")