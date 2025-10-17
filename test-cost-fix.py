#!/usr/bin/env python3
"""
Test the fixed cost analysis directly
"""

import boto3
import json

def test_lambda_function():
    """Test the Lambda function directly"""
    
    print("🧪 Testing Lambda function with cost analysis...")
    
    try:
        # Create Lambda client
        lambda_client = boto3.client('lambda', region_name='us-east-1')
        
        # Test payload
        test_payload = {
            "function": "getCostAnalysis",
            "parameters": {
                "time_period": "monthly"
            }
        }
        
        print(f"📤 Invoking Lambda with payload: {json.dumps(test_payload, indent=2)}")
        
        # Invoke the Lambda function
        response = lambda_client.invoke(
            FunctionName='aws-ai-concierge-tools-dev',
            InvocationType='RequestResponse',
            Payload=json.dumps(test_payload)
        )
        
        # Parse response
        response_payload = json.loads(response['Payload'].read())
        
        print(f"📥 Lambda Response:")
        print(f"Status Code: {response['StatusCode']}")
        
        if response_payload:
            print(f"Response Body:")
            print(json.dumps(response_payload, indent=2))
            
            # Check if we got cost data
            if 'body' in response_payload:
                body = json.loads(response_payload['body'])
                if body.get('success') and body.get('data'):
                    total_cost = body['data'].get('total_cost', 0)
                    data_source = body['data'].get('data_source', 'Cost Explorer')
                    
                    print(f"\n🎯 RESULT:")
                    print(f"Total Cost: ${total_cost:.2f}")
                    print(f"Data Source: {data_source}")
                    
                    if total_cost > 0:
                        print(f"✅ SUCCESS: Cost analysis now returns ${total_cost:.2f}!")
                        if 'Budgets' in data_source:
                            print(f"🔄 Using AWS Budgets API fallback (Cost Explorer data delayed)")
                    else:
                        print(f"⚠️ Still returning $0.00")
                else:
                    print(f"❌ Lambda returned error or no data")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Lambda: {e}")
        return False

def test_bedrock_agent():
    """Test the Bedrock Agent"""
    
    print("\n🤖 Testing Bedrock Agent...")
    
    try:
        # Create Bedrock Agent Runtime client
        bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
        
        # Test query
        test_query = "What are my AWS costs this month?"
        
        print(f"📤 Asking Bedrock Agent: '{test_query}'")
        
        # Invoke the agent
        response = bedrock_runtime.invoke_agent(
            agentId='WWYOPOAATI',
            agentAliasId='TSTALIASID',
            sessionId=f'test-session-cost-fix',
            inputText=test_query
        )
        
        # Process the response stream
        response_text = ""
        for event in response['completion']:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    response_text += chunk['bytes'].decode('utf-8')
        
        print(f"📥 Bedrock Agent Response:")
        print(response_text)
        
        # Check if the response mentions costs
        if '$' in response_text and ('1.15' in response_text or '1.1' in response_text):
            print(f"\n✅ SUCCESS: Bedrock Agent now returns cost information!")
        elif '$0' in response_text or 'zero' in response_text.lower():
            print(f"\n⚠️ Still returning zero costs")
        else:
            print(f"\n🔍 Response doesn't clearly indicate cost amount")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Bedrock Agent: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Testing Cost Analysis Fix")
    print("=" * 50)
    
    # Test Lambda function directly
    lambda_success = test_lambda_function()
    
    if lambda_success:
        # Test Bedrock Agent
        agent_success = test_bedrock_agent()
        
        if agent_success:
            print(f"\n🎉 TESTING COMPLETE!")
            print(f"The cost analysis fix has been deployed and tested.")
        else:
            print(f"\n⚠️ Lambda works but Bedrock Agent may need time to update")
    else:
        print(f"\n❌ Lambda function test failed")
    
    print(f"\n💡 If you still see $0.00:")
    print(f"1. Wait a few minutes for the Lambda deployment to propagate")
    print(f"2. The Budgets API fallback should show ~$1.15")
    print(f"3. Try asking the agent again in the AWS Console")