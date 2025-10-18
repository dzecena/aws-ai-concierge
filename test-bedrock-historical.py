#!/usr/bin/env python3
"""
Test Bedrock Agent with historical date queries
"""

import boto3
import json

def test_bedrock_agent_historical():
    """Test the Bedrock Agent with historical date queries"""
    
    print("🤖 Testing Bedrock Agent with historical dates...")
    
    try:
        # Create Bedrock Agent Runtime client
        bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
        
        # Test cases for historical dates
        test_queries = [
            "What were my AWS costs in September 2025?",
            "Show me costs for January 2024",
            "What did I spend in August 2025?"
        ]
        
        for query in test_queries:
            print(f"\n📤 Testing query: '{query}'")
            
            try:
                # Invoke the agent
                response = bedrock_runtime.invoke_agent(
                    agentId='WWYOPOAATI',
                    agentAliasId='TSTALIASID',
                    sessionId=f'test-historical-{hash(query)}',
                    inputText=query
                )
                
                # Process the response stream
                response_text = ""
                for event in response['completion']:
                    if 'chunk' in event:
                        chunk = event['chunk']
                        if 'bytes' in chunk:
                            response_text += chunk['bytes'].decode('utf-8')
                
                print(f"📥 Bedrock Agent Response:")
                print(response_text[:500] + "..." if len(response_text) > 500 else response_text)
                
                # Check if the response contains cost information
                if '$' in response_text and ('0.' in response_text or '1.' in response_text):
                    print(f"✅ SUCCESS: Found cost information in response")
                elif 'invalid' in response_text.lower() or 'error' in response_text.lower():
                    print(f"❌ ERROR: Response indicates an error")
                else:
                    print(f"🔍 UNCLEAR: Response doesn't clearly show cost amount")
                
            except Exception as e:
                print(f"❌ Error testing query '{query}': {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Bedrock Agent: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Bedrock Agent Historical Date Test")
    print("=" * 50)
    
    success = test_bedrock_agent_historical()
    
    if success:
        print(f"\n🎉 Bedrock Agent historical date test completed!")
    else:
        print(f"\n❌ Bedrock Agent historical date test failed")