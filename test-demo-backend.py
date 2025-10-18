#!/usr/bin/env python3
"""
Test the demo backend chat endpoint with cost query
"""

import requests
import json

def test_demo_backend():
    """Test the demo backend chat endpoint"""
    
    print("🧪 Testing Demo Backend Chat Endpoint...")
    
    # Demo backend API URL from deployment output
    api_url = "https://8yuqsjat6b.execute-api.us-east-1.amazonaws.com/prod/chat"
    
    # Test payload
    test_payload = {
        "message": "What are my AWS costs this month?",
        "sessionId": "test-session-cost-fix"
    }
    
    print(f"📤 Sending request to: {api_url}")
    print(f"📤 Payload: {json.dumps(test_payload, indent=2)}")
    
    try:
        # Send POST request
        response = requests.post(
            api_url,
            json=test_payload,
            headers={
                'Content-Type': 'application/json'
            },
            timeout=30
        )
        
        print(f"📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"📥 Response Body:")
            print(json.dumps(response_data, indent=2))
            
            # Check if we got real cost data
            response_text = response_data.get('response', '')
            
            if '$1.15' in response_text or '$1.1' in response_text:
                print(f"\n✅ SUCCESS: Demo backend now returns real cost data!")
                print(f"🎯 Found $1.15 in response - Budgets API fallback is working!")
            elif '$0.00' in response_text or '$0' in response_text:
                print(f"\n⚠️ Still returning $0.00 - fallback may not be working")
            else:
                print(f"\n🔍 Response doesn't clearly show cost amount")
                
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing demo backend: {e}")

if __name__ == "__main__":
    test_demo_backend()