#!/usr/bin/env python3
"""
Debug script to test cost analysis directly
"""

import boto3
import json
from datetime import datetime, timedelta

def test_cost_explorer_direct():
    """Test Cost Explorer API directly to see what data is available"""
    
    print("🔍 Testing Cost Explorer API directly...")
    
    try:
        # Create Cost Explorer client
        ce_client = boto3.client('ce', region_name='us-east-1')
        
        # Calculate current month dates
        end_date = datetime.now().date()
        start_date = end_date.replace(day=1)
        
        print(f"📅 Querying costs from {start_date} to {end_date}")
        
        # Test 1: Basic current month query
        print("\n🧪 Test 1: Basic current month query")
        response1 = ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': (end_date + timedelta(days=1)).strftime('%Y-%m-%d')  # End date is exclusive
            },
            Granularity='DAILY',
            Metrics=['BlendedCost']
        )
        
        print(f"Response: {len(response1.get('ResultsByTime', []))} time periods")
        total_cost = 0
        for result in response1.get('ResultsByTime', []):
            period_cost = float(result.get('Total', {}).get('BlendedCost', {}).get('Amount', 0))
            total_cost += period_cost
            print(f"  {result.get('TimePeriod', {}).get('Start')}: ${period_cost:.2f}")
        
        print(f"📊 Total cost (Test 1): ${total_cost:.2f}")
        
        # Test 2: With service breakdown
        print("\n🧪 Test 2: With service breakdown")
        response2 = ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': (end_date + timedelta(days=1)).strftime('%Y-%m-%d')
            },
            Granularity='MONTHLY',
            Metrics=['BlendedCost'],
            GroupBy=[
                {
                    'Type': 'DIMENSION',
                    'Key': 'SERVICE'
                }
            ]
        )
        
        print(f"Response: {len(response2.get('ResultsByTime', []))} time periods")
        total_cost2 = 0
        for result in response2.get('ResultsByTime', []):
            print(f"  Period: {result.get('TimePeriod', {}).get('Start')} to {result.get('TimePeriod', {}).get('End')}")
            for group in result.get('Groups', []):
                service = group.get('Keys', ['Unknown'])[0]
                cost = float(group.get('Metrics', {}).get('BlendedCost', {}).get('Amount', 0))
                if cost > 0:
                    print(f"    {service}: ${cost:.2f}")
                    total_cost2 += cost
        
        print(f"📊 Total cost (Test 2): ${total_cost2:.2f}")
        
        # Test 3: Last 7 days
        print("\n🧪 Test 3: Last 7 days")
        end_date_7d = datetime.now().date()
        start_date_7d = end_date_7d - timedelta(days=7)
        
        response3 = ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date_7d.strftime('%Y-%m-%d'),
                'End': end_date_7d.strftime('%Y-%m-%d')
            },
            Granularity='DAILY',
            Metrics=['BlendedCost'],
            GroupBy=[
                {
                    'Type': 'DIMENSION',
                    'Key': 'SERVICE'
                }
            ]
        )
        
        total_cost3 = 0
        service_totals = {}
        for result in response3.get('ResultsByTime', []):
            for group in result.get('Groups', []):
                service = group.get('Keys', ['Unknown'])[0]
                cost = float(group.get('Metrics', {}).get('BlendedCost', {}).get('Amount', 0))
                if cost > 0:
                    if service not in service_totals:
                        service_totals[service] = 0
                    service_totals[service] += cost
                    total_cost3 += cost
        
        print(f"📅 Last 7 days ({start_date_7d} to {end_date_7d}):")
        for service, cost in sorted(service_totals.items(), key=lambda x: x[1], reverse=True):
            print(f"  {service}: ${cost:.2f}")
        
        print(f"📊 Total cost (Test 3): ${total_cost3:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Cost Explorer: {e}")
        return False

def test_current_costs():
    """Test what the AWS Console shows vs our API"""
    
    print("\n🏥 AWS Console shows $1.15 for current month")
    print("Let's see what our API returns...")
    
    # Test the exact same query our Lambda would make
    try:
        ce_client = boto3.client('ce', region_name='us-east-1')
        
        # Current month calculation (same as our Lambda)
        end_date = datetime.now().date()
        start_date = end_date.replace(day=1)
        
        print(f"📅 Our Lambda queries: {start_date} to {end_date + timedelta(days=1)}")
        
        response = ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': (end_date + timedelta(days=1)).strftime('%Y-%m-%d')
            },
            Granularity='DAILY',
            Metrics=['BlendedCost', 'UsageQuantity'],
            GroupBy=[
                {
                    'Type': 'DIMENSION',
                    'Key': 'SERVICE'
                }
            ]
        )
        
        print(f"\n📊 Raw API Response:")
        print(f"Number of time periods: {len(response.get('ResultsByTime', []))}")
        
        total_cost = 0
        service_costs = {}
        
        for time_result in response.get('ResultsByTime', []):
            period_start = time_result.get('TimePeriod', {}).get('Start')
            period_end = time_result.get('TimePeriod', {}).get('End')
            
            period_total = 0
            for group in time_result.get('Groups', []):
                service = group.get('Keys', ['Unknown'])[0]
                cost = float(group.get('Metrics', {}).get('BlendedCost', {}).get('Amount', 0))
                
                if cost > 0:
                    if service not in service_costs:
                        service_costs[service] = 0
                    service_costs[service] += cost
                    total_cost += cost
                    period_total += cost
            
            if period_total > 0:
                print(f"  {period_start}: ${period_total:.2f}")
        
        print(f"\n💰 Service Breakdown:")
        for service, cost in sorted(service_costs.items(), key=lambda x: x[1], reverse=True):
            print(f"  {service}: ${cost:.2f}")
        
        print(f"\n🎯 TOTAL COST: ${total_cost:.2f}")
        
        if total_cost == 0:
            print("\n🚨 ISSUE IDENTIFIED: API returns $0.00 but Console shows $1.15")
            print("Possible causes:")
            print("1. Cost data delay (can take 8-24 hours)")
            print("2. Different time zone calculations")
            print("3. Different cost metrics (BlendedCost vs UnblendedCost)")
            print("4. Billing period vs calendar period differences")
        
        return total_cost
        
    except Exception as e:
        print(f"❌ Error in cost test: {e}")
        return None

if __name__ == "__main__":
    print("🧪 AWS Cost Analysis Debug Tool")
    print("=" * 50)
    
    # Test 1: Direct Cost Explorer API
    if test_cost_explorer_direct():
        print("\n✅ Cost Explorer API is accessible")
    else:
        print("\n❌ Cost Explorer API failed")
        exit(1)
    
    # Test 2: Current costs comparison
    cost = test_current_costs()
    
    if cost is not None:
        if cost > 0:
            print(f"\n✅ SUCCESS: Found ${cost:.2f} in costs")
        else:
            print(f"\n⚠️ ZERO COST ISSUE: API returns $0.00")
            print("\n🔧 RECOMMENDED FIXES:")
            print("1. Try querying last month's data instead")
            print("2. Use UnblendedCost instead of BlendedCost")
            print("3. Check if costs are in a different region")
            print("4. Wait 24 hours for cost data to populate")
    
    print("\n🏁 Debug complete!")