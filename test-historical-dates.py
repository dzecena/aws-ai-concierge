#!/usr/bin/env python3
"""
Test historical date parsing in the Lambda function
"""

import boto3
import json

def test_lambda_historical():
    """Test the Lambda function with historical date queries"""
    
    print("🧪 Testing Lambda function with historical dates...")
    
    try:
        lambda_client = boto3.client('lambda', region_name='us-east-1')
        
        # Test cases for historical dates
        test_cases = [
            {
                "name": "December 2024",
                "payload": {
                    "function": "getCostAnalysis",
                    "parameters": {
                        "time_period": "december_2024"
                    }
                }
            },
            {
                "name": "October 2025 (current month)",
                "payload": {
                    "function": "getCostAnalysis",
                    "parameters": {
                        "time_period": "october_2025"
                    }
                }
            },
            {
                "name": "January 2024",
                "payload": {
                    "function": "getCostAnalysis",
                    "parameters": {
                        "time_period": "january_2024"
                    }
                }
            }
        ]
        
        for test_case in test_cases:
            print(f"\n📤 Testing: {test_case['name']}")
            print(f"📤 Payload: {json.dumps(test_case['payload'], indent=2)}")
            
            try:
                # Invoke Lambda
                response = lambda_client.invoke(
                    FunctionName='aws-ai-concierge-tools-dev',
                    InvocationType='RequestResponse',
                    Payload=json.dumps(test_case['payload'])
                )
                
                # Parse response
                response_payload = json.loads(response['Payload'].read())
                
                print(f"📥 Response Status: {response['StatusCode']}")
                
                if 'response' in response_payload:
                    # This is a Bedrock Agent response format
                    function_response = response_payload['response']['functionResponse']['responseBody']['TEXT']['body']
                    data = json.loads(function_response)
                    
                    if data.get('success'):
                        result_data = data.get('data', {})
                        total_cost = result_data.get('total_cost', 0)
                        period = result_data.get('period', 'Unknown')
                        start_date = result_data.get('start_date', 'Unknown')
                        end_date = result_data.get('end_date', 'Unknown')
                        
                        print(f"✅ SUCCESS: {test_case['name']}")
                        print(f"   Total Cost: ${total_cost:.2f}")
                        print(f"   Period: {period}")
                        print(f"   Date Range: {start_date} to {end_date}")
                    else:
                        print(f"❌ FAILED: {data.get('error', 'Unknown error')}")
                else:
                    print(f"❌ Unexpected response format: {response_payload}")
                    
            except Exception as e:
                print(f"❌ Error testing {test_case['name']}: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Lambda: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Historical Date Parsing Test")
    print("=" * 50)
    
    success = test_lambda_historical()
    
    if success:
        print(f"\n🎉 Historical date parsing test completed!")
    else:
        print(f"\n❌ Historical date parsing test failed")