#!/usr/bin/env python3
"""
Simple Lambda test to check for syntax errors
"""

import boto3
import json

def test_lambda_simple():
    """Test Lambda with a simple payload"""
    
    print("🧪 Testing Lambda with simple payload...")
    
    try:
        lambda_client = boto3.client('lambda', region_name='us-east-1')
        
        # Simple test payload
        test_payload = {
            "function": "getCostAnalysis",
            "parameters": {
                "time_period": "MONTHLY"
            }
        }
        
        print(f"📤 Payload: {json.dumps(test_payload)}")
        
        # Invoke Lambda
        response = lambda_client.invoke(
            FunctionName='aws-ai-concierge-tools-dev',
            InvocationType='RequestResponse',
            Payload=json.dumps(test_payload)
        )
        
        # Parse response
        response_payload = json.loads(response['Payload'].read())
        
        print(f"📥 Status: {response['StatusCode']}")
        print(f"📥 Response: {json.dumps(response_payload, indent=2)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_lambda_simple()