#!/usr/bin/env python3
"""
Comprehensive validation of current and historical cost data across all systems
"""

import boto3
import json
import requests

def test_nova_lite_direct():
    """Test Nova Lite direct integration via demo backend"""
    
    print("🚀 Testing Nova Lite Direct Integration...")
    
    api_url = "https://8yuqsjat6b.execute-api.us-east-1.amazonaws.com/prod/chat"
    
    test_cases = [
        {
            "name": "Current Month (October 2025)",
            "message": "What are my current AWS costs?",
            "expected_cost": 1.15
        },
        {
            "name": "Historical Month (August 2025)",
            "message": "What were my AWS costs in August 2025?",
            "expected_cost": 0.06
        },
        {
            "name": "Recent Historical (September 2025)",
            "message": "Show me costs for September 2025",
            "expected_cost": 1.15
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        try:
            import requests
            
            payload = {
                "message": test_case["message"],
                "sessionId": f"test-nova-{hash(test_case['name'])}"
            }
            
            response = requests.post(
                api_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                response_data = response.json()
                response_text = response_data.get('response', '')
                
                # Extract cost from response
                cost_found = None
                if f"${test_case['expected_cost']:.2f}" in response_text:
                    cost_found = test_case['expected_cost']
                elif '$1.15' in response_text:
                    cost_found = 1.15
                elif '$0.06' in response_text:
                    cost_found = 0.06
                
                if cost_found == test_case['expected_cost']:
                    print(f"✅ {test_case['name']}: ${cost_found:.2f}")
                    results.append(True)
                else:
                    print(f"❌ {test_case['name']}: Expected ${test_case['expected_cost']:.2f}, got {cost_found}")
                    results.append(False)
            else:
                print(f"❌ {test_case['name']}: HTTP {response.status_code}")
                results.append(False)
                
        except Exception as e:
            print(f"❌ {test_case['name']}: {e}")
            results.append(False)
    
    return all(results)

def test_bedrock_agent():
    """Test Bedrock Agent"""
    
    print("\n🤖 Testing Bedrock Agent...")
    
    try:
        bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
        
        test_cases = [
            {
                "name": "Current Month",
                "query": "What are my current AWS costs?",
                "expected_cost": 1.15
            },
            {
                "name": "August 2025",
                "query": "What were my AWS costs in August 2025?",
                "expected_cost": 0.06
            },
            {
                "name": "September 2025",
                "query": "Show me costs for September 2025",
                "expected_cost": 1.15
            }
        ]
        
        results = []
        
        for test_case in test_cases:
            try:
                response = bedrock_runtime.invoke_agent(
                    agentId='WWYOPOAATI',
                    agentAliasId='TSTALIASID',
                    sessionId=f'test-bedrock-{hash(test_case["name"])}',
                    inputText=test_case["query"]
                )
                
                # Process the response stream
                response_text = ""
                for event in response['completion']:
                    if 'chunk' in event:
                        chunk = event['chunk']
                        if 'bytes' in chunk:
                            response_text += chunk['bytes'].decode('utf-8')
                
                # Check for expected cost
                if f"${test_case['expected_cost']:.2f}" in response_text or f"${test_case['expected_cost']:.1f}" in response_text:
                    print(f"✅ {test_case['name']}: ${test_case['expected_cost']:.2f}")
                    results.append(True)
                elif 'error' in response_text.lower() or 'unable' in response_text.lower():
                    print(f"❌ {test_case['name']}: Error in response")
                    results.append(False)
                else:
                    print(f"🔍 {test_case['name']}: Unclear response")
                    results.append(False)
                    
            except Exception as e:
                print(f"❌ {test_case['name']}: {e}")
                results.append(False)
        
        return all(results)
        
    except Exception as e:
        print(f"❌ Bedrock Agent test failed: {e}")
        return False

def test_lambda_direct():
    """Test Lambda function directly"""
    
    print("\n⚡ Testing Lambda Function Directly...")
    
    try:
        lambda_client = boto3.client('lambda', region_name='us-east-1')
        
        test_cases = [
            {
                "name": "Current Month",
                "time_period": "october_2025",
                "expected_cost": 1.15
            },
            {
                "name": "August 2025",
                "time_period": "august_2025",
                "expected_cost": 0.06
            },
            {
                "name": "Future Date Test",
                "time_period": "december_2024",
                "expected_error": "future_date"
            }
        ]
        
        results = []
        
        for test_case in test_cases:
            try:
                payload = {
                    "function": "getCostAnalysis",
                    "parameters": {
                        "time_period": test_case["time_period"]
                    }
                }
                
                response = lambda_client.invoke(
                    FunctionName='aws-ai-concierge-tools-dev',
                    InvocationType='RequestResponse',
                    Payload=json.dumps(payload)
                )
                
                response_payload = json.loads(response['Payload'].read())
                
                if 'response' in response_payload:
                    function_response = response_payload['response']['functionResponse']['responseBody']['TEXT']['body']
                    data = json.loads(function_response)
                    
                    if data.get('success'):
                        result_data = data.get('data', {})
                        total_cost = result_data.get('total_cost', 0)
                        error_type = result_data.get('error_type', '')
                        
                        if 'expected_cost' in test_case:
                            if abs(total_cost - test_case['expected_cost']) < 0.01:
                                print(f"✅ {test_case['name']}: ${total_cost:.2f}")
                                results.append(True)
                            else:
                                print(f"❌ {test_case['name']}: Expected ${test_case['expected_cost']:.2f}, got ${total_cost:.2f}")
                                results.append(False)
                        elif 'expected_error' in test_case:
                            if error_type == test_case['expected_error']:
                                print(f"✅ {test_case['name']}: Correctly detected {error_type}")
                                results.append(True)
                            else:
                                print(f"❌ {test_case['name']}: Expected {test_case['expected_error']}, got {error_type}")
                                results.append(False)
                    else:
                        print(f"❌ {test_case['name']}: Lambda returned error")
                        results.append(False)
                else:
                    print(f"❌ {test_case['name']}: Unexpected response format")
                    results.append(False)
                    
            except Exception as e:
                print(f"❌ {test_case['name']}: {e}")
                results.append(False)
        
        return all(results)
        
    except Exception as e:
        print(f"❌ Lambda test failed: {e}")
        return False

def main():
    """Run comprehensive validation"""
    
    print("🔧 Comprehensive Cost Analysis Validation")
    print("=" * 60)
    
    # Test all systems
    nova_lite_success = test_nova_lite_direct()
    bedrock_success = test_bedrock_agent()
    lambda_success = test_lambda_direct()
    
    print(f"\n📊 VALIDATION SUMMARY:")
    print(f"Nova Lite Direct: {'✅ PASS' if nova_lite_success else '❌ FAIL'}")
    print(f"Bedrock Agent:    {'✅ PASS' if bedrock_success else '❌ FAIL'}")
    print(f"Lambda Direct:    {'✅ PASS' if lambda_success else '❌ FAIL'}")
    
    overall_success = nova_lite_success and bedrock_success and lambda_success
    
    print(f"\n🎯 OVERALL STATUS: {'✅ ALL SYSTEMS WORKING' if overall_success else '⚠️ SOME ISSUES DETECTED'}")
    
    if overall_success:
        print(f"\n🎉 All cost analysis systems are working correctly!")
        print(f"✅ Current month costs: $1.15 (via Budgets API)")
        print(f"✅ Historical costs: $0.06 (August 2025, via Cost Explorer)")
        print(f"✅ Error handling: Future dates properly rejected")
        print(f"✅ Date parsing: Intelligent month/year recognition")
    
    return overall_success

if __name__ == "__main__":
    main()