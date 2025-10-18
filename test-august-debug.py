#!/usr/bin/env python3
"""
Debug August 2025 cost query
"""

import boto3
import json

def test_august_debug():
    """Test August 2025 cost query directly"""
    
    print("🔍 Testing August 2025 cost query...")
    
    try:
        lambda_client = boto3.client('lambda', region_name='us-east-1')
        
        # Test payload for August 2025
        test_payload = {
            "function": "getCostAnalysis",
            "parameters": {
                "time_period": "august_2025"
            }
        }
        
        print(f"📤 Payload: {json.dumps(test_payload, indent=2)}")
        
        # Invoke Lambda
        response = lambda_client.invoke(
            FunctionName='aws-ai-concierge-tools-dev',
            InvocationType='RequestResponse',
            Payload=json.dumps(test_payload)
        )
        
        # Parse response
        response_payload = json.loads(response['Payload'].read())
        
        print(f"📥 Response Status: {response['StatusCode']}")
        print(f"📥 Full Response: {json.dumps(response_payload, indent=2)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_august_debug()