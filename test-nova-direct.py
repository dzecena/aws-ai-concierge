#!/usr/bin/env python3
"""
Direct Nova model testing script to understand format and capabilities
"""
import boto3
import json
import time
from datetime import datetime

def test_nova_model(model_id, test_message):
    """Test a Nova model directly via bedrock-runtime"""
    print(f"\n🧪 Testing {model_id}")
    print("=" * 50)
    
    try:
        bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
        
        # Nova models use a different message format than Claude
        # Nova uses the "messages" format similar to OpenAI
        request_body = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "text": test_message
                        }
                    ]
                }
            ],
            "inferenceConfig": {
                "maxTokens": 500,
                "temperature": 0.7
            }
        }
        
        print(f"📤 Request body: {json.dumps(request_body, indent=2)}")
        
        start_time = time.time()
        
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body),
            contentType='application/json',
            accept='application/json'
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Parse response
        response_body = json.loads(response['body'].read())
        print(f"📥 Response body: {json.dumps(response_body, indent=2)}")
        
        # Extract the actual response text
        if 'output' in response_body and 'message' in response_body['output']:
            response_text = response_body['output']['message']['content'][0]['text']
            print(f"✅ SUCCESS: {model_id}")
            print(f"⏱️ Response time: {response_time:.2f} seconds")
            print(f"📝 Response: {response_text}")
            return True, response_text, response_time
        else:
            print(f"❌ FAILED: Unexpected response format")
            return False, None, response_time
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        print(f"🔍 Error type: {type(e).__name__}")
        return False, str(e), 0

def test_claude_model(model_id, test_message):
    """Test Claude model for comparison"""
    print(f"\n🧪 Testing {model_id} (Claude)")
    print("=" * 50)
    
    try:
        bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
        
        # Claude uses a different format
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 500,
            "messages": [
                {
                    "role": "user",
                    "content": test_message
                }
            ]
        }
        
        print(f"📤 Request body: {json.dumps(request_body, indent=2)}")
        
        start_time = time.time()
        
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body),
            contentType='application/json',
            accept='application/json'
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Parse response
        response_body = json.loads(response['body'].read())
        print(f"📥 Response body: {json.dumps(response_body, indent=2)}")
        
        # Extract the actual response text
        if 'content' in response_body and len(response_body['content']) > 0:
            response_text = response_body['content'][0]['text']
            print(f"✅ SUCCESS: {model_id}")
            print(f"⏱️ Response time: {response_time:.2f} seconds")
            print(f"📝 Response: {response_text}")
            return True, response_text, response_time
        else:
            print(f"❌ FAILED: Unexpected response format")
            return False, None, response_time
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        print(f"🔍 Error type: {type(e).__name__}")
        return False, str(e), 0

def main():
    print("🚀 Direct Nova Model Testing")
    print("=" * 60)
    print(f"🕐 Started at: {datetime.now().isoformat()}")
    
    test_message = "Hello! Can you help me analyze AWS costs? What capabilities do you have?"
    
    # Test Nova models
    nova_models = [
        "amazon.nova-pro-v1:0",
        "amazon.nova-lite-v1:0", 
        "amazon.nova-micro-v1:0"
    ]
    
    # Test Claude for comparison
    claude_models = [
        "anthropic.claude-3-haiku-20240307-v1:0"
    ]
    
    results = {}
    
    # Test Nova models
    for model in nova_models:
        success, response, time_taken = test_nova_model(model, test_message)
        results[model] = {
            'success': success,
            'response': response,
            'time': time_taken,
            'type': 'nova'
        }
        time.sleep(2)  # Brief pause between tests
    
    # Test Claude for comparison
    for model in claude_models:
        success, response, time_taken = test_claude_model(model, test_message)
        results[model] = {
            'success': success,
            'response': response,
            'time': time_taken,
            'type': 'claude'
        }
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TESTING SUMMARY")
    print("=" * 60)
    
    for model, result in results.items():
        status = "✅ SUCCESS" if result['success'] else "❌ FAILED"
        time_str = f"{result['time']:.2f}s" if result['time'] > 0 else "N/A"
        print(f"{model}: {status} ({time_str})")
        
        if not result['success'] and result['response']:
            print(f"  Error: {result['response']}")
    
    # Check if Nova models work differently
    nova_working = any(results[model]['success'] for model in nova_models if model in results)
    claude_working = any(results[model]['success'] for model in claude_models if model in results)
    
    print(f"\n🎯 CONCLUSIONS:")
    print(f"Nova models working: {'✅ YES' if nova_working else '❌ NO'}")
    print(f"Claude models working: {'✅ YES' if claude_working else '❌ NO'}")
    
    if nova_working:
        print("💡 Nova models are accessible via direct API calls!")
        print("💡 The issue might be specific to Bedrock Agents integration")
    else:
        print("💡 Nova models may need different permissions or formats")

if __name__ == "__main__":
    main()