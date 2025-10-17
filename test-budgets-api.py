#!/usr/bin/env python3
"""
Test AWS Budgets API directly
"""

import boto3
import json

def test_budgets_api():
    """Test AWS Budgets API to see current spend"""
    
    print("💳 Testing AWS Budgets API directly...")
    
    try:
        # Create clients
        budgets_client = boto3.client('budgets', region_name='us-east-1')
        sts_client = boto3.client('sts')
        
        # Get account ID
        account_id = sts_client.get_caller_identity()['Account']
        print(f"Account ID: {account_id}")
        
        # List budgets
        budgets_response = budgets_client.describe_budgets(AccountId=account_id)
        budgets = budgets_response.get('Budgets', [])
        
        print(f"Found {len(budgets)} budgets:")
        
        for budget in budgets:
            budget_name = budget.get('BudgetName')
            calculated_spend = budget.get('CalculatedSpend', {})
            actual_spend = calculated_spend.get('ActualSpend', {})
            forecasted_spend = calculated_spend.get('ForecastedSpend', {})
            
            print(f"\n📊 Budget: {budget_name}")
            
            if actual_spend:
                amount = actual_spend.get('Amount', '0')
                unit = actual_spend.get('Unit', 'USD')
                print(f"   Actual Spend: ${amount} {unit}")
                
                # Test if this would work in our Lambda
                cost_amount = float(amount)
                if cost_amount > 0:
                    print(f"   ✅ This budget has spend data: ${cost_amount:.2f}")
                    print(f"   🔄 This should be used as fallback data")
                else:
                    print(f"   ⚠️ This budget shows $0 spend")
            else:
                print(f"   ❌ No actual spend data")
            
            if forecasted_spend:
                amount = forecasted_spend.get('Amount', '0')
                unit = forecasted_spend.get('Unit', 'USD')
                print(f"   Forecasted: ${amount} {unit}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Budgets API: {e}")
        return False

def test_lambda_with_debug():
    """Test Lambda with debug to see why fallback isn't working"""
    
    print("\n🔍 Testing Lambda with debug info...")
    
    try:
        lambda_client = boto3.client('lambda', region_name='us-east-1')
        
        # Test payload
        test_payload = {
            "function": "getCostAnalysis",
            "parameters": {
                "time_period": "monthly"
            }
        }
        
        # Invoke Lambda
        response = lambda_client.invoke(
            FunctionName='aws-ai-concierge-tools-dev',
            InvocationType='RequestResponse',
            Payload=json.dumps(test_payload)
        )
        
        # Parse response
        response_payload = json.loads(response['Payload'].read())
        
        if 'response' in response_payload:
            # This is a Bedrock Agent response format
            function_response = response_payload['response']['functionResponse']['responseBody']['TEXT']['body']
            data = json.loads(function_response)
            
            if data.get('success'):
                result_data = data.get('data', {})
                total_cost = result_data.get('total_cost', 0)
                data_source = result_data.get('data_source', 'Cost Explorer')
                message = result_data.get('message', '')
                
                print(f"Total Cost: ${total_cost:.2f}")
                print(f"Data Source: {data_source}")
                print(f"Message: {message}")
                
                if total_cost == 0:
                    print(f"\n🔍 ANALYSIS:")
                    print(f"- Cost Explorer returned $0.00")
                    print(f"- Fallback should have triggered")
                    print(f"- Check Lambda logs for Budgets API call")
                
                return total_cost
        
        return None
        
    except Exception as e:
        print(f"❌ Error testing Lambda: {e}")
        return None

if __name__ == "__main__":
    print("🔧 AWS Budgets API Test")
    print("=" * 50)
    
    # Test Budgets API directly
    budgets_success = test_budgets_api()
    
    if budgets_success:
        # Test Lambda
        cost = test_lambda_with_debug()
        
        if cost is not None:
            if cost > 0:
                print(f"\n✅ SUCCESS: Lambda now returns ${cost:.2f}")
            else:
                print(f"\n⚠️ ISSUE: Lambda still returns $0.00")
                print(f"The Budgets API fallback may not be working correctly")
                print(f"Check CloudWatch logs for the Lambda function")
        else:
            print(f"\n❌ Could not get cost data from Lambda")
    else:
        print(f"\n❌ Budgets API test failed")
    
    print(f"\n💡 NEXT STEPS:")
    print(f"1. Check CloudWatch logs: /aws/lambda/aws-ai-concierge-tools-dev")
    print(f"2. Verify Budgets API permissions in Lambda role")
    print(f"3. The fallback logic should trigger when Cost Explorer returns $0")