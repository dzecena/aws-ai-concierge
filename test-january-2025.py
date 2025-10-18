#!/usr/bin/env python3
"""
Test January 2025 to see if it's a data retention issue
"""

import boto3
import json

def test_january_2025():
    """Test January 2025 cost query"""
    
    print("🧪 Testing January 2025...")
    
    try:
        lambda_client = boto3.client('lambda', region_name='us-east-1')
        
        # Test payload for January 2025
        test_payload = {
            "function": "getCostAnalysis",
            "parameters": {
                "time_period": "january_2025"
            }
        }
        
        print(f"📤 Testing Lambda directly...")
        
        # Invoke Lambda
        response = lambda_client.invoke(
            FunctionName='aws-ai-concierge-tools-dev',
            InvocationType='RequestResponse',
            Payload=json.dumps(test_payload)
        )
        
        # Parse response
        response_payload = json.loads(response['Payload'].read())
        
        if 'response' in response_payload:
            function_response = response_payload['response']['functionResponse']['responseBody']['TEXT']['body']
            data = json.loads(function_response)
            
            if data.get('success'):
                result_data = data.get('data', {})
                total_cost = result_data.get('total_cost', 0)
                print(f"✅ Lambda SUCCESS: January 2025 = ${total_cost:.2f}")
            else:
                print(f"❌ Lambda FAILED: {data.get('error', 'Unknown error')}")
        
        # Test Bedrock Agent
        print(f"\n📤 Testing Bedrock Agent...")
        bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
        
        response = bedrock_runtime.invoke_agent(
            agentId='WWYOPOAATI',
            agentAliasId='TSTALIASID',
            sessionId='test-jan-2025',
            inputText='What were my AWS costs in January 2025?'
        )
        
        # Process the response stream
        response_text = ""
        for event in response['completion']:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    response_text += chunk['bytes'].decode('utf-8')
        
        print(f"📥 Bedrock Agent Response:")
        print(response_text[:300] + "..." if len(response_text) > 300 else response_text)
        
        if '$' in response_text and ('0.' in response_text or '1.' in response_text):
            print(f"✅ Bedrock Agent SUCCESS: Found cost information")
        else:
            print(f"❌ Bedrock Agent FAILED: No cost information found")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_january_2025()